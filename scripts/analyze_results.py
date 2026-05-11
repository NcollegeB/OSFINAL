#!/usr/bin/env python3
import csv
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path


Z_95 = 1.96


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: analyze_results.py <raw_csv> <summary_csv>")

    raw_csv = Path(sys.argv[1])
    summary_csv = Path(sys.argv[2])
    groups: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)

    with raw_csv.open("r", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            key = (row["language"], row["algorithm"], row["threads"], row["workload"])
            groups[key].append(float(row["elapsed_ms"]))

    fieldnames = [
        "language",
        "algorithm",
        "threads",
        "workload",
        "runs",
        "mean_ms",
        "stdev_ms",
        "min_ms",
        "max_ms",
        "ci95_half_width_ms",
        "margin_error_percent",
    ]

    with summary_csv.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for (language, algorithm, threads, workload), values in sorted(groups.items()):
            runs = len(values)
            mean = statistics.mean(values)
            stdev = statistics.stdev(values) if runs > 1 else 0.0
            ci_half_width = Z_95 * stdev / math.sqrt(runs) if runs > 1 else 0.0
            margin_percent = (ci_half_width / mean) * 100.0 if mean > 0 else 0.0

            writer.writerow(
                {
                    "language": language,
                    "algorithm": algorithm,
                    "threads": threads,
                    "workload": workload,
                    "runs": runs,
                    "mean_ms": f"{mean:.6f}",
                    "stdev_ms": f"{stdev:.6f}",
                    "min_ms": f"{min(values):.6f}",
                    "max_ms": f"{max(values):.6f}",
                    "ci95_half_width_ms": f"{ci_half_width:.6f}",
                    "margin_error_percent": f"{margin_percent:.2f}",
                }
            )

    print(f"Wrote {summary_csv}")


if __name__ == "__main__":
    main()

