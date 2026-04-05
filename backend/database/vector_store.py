import faiss
import numpy as np
import pickle
from pathlib import Path
from typing import List, Optional, Dict
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.config import get_settings


class VectorStore:
    def __init__(self, index_path: Optional[Path] = None, dimension: int = 384):
        self.settings = get_settings()
        self.index_path = index_path or self.settings.faiss_index_path
        self.dimension = dimension
        self.index: Optional[faiss.Index] = None
        self.metadata: Dict[str, dict] = {}
        self._load_or_create_index()

    def _load_or_create_index(self):
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        index_file = self.index_path.with_suffix(".index")
        meta_file = self.index_path.with_suffix(".pkl")

        if index_file.exists() and meta_file.exists():
            self.index = faiss.read_index(str(index_file))
            with open(meta_file, "rb") as f:
                self.metadata = pickle.load(f)
        else:
            self.index = faiss.IndexFlatIP(self.dimension)
            self.metadata = {}

    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        faiss.normalize_L2(vectors)
        return vectors

    def add_vectors(
        self, ids: List[str], vectors: np.ndarray, metadata: List[dict] = None
    ):
        vectors = np.array(vectors).astype("float32")
        vectors = self._normalize(vectors)

        self.index.add(vectors)

        for i, id_val in enumerate(ids):
            self.metadata[id_val] = {
                "index": self.index.ntotal - len(ids) + i,
                **(metadata[i] if metadata else {}),
            }

        self._save()

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[dict]:
        query_vector = np.array(query_vector).astype("float32").reshape(1, -1)
        query_vector = self._normalize(query_vector)

        distances, indices = self.index.search(query_vector, top_k)

        results = []
        id_to_index = {v["index"]: k for k, v in self.metadata.items()}

        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0 and idx in id_to_index:
                results.append(
                    {
                        "id": id_to_index[idx],
                        "score": float(dist),
                        "metadata": self.metadata[id_to_index[idx]],
                    }
                )

        return results

    def get_vector(self, id_val: str) -> Optional[np.ndarray]:
        if id_val not in self.metadata:
            return None

        idx = self.metadata[id_val]["index"]
        vectors = np.zeros((1, self.dimension), dtype="float32")
        self.index.reconstruct(idx, vectors[0])
        return vectors[0]

    def delete_vector(self, id_val: str):
        if id_val not in self.metadata:
            return

        del self.metadata[id_val]
        self._save()

    def _save(self):
        index_file = self.index_path.with_suffix(".index")
        meta_file = self.index_path.with_suffix(".pkl")

        faiss.write_index(self.index, str(index_file))
        with open(meta_file, "wb") as f:
            pickle.dump(self.metadata, f)

    def clear(self):
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = {}
        self._save()

    def clear_all_vectors(self):
        self.clear()


vector_store = VectorStore()
