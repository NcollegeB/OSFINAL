#!/usr/bin/env python3
import csv
import math
import sys
from datetime import date
from pathlib import Path


ALGORITHM_ORDER = ["monte_carlo", "matrix_mul", "dns_lookup"]
ALGORITHM_NAMES = {
    "monte_carlo": "Monte Carlo Pi",
    "matrix_mul": "Matrix Multiplication",
    "dns_lookup": "DNS Lookup",
}
WORKLOAD_NAMES = {
    "monte_carlo": "Points",
    "matrix_mul": "Matrix Size",
    "dns_lookup": "Hostnames",
}


def load_summary(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def workload_value(row: dict[str, str]) -> int:
    return int(row["workload"])


def workload_label(algorithm: str, workload: int) -> str:
    if algorithm == "monte_carlo" and workload >= 1_000_000:
        return f"{workload // 1_000_000}M"
    if algorithm == "matrix_mul":
        return f"{workload}x{workload}"
    return str(workload)


def algorithm_sort_key(algorithm: str) -> tuple[int, str]:
    try:
        return (ALGORITHM_ORDER.index(algorithm), algorithm)
    except ValueError:
        return (len(ALGORITHM_ORDER), algorithm)


def format_ms(value: float) -> str:
    if value < 10:
        return f"{value:.3f}"
    return f"{value:.2f}"


def format_percent(value: float) -> str:
    return f"{value:.2f}%"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def pair_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    by_case: dict[tuple[str, int], dict[str, dict[str, str]]] = {}
    for row in rows:
        key = (row["algorithm"], workload_value(row))
        by_case.setdefault(key, {})[row["language"]] = row

    paired = []
    for (algorithm, workload), languages in sorted(
        by_case.items(), key=lambda item: (algorithm_sort_key(item[0][0]), item[0][1])
    ):
        if "c" not in languages or "rust" not in languages:
            continue

        c = languages["c"]
        rust = languages["rust"]
        c_mean = float(c["mean_ms"])
        rust_mean = float(rust["mean_ms"])
        c_ci = float(c["ci95_half_width_ms"])
        rust_ci = float(rust["ci95_half_width_ms"])

        if c_mean < rust_mean:
            winner = "C"
            speedup = rust_mean / c_mean
        else:
            winner = "Rust"
            speedup = c_mean / rust_mean

        if c_mean + c_ci < rust_mean - rust_ci:
            ci_result = "C likely faster"
        elif rust_mean + rust_ci < c_mean - c_ci:
            ci_result = "Rust likely faster"
        else:
            ci_result = "Overlapping 95% CIs"

        paired.append(
            {
                "algorithm": algorithm,
                "workload": workload,
                "c": c,
                "rust": rust,
                "c_mean": c_mean,
                "rust_mean": rust_mean,
                "c_ci": c_ci,
                "rust_ci": rust_ci,
                "winner": winner,
                "speedup": speedup,
                "ci_result": ci_result,
            }
        )

    return paired


def chart_y_max(values: list[float]) -> str:
    if not values:
        return "1"
    value = max(values) * 1.15
    if value <= 2:
        rounded = math.ceil(value * 10) / 10
    elif value <= 10:
        rounded = math.ceil(value)
    elif value <= 100:
        rounded = math.ceil(value / 5) * 5
    elif value <= 1000:
        rounded = math.ceil(value / 50) * 50
    else:
        rounded = math.ceil(value / 500) * 500
    if float(rounded).is_integer():
        return str(int(rounded))
    return f"{rounded:.1f}"


def mermaid_runtime_chart(algorithm: str, pairs: list[dict[str, object]]) -> str:
    labels = [workload_label(algorithm, int(pair["workload"])) for pair in pairs]
    c_values = [float(pair["c_mean"]) for pair in pairs]
    rust_values = [float(pair["rust_mean"]) for pair in pairs]
    y_max = chart_y_max(c_values + rust_values)
    title = f"{ALGORITHM_NAMES.get(algorithm, algorithm)} Mean Runtime"
    x_name = WORKLOAD_NAMES.get(algorithm, "Workload")

    return "\n".join(
        [
            "```mermaid",
            "xychart-beta",
            f'    title "{title} (C bars, Rust line)"',
            f'    x-axis "{x_name}" [{", ".join(labels)}]',
            f'    y-axis "Mean runtime (ms)" 0 --> {y_max}',
            "    bar [" + ", ".join(f"{value:.3f}" for value in c_values) + "]",
            "    line [" + ", ".join(f"{value:.3f}" for value in rust_values) + "]",
            "```",
        ]
    )


def result_table(pairs: list[dict[str, object]]) -> str:
    rows = []
    for pair in pairs:
        algorithm = str(pair["algorithm"])
        rows.append(
            [
                ALGORITHM_NAMES.get(algorithm, algorithm),
                workload_label(algorithm, int(pair["workload"])),
                f"{format_ms(float(pair['c_mean']))} +/- {format_ms(float(pair['c_ci']))}",
                f"{format_ms(float(pair['rust_mean']))} +/- {format_ms(float(pair['rust_ci']))}",
                str(pair["winner"]),
                f"{float(pair['speedup']):.2f}x",
                str(pair["ci_result"]),
            ]
        )
    return markdown_table(
        [
            "Algorithm",
            "Workload",
            "C mean ms +/- 95% CI",
            "Rust mean ms +/- 95% CI",
            "Lower mean",
            "Speedup",
            "CI Reading",
        ],
        rows,
    )


def margin_table(rows: list[dict[str, str]]) -> str:
    table_rows = []
    for row in sorted(
        rows, key=lambda r: (algorithm_sort_key(r["algorithm"]), workload_value(r), r["language"])
    ):
        algorithm = row["algorithm"]
        table_rows.append(
            [
                ALGORITHM_NAMES.get(algorithm, algorithm),
                row["language"].upper() if row["language"] == "c" else "Rust",
                workload_label(algorithm, workload_value(row)),
                row["runs"],
                format_percent(float(row["margin_error_percent"])),
                format_ms(float(row["stdev_ms"])),
            ]
        )
    return markdown_table(
        ["Algorithm", "Language", "Workload", "Runs", "Margin Error", "Stdev ms"],
        table_rows,
    )


def headline_findings(pairs: list[dict[str, object]]) -> list[str]:
    findings = []
    by_algorithm: dict[str, list[dict[str, object]]] = {}
    for pair in pairs:
        by_algorithm.setdefault(str(pair["algorithm"]), []).append(pair)

    for algorithm in sorted(by_algorithm, key=algorithm_sort_key):
        algorithm_pairs = by_algorithm[algorithm]
        c_mean_wins = sum(1 for pair in algorithm_pairs if pair["winner"] == "C")
        rust_mean_wins = len(algorithm_pairs) - c_mean_wins
        c_ci_wins = sum(1 for pair in algorithm_pairs if pair["ci_result"] == "C likely faster")
        rust_ci_wins = sum(
            1 for pair in algorithm_pairs if pair["ci_result"] == "Rust likely faster"
        )
        overlap = len(algorithm_pairs) - c_ci_wins - rust_ci_wins
        findings.append(
            f"- {ALGORITHM_NAMES.get(algorithm, algorithm)}: C had the lower mean in "
            f"{c_mean_wins}/{len(algorithm_pairs)} cases and Rust had the lower mean in "
            f"{rust_mean_wins}/{len(algorithm_pairs)} cases. Using non-overlapping 95% "
            f"CIs as a conservative check: C likely faster in {c_ci_wins}, Rust likely "
            f"faster in {rust_ci_wins}, and {overlap} overlap."
        )
    return findings


def write_report(rows: list[dict[str, str]], output: Path, summary_path: Path) -> None:
    pairs = pair_rows(rows)
    algorithms = sorted({str(pair["algorithm"]) for pair in pairs}, key=algorithm_sort_key)
    total_runs = sum(int(row["runs"]) for row in rows)
    max_margin = max(float(row["margin_error_percent"]) for row in rows)
    max_margin_row = max(rows, key=lambda row: float(row["margin_error_percent"]))
    thread_counts = ", ".join(sorted({row["threads"] for row in rows}))
    run_counts = ", ".join(sorted({row["runs"] for row in rows}))
    command_threads = thread_counts if "," not in thread_counts else "<threads>"
    command_trials = run_counts if "," not in run_counts else "<trials>"
    if max_margin <= 10.0:
        margin_sentence = (
            "The target margin of error for the assignment is around 5-10%. "
            "The current summary stays within that range."
        )
    else:
        max_algorithm = ALGORITHM_NAMES.get(max_margin_row["algorithm"], max_margin_row["algorithm"])
        max_language = "C" if max_margin_row["language"] == "c" else "Rust"
        max_workload = workload_label(
            max_margin_row["algorithm"], workload_value(max_margin_row)
        )
        margin_sentence = (
            "The target margin of error for the assignment is around 5-10%. "
            f"Most current cases are within that range, but {max_algorithm} "
            f"({max_language}, workload {max_workload}) is above the target at "
            f"{max_margin:.2f}%. This should be discussed as timing noise, likely "
            "from DNS resolver/cache/network behavior."
        )

    lines = [
        "---",
        "tags:",
        "  - csci440",
        "  - operating-systems",
        "  - threads",
        "  - benchmark",
        "cssclasses:",
        "  - osfinal-paper",
        f"generated: {date.today().isoformat()}",
        f"source: {summary_path.as_posix()}",
        "---",
        "",
        "# CSCI440 Final Project: C vs Rust Thread Performance",
        "",
        "## Rubric Checklist",
        "",
        "- [ ] Approved question is clearly stated",
        "- [ ] Workloads and languages are defined",
        "- [ ] Experimental setup includes CPU, memory, OS, compiler versions, and artifacts",
        "- [ ] Testing procedure explains commands, timing method, trials, and workload sizes",
        "- [ ] Results include means, standard deviations, confidence intervals, and margin of error",
        "- [ ] Conclusion answers the question using the evidence",
        "- [ ] Learning outcome is personal and specific",
        "- [ ] Code, scripts, references, and AI citation are included",
        "",
        "## Approved Question",
        "",
        "How does the performance of threads in C compare to Rust?",
        "",
        "This project compares C programs using POSIX pthreads with Rust programs using `std::thread`. The same thread count is used for both languages, and the amount of work changes across three workloads: Monte Carlo pi estimation, matrix multiplication, and DNS hostname resolution.",
        "",
        "## Workloads",
        "",
        "- Monte Carlo pi estimation: CPU-bound random point generation and counting inside a unit circle.",
        "- Matrix multiplication: CPU-bound multiplication of square matrices using row ranges assigned to worker threads.",
        "- DNS lookup: threaded hostname resolution using the operating system resolver. This workload is intentionally noisier because DNS caching, resolver latency, and network behavior can affect timing.",
        "",
        "## Experimental Setup",
        "",
        "- Machine: 11th Gen Intel Core i5-11400F at 2.60 GHz",
        "- CPU layout: 6 cores, 12 logical CPUs",
        "- Memory available to WSL during capture: 7.7 GiB",
        "- OS: Ubuntu 24.04.1 LTS running under WSL2",
        "- Kernel: `6.6.114.1-microsoft-standard-WSL2`",
        "- C compiler: GCC 13.3.0",
        "- Rust compiler: rustc 1.94.0",
        "- Cargo: cargo 1.94.0",
        "- Threads used in current summary: " + thread_counts,
        "- Runs per language/workload case: " + run_counts,
        "",
        "Possible artifacts to discuss: WSL2 virtualization overhead, background Windows processes, CPU frequency scaling, DNS cache behavior, network latency, and cache effects in matrix multiplication.",
        "",
        "## Testing Procedure",
        "",
        "The benchmark runner builds all C and Rust programs, generates DNS input files, then runs each language/workload case repeatedly. C timing uses `clock_gettime(CLOCK_MONOTONIC)`. Rust timing uses `std::time::Instant`. The result analyzer computes the mean, standard deviation, 95% confidence interval half-width, and margin of error.",
        "",
        "Commands used:",
        "",
        "```bash",
        "cd /mnt/c/Users/19255/Documents/OS/OSFINAL",
        f"THREADS={command_threads} TRIALS={command_trials} python3 scripts/run_benchmarks.py",
        "python3 scripts/analyze_results.py results/benchmark_raw.csv results/benchmark_summary.csv",
        f"python3 scripts/make_obsidian_report.py results/benchmark_summary.csv {output.as_posix()}",
        "```",
        "",
        "Confidence value: approximately 95% confidence using z-score `1.96`.",
        "",
        "## Current Results Snapshot",
        "",
        f"- Total individual program runs summarized: {total_runs}",
        f"- Maximum current margin of error: {max_margin:.2f}%",
        "- Lower runtime is better.",
        "- In the Mermaid charts below, bars are C and the line is Rust.",
        "",
        "## Headline Findings",
        "",
        *headline_findings(pairs),
        "",
        '<div class="page-break"></div>',
        "",
        "## Runtime Graphs",
        "",
    ]

    for algorithm in algorithms:
        algorithm_pairs = [pair for pair in pairs if pair["algorithm"] == algorithm]
        lines.extend(
            [
                f"### {ALGORITHM_NAMES.get(algorithm, algorithm)}",
                "",
                mermaid_runtime_chart(algorithm, algorithm_pairs),
                "",
            ]
        )

    lines.extend(
        [
            '<div class="page-break"></div>',
            "",
            "## Results Table",
            "",
            result_table(pairs),
            "",
            "## Accuracy And Margin Of Error",
            "",
            margin_sentence + " The largest margin of error is shown in the table below.",
            "",
            margin_table(rows),
            "",
            "## Draft Interpretation",
            "",
            "The strongest current evidence is from the Monte Carlo workload. C has a lower mean runtime at every tested input size, and the 95% confidence intervals do not overlap. That supports saying C pthreads were faster than Rust threads for this CPU-bound Monte Carlo implementation on this machine.",
            "",
            "Matrix multiplication is much closer. C has a small advantage for the smallest matrix size, but the larger matrix sizes have overlapping confidence intervals. This suggests that for the matrix workload, memory access patterns and compiler optimization may matter more than the thread API itself.",
            "",
            "DNS lookup should be interpreted carefully. The means are close and the confidence intervals overlap for all DNS input sizes. Because DNS depends on the operating system resolver, cache state, and network behavior, this workload is useful as a real OS-flavored threaded task, but it is not as clean as the CPU-bound workloads.",
            "",
            "## Conclusion Draft",
            "",
            "Based on the current results, C pthreads performed better for Monte Carlo, were roughly comparable to Rust for matrix multiplication, and were roughly comparable for DNS lookup. The answer is therefore workload-dependent: C showed a clear advantage in one CPU-bound benchmark, but the other workloads did not show a consistently statistically meaningful difference.",
            "",
            "## Learning Outcome Notes",
            "",
            "- Thread performance is not only about the language; workload design, memory behavior, OS services, and timing noise matter.",
            "- Repeated trials are necessary because a single run could give a misleading result.",
            "- DNS is a good example of an operating-system-related workload, but it is harder to control than pure CPU work.",
            "- Rust's thread API adds safety and ergonomics, while still mapping to native OS threads.",
            "- Confidence intervals helped separate strong evidence from small differences that may just be noise.",
            "",
            "## References And Citation Reminders",
            "",
            "- Cite the class final project prompt.",
            "- Cite POSIX pthread documentation and `getaddrinfo` documentation.",
            "- Cite Rust `std::thread`, `std::time::Instant`, and `std::net::ToSocketAddrs` documentation.",
            "- Cite any code adapted from the earlier DNS assignment.",
            "- Cite AI assistance using `docs/ai-citation-log.md`.",
        ]
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if len(sys.argv) not in (2, 3):
        raise SystemExit(
            "Usage: make_obsidian_report.py <summary_csv> [output_markdown]"
        )

    summary_path = Path(sys.argv[1])
    output = Path(sys.argv[2]) if len(sys.argv) == 3 else Path("docs/generated-results.md")
    protected_outputs = {
        Path("docs/obsidian-final-project.md"),
        Path("obsidian-final-project.md"),
    }
    if output.as_posix() in {path.as_posix() for path in protected_outputs}:
        raise SystemExit(
            "Refusing to overwrite an editable paper file. Use docs/generated-results.md "
            "or another generated-only output path."
        )

    rows = load_summary(summary_path)
    if not rows:
        raise SystemExit(f"No rows found in {summary_path}")

    write_report(rows, output, summary_path)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
