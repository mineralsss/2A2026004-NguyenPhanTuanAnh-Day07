from __future__ import annotations
import dotenv

from typing import Any, Callable

from .chunking import _dot, compute_similarity
from .embeddings import _mock_embed
from .models import Document

dotenv.load_dotenv()


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401
            from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
            client = chromadb.PersistentClient(path="./chroma_db")
            self._collection = client.create_collection(name=self._collection_name, embedding_function=OpenAIEmbeddingFunction(api_key_env_var=dotenv.get_key(".env", "OPENAI_API_KEY"), model_name="text-embedding-3-small"))

            # TODO: initialize chromadb client + collection
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        # TODO: build a normalized stored record for one document
        record_id = str(self._next_index)
        self._next_index += 1
        metadata = dict(doc.metadata)
        metadata["doc_id"] = doc.id
        return {
            "id": record_id,
            "content": doc.content,
            "embedding": self._embedding_fn(doc.content),
            "metadata": metadata,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        # TODO: run in-memory similarity search over provided records
        if not records:
            return []
        query_embedding = self._embedding_fn(query)
        scored_records = []
        for record in records:
            score = compute_similarity(query_embedding, record["embedding"])
            scored_records.append({
                "id": record["id"],
                "content": record["content"],
                "metadata": record["metadata"],
                "score": score,
            })
        scored_records.sort(key=lambda r: r["score"], reverse=True)
        return scored_records[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        # TODO: embed each doc and add to store
        for doc in docs:
            record = self._make_record(doc)
            if self._use_chroma:
                self._collection.add(ids=[record["id"]], documents=[record["content"]], embeddings=[record["embedding"]], metadatas=[record["metadata"]])
            else:
                self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        # TODO: embed query, compute similarities, return top_k
        if self._use_chroma and self._collection is not None:
            result = self._collection.query(query_embeddings=[self._embedding_fn(query)], n_results=top_k)
            documents = result.get("documents", [[]])[0]
            metadatas = result.get("metadatas", [[]])[0]
            distances = result.get("distances", [[]])[0]
            records: list[dict[str, Any]] = []
            for content, metadata, distance in zip(documents, metadatas, distances, strict=False):
                records.append({
                    "content": content,
                    "metadata": metadata,
                    "score": -float(distance) if distance is not None else 0.0,
                })
            records.sort(key=lambda item: item["score"], reverse=True)
            return records[:top_k]
        return self._search_records(query, self._store, top_k=top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        # TODO
        return self._collection.count() if self._use_chroma else len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        # TODO: filter by metadata, then search among filtered chunks
        if self._use_chroma and self._collection is not None:
            result = self._collection.query(
                query_embeddings=[self._embedding_fn(query)],
                n_results=top_k,
                where=metadata_filter or None,
            )
            documents = result.get("documents", [[]])[0]
            metadatas = result.get("metadatas", [[]])[0]
            distances = result.get("distances", [[]])[0]
            records: list[dict[str, Any]] = []
            for content, metadata, distance in zip(documents, metadatas, distances, strict=False):
                records.append({
                    "content": content,
                    "metadata": metadata,
                    "score": -float(distance) if distance is not None else 0.0,
                })
            records.sort(key=lambda item: item["score"], reverse=True)
            return records[:top_k]
        
        records = self._store
        if metadata_filter:
            records = [record for record in records if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())]
        return self._search_records(query, records, top_k) 

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        # TODO: remove all stored chunks where metadata['doc_id'] == doc_id
        if self._use_chroma:
            # ChromaDB doesn't support deletion by metadata, so we need to query for matching records first
            matching = self._collection.query(where={"doc_id": doc_id}, n_results=self.get_collection_size())
            ids_to_delete = matching["ids"][0]
            if ids_to_delete:
                self._collection.delete(ids=ids_to_delete)
                return True
            return False
        else:
            initial_len = len(self._store)
            self._store = [record for record in self._store if record["metadata"].get("doc_id") != doc_id]
            return len(self._store) < initial_len
