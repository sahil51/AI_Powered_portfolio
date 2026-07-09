from __future__ import annotations

import math

from application.retrieval.models import ScoreStrategy


class ScoreFusion:
    @staticmethod
    def normalize_scores(scores: list[float], method: str = "min_max") -> list[float]:
        if not scores:
            return []
        if method == "min_max":
            min_s = min(scores)
            max_s = max(scores)
            if max_s == min_s:
                return [1.0] * len(scores)
            return [(s - min_s) / (max_s - min_s) for s in scores]
        elif method == "z_score":
            n = len(scores)
            if n == 0:
                return scores
            mean = sum(scores) / n
            variance = sum((s - mean) ** 2 for s in scores) / n
            std = math.sqrt(variance) if variance > 0 else 1.0
            return [(s - mean) / std for s in scores]
        elif method == "rank":
            sorted_unique = sorted(set(scores), reverse=True)
            rank_map = {v: i for i, v in enumerate(sorted_unique)}
            n = len(sorted_unique)
            if n <= 1:
                return [1.0] * len(scores)
            return [1.0 - rank_map[s] / (n - 1) for s in scores]
        return scores

    @staticmethod
    def weighted_avg(
        semantic_scores: list[tuple[str, float]],
        keyword_scores: list[tuple[str, float]],
        metadata_scores: list[tuple[str, float]],
        weights: tuple[float, float, float] = (0.5, 0.3, 0.2),
        strategy: ScoreStrategy = ScoreStrategy.WEIGHTED_AVG,
    ) -> dict[str, float]:
        w_sem, w_kw, w_meta = weights

        sem_map = dict(semantic_scores)
        kw_map = dict(keyword_scores)
        meta_map = dict(metadata_scores)

        all_ids = set(sem_map.keys()) | set(kw_map.keys()) | set(meta_map.keys())
        result: dict[str, float] = {}

        if strategy == ScoreStrategy.WEIGHTED_AVG:
            for cid in all_ids:
                result[cid] = (
                    w_sem * sem_map.get(cid, 0.0)
                    + w_kw * kw_map.get(cid, 0.0)
                    + w_meta * meta_map.get(cid, 0.0)
                )
        elif strategy == ScoreStrategy.MAX:
            for cid in all_ids:
                result[cid] = max(
                    sem_map.get(cid, 0.0),
                    kw_map.get(cid, 0.0),
                    meta_map.get(cid, 0.0),
                )
        elif strategy == ScoreStrategy.MIN:
            for cid in all_ids:
                scores = [s for s in (sem_map.get(cid, 0.0), kw_map.get(cid, 0.0), meta_map.get(cid, 0.0)) if s > 0]
                result[cid] = min(scores) if scores else 0.0
        else:
            for cid in all_ids:
                result[cid] = (
                    w_sem * sem_map.get(cid, 0.0)
                    + w_kw * kw_map.get(cid, 0.0)
                    + w_meta * meta_map.get(cid, 0.0)
                )

        return result

    @staticmethod
    def reciprocal_rank_fusion(
        rankings: list[list[str]],
        k: int = 60,
    ) -> dict[str, float]:
        scores: dict[str, float] = {}
        for ranking in rankings:
            for rank, cid in enumerate(ranking):
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
        return scores

    @staticmethod
    def distribution_based_score_fusion(
        score_lists: list[list[tuple[str, float]]],
    ) -> dict[str, float]:
        all_scores: dict[str, list[float]] = {}
        for score_list in score_lists:
            for cid, score in score_list:
                if cid not in all_scores:
                    all_scores[cid] = []
                all_scores[cid].append(score)

        result: dict[str, float] = {}
        for cid, scores in all_scores.items():
            if scores:
                result[cid] = sum(scores) / len(scores)
            else:
                result[cid] = 0.0
        return result
