"""ChromaDB vector store for vulnerability data."""

from datetime import datetime, timezone
from typing import Any

import chromadb

from cyberscale.store.embeddings import EmbeddingModel


class VulnStore:
    """Persistent vector store for vulnerability descriptions and metadata."""

    COLLECTION_NAME = "vulnerabilities"

    def __init__(
        self,
        persist_dir: str = "data/chromadb",
        embedding_model: EmbeddingModel | None = None,
    ):
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._embedder = embedding_model or EmbeddingModel()
        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def add(
        self,
        cve_id: str,
        description: str,
        cvss_score: float | None = None,
        cvss_version: str | None = None,
        cwe: str | None = None,
        source: str = "manual",
        exploitation_status: str = "none",
    ) -> None:
        """Add or update a vulnerability in the store."""
        embedding = self._embedder.encode([description])[0]
        metadata: dict[str, Any] = {
            "cve_id": cve_id,
            "source": source,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "exploitation_status": exploitation_status,
        }
        if cvss_score is not None:
            metadata["cvss_score"] = cvss_score
        if cvss_version:
            metadata["cvss_version"] = cvss_version
        if cwe:
            metadata["cwe"] = cwe

        self._collection.upsert(
            ids=[cve_id],
            embeddings=[embedding],
            documents=[description],
            metadatas=[metadata],
        )

    def get_by_cve_id(self, cve_id: str) -> dict[str, Any] | None:
        """Retrieve a vulnerability by CVE ID."""
        try:
            result = self._collection.get(
                ids=[cve_id], include=["documents", "metadatas"]
            )
        except Exception:
            return None
        if not result["ids"]:
            return None
        return {
            "cve_id": cve_id,
            "description": result["documents"][0],
            **result["metadatas"][0],
        }

    def search_similar(
        self, description: str, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """Find similar vulnerabilities by description embedding."""
        embedding = self._embedder.encode([description])[0]
        results = self._collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        entries = []
        for i, cve_id in enumerate(results["ids"][0]):
            entries.append({
                "cve_id": cve_id,
                "description": results["documents"][0][i],
                "distance": results["distances"][0][i],
                **results["metadatas"][0][i],
            })
        return entries

    def count(self) -> int:
        """Return the number of entries in the store."""
        return self._collection.count()
