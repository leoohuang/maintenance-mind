"""Shared vector retrieval base class for work orders and manual chunks."""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import faiss
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class VectorIndex:
    """Wrap a FAISS cosine-similarity index over document dictionaries."""

    def __init__(self, name: str, model_name: str = EMBEDDING_MODEL):
        self.name = name
        self.model = SentenceTransformer(model_name)
        self.documents: list[dict[str, Any]] = []
        self.index: faiss.Index | None = None

    @property
    def dim(self) -> int:
        return self.model.get_embedding_dimension()

    def build(self, documents: list[dict[str, Any]]):
        """Build an in-memory FAISS index from documents with `text` fields."""
        self.documents = documents
        texts = [document["text"] for document in documents]
        embeddings = self.model.encode(
            texts, show_progress_bar=True, normalize_embeddings=True
        ).astype("float32")
        self.index = faiss.IndexFlatIP(self.dim)
        self.index.add(embeddings)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if self.index is None or not self.documents:
            return []
        query_vector = self.model.encode(
            [query], normalize_embeddings=True
        ).astype("float32")
        scores, indices = self.index.search(query_vector, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.documents):
                continue
            document = dict(self.documents[idx])
            document["score"] = float(score)
            results.append(document)
        return results

    def save(self, dir_path: Path):
        if self.index is None:
            raise RuntimeError("Cannot save a vector index before build or load.")
        dir_path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(dir_path / f"{self.name}.faiss"))
        with open(dir_path / f"{self.name}.pkl", "wb") as handle:
            pickle.dump(self.documents, handle)

    def load(self, dir_path: Path) -> bool:
        index_path = dir_path / f"{self.name}.faiss"
        documents_path = dir_path / f"{self.name}.pkl"
        if not index_path.exists() or not documents_path.exists():
            return False
        self.index = faiss.read_index(str(index_path))
        with open(documents_path, "rb") as handle:
            self.documents = pickle.load(handle)
        return True
