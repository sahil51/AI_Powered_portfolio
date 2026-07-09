from __future__ import annotations

import math
from collections.abc import Sequence

from application.retrieval.models import SearchResult


class ScoreNormalizer:
    @staticmethod
    def min_max(scores: list[float]) -> list[float]:
        if not scores:
            return []
        min_s = min(scores)
        max_s = max(scores)
        if max_s == min_s:
            return [1.0] * len(scores)
        return [(s - min_s) / (max_s - min_s) for s in scores]

    @staticmethod
    def z_score(scores: list[float]) -> list[float]:
        if not scores:
            return []
        n = len(scores)
        mean = sum(scores) / n
        variance = sum((s - mean) ** 2 for s in scores) / n
        std = math.sqrt(variance) if variance > 0 else 1.0
        return [(s - mean) / std for s in scores]

    @staticmethod
    def rank_based(scores: list[float]) -> list[float]:
        if not scores:
            return []
        sorted_unique = sorted(set(scores), reverse=True)
        rank_map = {v: i for i, v in enumerate(sorted_unique)}
        n = len(sorted_unique)
        if n <= 1:
            return [1.0] * len(scores)
        return [1.0 - rank_map[s] / (n - 1) for s in scores]


class MMRReranker:
    def __init__(self, lambda_: float = 0.7) -> None:
        self._lambda = lambda_

    async def rerank(
        self,
        candidates: Sequence[SearchResult],
        top_k: int,
        embeddings: list[list[float]] | None = None,
    ) -> list[SearchResult]:
        if not candidates:
            return []

        candidates_list = list(candidates)
        selected: list[SearchResult] = []
        remaining = list(candidates_list)

        while len(selected) < top_k and remaining:
            mmr_scores: list[float] = []
            for i, candidate in enumerate(remaining):
                relevance = candidate.score
                if selected and embeddings:
                    max_sim = max(
                        self._cosine_similarity(embeddings[candidates_list.index(candidate)],
                                                 embeddings[candidates_list.index(s)])
                        for s in selected
                    )
                else:
                    max_sim = 0.0
                mmr = self._lambda * relevance - (1 - self._lambda) * max_sim
                mmr_scores.append(mmr)

            best_idx = max(range(len(remaining)), key=lambda i: mmr_scores[i])
            best = remaining.pop(best_idx)
            best.rerank_score = mmr_scores[best_idx]
            selected.append(best)

        return selected

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
