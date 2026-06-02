"""RAG pipeline: clinical note → candidate codes → GPT-4o ranked suggestions."""

import os
import json
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

load_dotenv()

openai_client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version=os.environ["AZURE_OPENAI_API_VERSION"],
)
CHAT_MODEL = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"]
EMBEDDING_MODEL = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]

search_client = SearchClient(
    endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
    index_name=os.environ["AZURE_SEARCH_INDEX_NAME"],
    credential=AzureKeyCredential(os.environ["AZURE_SEARCH_API_KEY"]),
)

SYSTEM_PROMPT = """You are a senior clinical coder with expertise in ICD-10-CM, OPCS-4, SNOMED CT, and HCC risk adjustment.

Given a clinical note and a list of candidate codes retrieved from a reference database, your task is to:
1. Select the most appropriate codes for the encounter.
2. Rank them by relevance (most specific first).
3. For each code provide a brief clinical justification.
4. Flag any codes that need human review with "REVIEW: <reason>".

Return ONLY valid JSON in this exact structure:
{
  "suggestions": [
    {
      "code": "string",
      "system": "string",
      "description": "string",
      "justification": "string",
      "confidence": "high|medium|low",
      "review_flag": "string or null"
    }
  ],
  "coding_notes": "string"
}"""


def embed(text: str) -> list[float]:
    response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=[text])
    return response.data[0].embedding


def retrieve_candidates(note: str, top_k: int = 20, systems: list[str] | None = None) -> list[dict]:
    vector = embed(note)
    vector_query = VectorizedQuery(vector=vector, k_nearest_neighbors=top_k, fields="embedding")

    filter_expr = None
    if systems:
        quoted = ", ".join(f"'{s}'" for s in systems)
        filter_expr = f"search.in(system, '{','.join(systems)}', ',')"

    results = search_client.search(
        search_text=note,
        vector_queries=[vector_query],
        filter=filter_expr,
        select=["code", "system", "description", "notes"],
        top=top_k,
    )
    return [dict(r) for r in results]


def suggest_codes(note: str, systems: list[str] | None = None) -> dict:
    candidates = retrieve_candidates(note, systems=systems)

    candidate_text = "\n".join(
        f"- [{r['system']}] {r['code']}: {r['description']}"
        + (f" ({r['notes']})" if r.get("notes") else "")
        for r in candidates
    )

    user_message = f"""CLINICAL NOTE:
{note}

CANDIDATE CODES FROM REFERENCE DATABASE:
{candidate_text}

Please select and rank the appropriate codes."""

    response = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    raw = response.choices[0].message.content
    return json.loads(raw)
