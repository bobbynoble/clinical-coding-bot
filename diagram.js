const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3" x 7.5"
pres.title = "Clinical Coding Bot - Architecture";

const slide = pres.addSlide();
slide.background = { color: "0F1C3F" };

// ── Palette ──────────────────────────────────────────────────────────────────
const NAV   = "1E2761";  // deep navy  (unused background tiles)
const TEAL  = "028090";  // teal       (Azure Search + arrows)
const BLUE  = "1565C0";  // mid blue   (middle steps)
const GREEN = "1B7F4A";  // green      (output)
const WHITE = "FFFFFF";
const LGREY = "A8B8D8";  // label grey
const ACCENT= "00C4CC";  // bright teal for arrows

// ── Title ────────────────────────────────────────────────────────────────────
slide.addText("Clinical Coding Bot — Architecture", {
  x: 0.4, y: 0.18, w: 12.5, h: 0.55,
  fontSize: 26, bold: true, color: WHITE, fontFace: "Calibri",
  align: "left", margin: 0
});
slide.addText("How a clinical note becomes suggested ICD-10 / OPCS-4 / HCC codes", {
  x: 0.4, y: 0.72, w: 12.5, h: 0.35,
  fontSize: 13, color: LGREY, fontFace: "Calibri",
  align: "left", margin: 0
});

// ── Divider line ─────────────────────────────────────────────────────────────
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.4, y: 1.1, w: 12.5, h: 0.025,
  fill: { color: ACCENT }, line: { color: ACCENT }
});

// ── Node definitions ─────────────────────────────────────────────────────────
// 6 nodes across the slide with arrows between them
const NODE_Y   = 1.6;
const NODE_W   = 1.75;
const NODE_H   = 2.0;
const GAP      = 0.38;
const START_X  = 0.38;

const nodes = [
  {
    label: "Clinical\nNote",
    sub:   "Discharge summary,\nclinic letter, etc.",
    color: "0B3D6E",
    tag:   "INPUT",
    tagColor: "00C4CC"
  },
  {
    label: "Web UI",
    sub:   "FastAPI + HTML\nlocalhost:8000",
    color: "0D5B9E",
    tag:   "FRONTEND",
    tagColor: "4A90D9"
  },
  {
    label: "Embeddings",
    sub:   "text-embedding-\n3-large (Azure)",
    color: TEAL,
    tag:   "AZURE OPENAI",
    tagColor: "00A4BD"
  },
  {
    label: "AI Search",
    sub:   "Vector search\nTop 20 candidates",
    color: "025F6D",
    tag:   "AZURE SEARCH",
    tagColor: "00A4BD"
  },
  {
    label: "GPT-4.1",
    sub:   "Ranks codes,\nadds justification",
    color: "1A237E",
    tag:   "AZURE OPENAI",
    tagColor: "4A90D9"
  },
  {
    label: "Suggested\nCodes",
    sub:   "ICD-10 · OPCS-4\nHCC · Confidence",
    color: GREEN,
    tag:   "OUTPUT",
    tagColor: "2ECC71"
  }
];

const makeShadow = () => ({
  type: "outer", color: "000000", blur: 8, offset: 3, angle: 135, opacity: 0.35
});

nodes.forEach((node, i) => {
  const x = START_X + i * (NODE_W + GAP);

  // Card background
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y: NODE_Y, w: NODE_W, h: NODE_H,
    fill: { color: node.color },
    line: { color: ACCENT, width: 0.75 },
    shadow: makeShadow()
  });

  // Top accent stripe
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y: NODE_Y, w: NODE_W, h: 0.08,
    fill: { color: node.tagColor },
    line: { color: node.tagColor }
  });

  // Tag label
  slide.addText(node.tag, {
    x: x + 0.05, y: NODE_Y + 0.1, w: NODE_W - 0.1, h: 0.28,
    fontSize: 7.5, bold: true, color: node.tagColor,
    fontFace: "Calibri", align: "center", margin: 0
  });

  // Step number circle (background oval)
  const circleSize = 0.38;
  const circleX = x + (NODE_W - circleSize) / 2;
  slide.addShape(pres.shapes.OVAL, {
    x: circleX, y: NODE_Y + 0.42, w: circleSize, h: circleSize,
    fill: { color: node.tagColor },
    line: { color: node.tagColor }
  });
  slide.addText(String(i + 1), {
    x: circleX, y: NODE_Y + 0.42, w: circleSize, h: circleSize,
    fontSize: 13, bold: true, color: WHITE,
    fontFace: "Calibri", align: "center", valign: "middle", margin: 0
  });

  // Main label
  slide.addText(node.label, {
    x: x + 0.05, y: NODE_Y + 0.88, w: NODE_W - 0.1, h: 0.65,
    fontSize: 14, bold: true, color: WHITE,
    fontFace: "Calibri", align: "center", valign: "middle", margin: 0
  });

  // Sub text
  slide.addText(node.sub, {
    x: x + 0.08, y: NODE_Y + 1.52, w: NODE_W - 0.16, h: 0.42,
    fontSize: 9, color: LGREY,
    fontFace: "Calibri", align: "center", valign: "top", margin: 0
  });

  // Arrow to next node
  if (i < nodes.length - 1) {
    const arrowX = x + NODE_W + 0.05;
    const arrowY = NODE_Y + NODE_H / 2 - 0.015;
    slide.addShape(pres.shapes.LINE, {
      x: arrowX, y: arrowY, w: GAP - 0.1, h: 0,
      line: { color: ACCENT, width: 2.5, endArrowType: "triangle" }
    });
  }
});

// ── Bottom info row ───────────────────────────────────────────────────────────
const infoY = NODE_Y + NODE_H + 0.28;
const infos = [
  { text: "Clinician pastes note into the web interface and selects code systems (ICD-10, OPCS-4, HCC)", x: 0.38 },
  { text: "FastAPI receives the note and orchestrates the RAG pipeline", x: 0.38 + (NODE_W + GAP) * 1 },
  { text: "Note is vectorised into a 3,072-dimension embedding using Azure OpenAI", x: 0.38 + (NODE_W + GAP) * 2 },
  { text: "Embedding is compared to 71,000 indexed codes — top 20 by cosine similarity returned", x: 0.38 + (NODE_W + GAP) * 3 },
  { text: "GPT-4.1 selects the best codes and writes a clinical justification for each", x: 0.38 + (NODE_W + GAP) * 4 },
  { text: "Codes displayed with High / Medium / Low confidence and any review flags", x: 0.38 + (NODE_W + GAP) * 5 }
];

infos.forEach((info, i) => {
  // Connector dot
  const dotSize = 0.1;
  const dotX = info.x + (NODE_W - dotSize) / 2;
  slide.addShape(pres.shapes.OVAL, {
    x: dotX, y: infoY - 0.08, w: dotSize, h: dotSize,
    fill: { color: ACCENT }, line: { color: ACCENT }
  });

  slide.addText(info.text, {
    x: info.x, y: infoY + 0.06, w: NODE_W, h: 0.85,
    fontSize: 8.5, color: LGREY,
    fontFace: "Calibri", align: "center", valign: "top", margin: 0
  });
});

// ── Footer ────────────────────────────────────────────────────────────────────
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 7.15, w: 13.3, h: 0.35,
  fill: { color: "0A1628" }, line: { color: "0A1628" }
});
slide.addText("Azure OpenAI (GPT-4.1 + text-embedding-3-large)  ·  Azure AI Search (HNSW vector index)  ·  FastAPI  ·  ngrok", {
  x: 0.4, y: 7.17, w: 12.5, h: 0.28,
  fontSize: 8, color: "6B7FA8", fontFace: "Calibri", align: "center", margin: 0
});

// ── Write file ────────────────────────────────────────────────────────────────
pres.writeFile({ fileName: "C:\\Users\\RobertNoble\\Clinical Coding\\Clinical_Coding_Bot_Diagram.pptx" })
  .then(() => console.log("✅  Saved: Clinical_Coding_Bot_Diagram.pptx"))
  .catch(e => console.error("❌", e));
