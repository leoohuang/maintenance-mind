"""Build FAISS vector indices for work orders and equipment manuals."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.retriever import VectorIndex

ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = ROOT / "data" / "indices"


def build_orders_index():
    orders_file = ROOT / "data" / "synthetic_orders.json"
    if not orders_file.exists():
        print("! Run scripts/generate_orders.py first")
        return

    orders = json.loads(orders_file.read_text())
    print(f"Loaded {len(orders)} orders")
    documents = []
    for order in orders:
        actions = " ".join(order.get("actions_taken", []))
        documents.append(
            {
                "text": (
                    f"Equipment: {order.get('equipment', '')} "
                    f"({order.get('equipment_id', '')}). "
                    f"Issue: {order.get('reported_issue', '')} "
                    f"Diagnosis: {order.get('diagnosis', '')} "
                    f"Actions: {actions} "
                    f"Root cause: {order.get('root_cause', '')}"
                ),
                "metadata": order,
            }
        )

    index = VectorIndex("work_orders")
    index.build(documents)
    index.save(INDEX_DIR)
    print(f"-> Saved work_orders index ({len(documents)} docs)")


def chunk_text(text: str, max_chars: int = 800, overlap: int = 100) -> list[str]:
    """Split text by paragraph while keeping oversized paragraphs bounded."""
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    chunks = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) <= max_chars:
            current += "\n\n" + paragraph if current else paragraph
        else:
            if current:
                chunks.append(current)
            if len(paragraph) <= max_chars:
                current = paragraph
            else:
                for start in range(0, len(paragraph), max_chars - overlap):
                    chunks.append(paragraph[start : start + max_chars])
                current = ""
    if current:
        chunks.append(current)
    return chunks


def read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n\n".join((page.extract_text() or "") for page in reader.pages)


def build_manuals_index():
    manuals_dir = ROOT / "data" / "manuals"
    if not manuals_dir.exists():
        print("! No manuals/ directory found")
        return

    documents = []
    for path in manuals_dir.glob("*"):
        if path.suffix.lower() == ".pdf":
            print(f"Reading PDF: {path.name}")
            full_text = read_pdf(path)
        elif path.suffix.lower() in {".md", ".txt"}:
            print(f"Reading text: {path.name}")
            full_text = path.read_text(errors="ignore")
        else:
            continue

        chunks = chunk_text(full_text)
        documents.extend(
            {
                "text": chunk,
                "metadata": {
                    "source": path.name,
                    "chunk_id": chunk_id,
                    "total_chunks": len(chunks),
                },
            }
            for chunk_id, chunk in enumerate(chunks)
        )

    if not documents:
        print("! No manual content extracted")
        return

    index = VectorIndex("manuals")
    index.build(documents)
    index.save(INDEX_DIR)
    print(f"-> Saved manuals index ({len(documents)} chunks)")


def main():
    build_orders_index()
    build_manuals_index()
    print("\nAll indices built.")


if __name__ == "__main__":
    main()
