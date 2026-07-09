import math


class PerformanceStatistics:
    @staticmethod
    def calculate_percentiles(latencies: list[float]) -> dict[str, float]:
        if not latencies:
            return {
                "min": 0.0,
                "max": 0.0,
                "mean": 0.0,
                "median": 0.0,
                "p90": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "std_dev": 0.0,
            }

        sorted_lats = sorted(latencies)
        n = len(sorted_lats)

        mean_val = sum(sorted_lats) / n
        variance = sum((x - mean_val) ** 2 for x in sorted_lats) / n
        std_dev = math.sqrt(variance)

        def get_percentile(p: float) -> float:
            k = (n - 1) * p
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return sorted_lats[int(k)]
            return sorted_lats[f] * (c - k) + sorted_lats[c] * (k - f)

        return {
            "min": float(sorted_lats[0]),
            "max": float(sorted_lats[-1]),
            "mean": float(mean_val),
            "median": get_percentile(0.50),
            "p90": get_percentile(0.90),
            "p95": get_percentile(0.95),
            "p99": get_percentile(0.99),
            "std_dev": float(std_dev),
        }
