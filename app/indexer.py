"""
Load coding reference CSVs into Azure AI Search.
Run once (or re-run to refresh): python -m app.indexer
"""

import os
import json
import time
import pandas as pd
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SearchField as VectorField,
)
from azure.core.credentials import AzureKeyCredential

load_dotenv()

SEARCH_ENDPOINT = os.environ["AZURE_SEARCH_ENDPOINT"]
SEARCH_KEY = os.environ["AZURE_SEARCH_API_KEY"]
INDEX_NAME = os.environ["AZURE_SEARCH_INDEX_NAME"]

openai_client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version=os.environ["AZURE_OPENAI_API_VERSION"],
)
EMBEDDING_MODEL = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]

credential = AzureKeyCredential(SEARCH_KEY)


def create_index():
    index_client = SearchIndexClient(SEARCH_ENDPOINT, credential)
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SimpleField(name="code", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="system", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="description", type=SearchFieldDataType.String),
        SearchableField(name="notes", type=SearchFieldDataType.String),
        VectorField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=3072,
            vector_search_profile_name="hnsw-profile",
        ),
    ]
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
        profiles=[VectorSearchProfile(name="hnsw-profile", algorithm_configuration_name="hnsw")],
    )
    index = SearchIndex(name=INDEX_NAME, fields=fields, vector_search=vector_search)
    index_client.create_or_update_index(index)
    print(f"Index '{INDEX_NAME}' ready.")


def embed(texts: list[str]) -> list[list[float]]:
    response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [r.embedding for r in response.data]


def load_icd10(path: str):
    """
    Expects a CSV with at minimum columns: code, description
    ICD-10-CM order file from CMS works out of the box.
    """
    df = pd.read_csv(path, dtype=str).fillna("")
    # normalise common column name variants
    df.columns = [c.strip().lower() for c in df.columns]
    if "long description" in df.columns:
        df = df.rename(columns={"long description": "description", "short description": "notes"})
    return df[["code", "description"]].assign(system="ICD-10-CM", notes="")


def load_opcs4(path: str):
    df = pd.read_csv(path, dtype=str).fillna("")
    df.columns = [c.strip().lower() for c in df.columns]
    return df[["code", "description"]].assign(system="OPCS-4", notes="")


def load_hcc(path: str):
    """CMS HCC crosswalk CSV: ICD-10 code → HCC category"""
    df = pd.read_csv(path, dtype=str).fillna("")
    df.columns = [c.strip().lower() for c in df.columns]
    # typical CMS file has 'icd_10_cm_code' and 'icd_10_cm_code_description'
    df = df.rename(columns={
        "icd_10_cm_code": "code",
        "icd_10_cm_code_description": "description",
        "hcc_description": "notes",
    })
    return df[["code", "description", "notes"]].assign(system="HCC")


LOADERS = {
    "icd10": load_icd10,
    "opcs4": load_opcs4,
    "hcc": load_hcc,
}

BATCH = 100  # embeddings per API call


def index_dataframe(df: pd.DataFrame, search_client: SearchClient):
    docs = df.to_dict(orient="records")
    for i in range(0, len(docs), BATCH):
        batch = docs[i : i + BATCH]
        texts = [f"{d['code']} {d['description']} {d.get('notes', '')}" for d in batch]
        embeddings = embed(texts)
        upload = [
            {
                "id": f"{d['system'].replace('-','').lower()}_{d['code'].replace('.','_')}",
                "code": d["code"],
                "system": d["system"],
                "description": d["description"],
                "notes": d.get("notes", ""),
                "embedding": emb,
            }
            for d, emb in zip(batch, embeddings)
        ]
        search_client.upload_documents(upload)
        print(f"  Indexed {min(i + BATCH, len(docs))}/{len(docs)}", end="\r")
    print()


def run(data_dir: str = "data"):
    create_index()
    search_client = SearchClient(SEARCH_ENDPOINT, INDEX_NAME, credential)
    for name, loader in LOADERS.items():
        csv = os.path.join(data_dir, f"{name}.csv")
        if os.path.exists(csv):
            print(f"Loading {name} from {csv} ...")
            df = loader(csv)
            index_dataframe(df, search_client)
            print(f"  Done ({len(df)} records).")
        else:
            print(f"Skipping {name} — {csv} not found.")


if __name__ == "__main__":
    run()
