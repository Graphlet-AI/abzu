from typing import Literal

import numpy as np
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from sklearn.cluster import AgglomerativeClustering


class E5EntityBlocker:

    def __init__(self, model_name: str = "Qwen/Qwen3-Embedding-4B"):
        """
        E5EntityBlocker blocks data and returns agglomerative clusters. Initialize with the large E5 model.
        """
        device: Literal["cpu", "cuda", "mps"]
        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
        self.model = SentenceTransformer(
            model_name, device=device, model_kwargs={"device_map": "auto"}
        )

    def encode_companies(self, company_names: list[str]) -> np.ndarray:
        """
        Encode company names into embeddings.

        With the standard E5 model, we simply encode the text as-is.
        No special formatting or instruction prefixes needed!
        """
        embeddings = self.model.encode(
            company_names,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        return embeddings

    def calculate_similarity_matrix(self, company_names: list[str]) -> np.ndarray:
        """
        Calculate pairwise similarity matrix for all companies.

        This is straightforward with standard E5:
        - Encode all companies once
        - Compute standard cosine similarity
        - Result is naturally symmetric
        """
        # Handle empty list
        if len(company_names) == 0:
            return np.array([]).reshape(0, 0)

        # Get embeddings for all companies
        embeddings: np.ndarray = self.encode_companies(company_names)

        # Calculate cosine similarity - it's symmetric by default!
        similarity_matrix: np.ndarray = cos_sim(embeddings, embeddings).numpy()

        return similarity_matrix

    def create_blocks(
        self, company_names: list[str], threshold: float = 0.8
    ) -> dict[int, list[str]]:
        """
        Create blocking groups for entity resolution.

        Args:
            company_names: List of company names to block
            threshold: Similarity threshold (0-1 scale, unlike instruct model's 0-100)

        Returns:
            Dictionary mapping block_id to list of companies in that block
        """
        # Handle edge cases
        if len(company_names) == 0:
            return {}
        if len(company_names) == 1:
            return {0: company_names}

        # Calculate similarities
        similarity_matrix = self.calculate_similarity_matrix(company_names)

        # Convert similarity to distance for clustering
        distance_matrix = 1 - similarity_matrix

        # Perform hierarchical clustering
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=1 - threshold,  # Convert back to distance
            metric="precomputed",
            linkage="average",  # Average linkage often works well for entity resolution
        )

        cluster_labels = clustering.fit_predict(distance_matrix)

        # Organize results into blocks
        blocks = {}
        for idx, label in enumerate(cluster_labels):
            if label not in blocks:
                blocks[label] = []
            blocks[label].append(company_names[idx])

        return blocks

    def find_similar_companies(
        self, query_company: str, candidate_companies: list[str], top_k: int = 5
    ) -> list[dict[str, str | float]]:
        """
        Find companies most similar to a query company.

        With standard E5, this is just cosine similarity ranking.
        """
        # Encode query and candidates together for efficiency
        all_companies: list[str] = [query_company] + list(candidate_companies)
        embeddings: np.ndarray = self.encode_companies(all_companies)

        # Query is first, candidates are the rest
        query_embedding: np.ndarray = embeddings[0:1]
        candidate_embeddings: np.ndarray = embeddings[1:]

        # Calculate similarities
        similarities: np.ndarray = cos_sim(query_embedding, candidate_embeddings).numpy()[0]

        # Get top-k results
        top_indices: np.ndarray = np.argsort(similarities)[::-1][:top_k]

        results: list[dict[str, str | float]] = []
        for idx in top_indices:
            results.append({"company": candidate_companies[idx], "similarity": similarities[idx]})

        return results

    def find_duplicates(self, company_names: list[str], threshold: float = 0.8) -> pd.DataFrame:
        """
        Find potential duplicate companies based on similarity threshold.

        Returns DataFrame with company pairs and their similarities.
        """
        similarity_matrix = self.calculate_similarity_matrix(company_names)

        duplicates = []
        # Only check upper triangle to avoid duplicate pairs
        for i in range(len(company_names)):
            for j in range(i + 1, len(company_names)):
                if similarity_matrix[i][j] >= threshold:
                    duplicates.append(
                        {
                            "company1": company_names[i],
                            "company2": company_names[j],
                            "similarity": similarity_matrix[i][j],
                        }
                    )

        # Return sorted by similarity
        if duplicates:
            return pd.DataFrame(duplicates).sort_values("similarity", ascending=False)
        else:
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=["company1", "company2", "similarity"])

    def get_pairwise_similarity(self, company1: str, company2: str) -> float:
        """
        Get similarity between two specific companies.

        Simple helper method for checking individual pairs.
        """
        embeddings: np.ndarray = self.encode_companies([company1, company2])
        similarity: float = cos_sim([embeddings[0]], [embeddings[1]]).numpy()[0][0]
        return similarity
