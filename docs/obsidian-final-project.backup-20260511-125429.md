---
tags:
  - csci440
  - operating-systems
  - threads
  - benchmark
cssclasses:
  - osfinal-paper
generated: 2026-05-11
source: results/benchmark_summary.csv
---

# CSCI440 Final Project: C vs Rust Thread Performance

## Approved Question

How does the performance of threads in C compare to Rust?

This project compares C programs using POSIX pthreads with Rust programs using `std::thread`. The same thread count is used for both languages, and the amount of work changes across three workloads: Monte Carlo pi estimation, matrix multiplication, and DNS hostname resolution.

## Workloads

- Monte Carlo pi estimation: CPU-bound random point generation and counting inside a unit circle.
- Matrix multiplication: CPU-bound multiplication of square matrices using row ranges assigned to worker threads.
- DNS lookup: threaded hostname resolution using the operating system resolver. This workload is intentionally noisier because DNS caching, resolver latency, and network behavior can affect timing.

## Experimental Setup

- Machine: 11th Gen Intel Core i5-11400F at 2.60 GHz
- CPU layout: 6 cores, 12 logical CPUs
- Memory available to WSL during capture: 7.7 GiB
- OS: Ubuntu 24.04.1 LTS running under WSL2
- Kernel: `6.6.114.1-microsoft-standard-WSL2`
- C compiler: GCC 13.3.0
- Rust compiler: rustc 1.94.0
- Cargo: cargo 1.94.0
- Threads used in current summary: 4
- Runs per language/workload case: 50

Possible artifacts to discuss: WSL2 virtualization overhead, background Windows processes, CPU frequency scaling, DNS cache behavior, network latency, and cache effects in matrix multiplication.

## Testing Procedure

The benchmark runner builds all C and Rust programs, generates DNS input files, then runs each language/workload case repeatedly. C timing uses `clock_gettime(CLOCK_MONOTONIC)`. Rust timing uses `std::time::Instant`. The result analyzer computes the mean, standard deviation, 95% confidence interval half-width, and margin of error.

Commands used:

```bash
cd /mnt/c/Users/19255/Documents/OS/OSFINAL
THREADS=4 TRIALS=30 python3 scripts/run_benchmarks.py
python3 scripts/analyze_results.py results/benchmark_raw.csv results/benchmark_summary.csv
python3 scripts/make_obsidian_report.py results/benchmark_summary.csv docs/obsidian-final-project.md
```

Confidence value: approximately 95% confidence using z-score `1.96`.

## Current Results Snapshot

- Total individual program runs summarized: 900
- Maximum current margin of error: 28.93%
- Lower runtime is better.
- In the Mermaid charts below, bars are C and the line is Rust.

## Headline Findings

- Monte Carlo Pi: C had the lower mean in 3/3 cases and Rust had the lower mean in 0/3 cases. Using non-overlapping 95% CIs as a conservative check: C likely faster in 3, Rust likely faster in 0, and 0 overlap.
- Matrix Multiplication: C had the lower mean in 2/3 cases and Rust had the lower mean in 1/3 cases. Using non-overlapping 95% CIs as a conservative check: C likely faster in 2, Rust likely faster in 0, and 1 overlap.
- DNS Lookup: C had the lower mean in 1/3 cases and Rust had the lower mean in 2/3 cases. Using non-overlapping 95% CIs as a conservative check: C likely faster in 0, Rust likely faster in 0, and 3 overlap.

<div class="page-break"></div>

## Runtime Graphs

### Monte Carlo Pi

```mermaid
xychart-beta
    title "Monte Carlo Pi Mean Runtime (C bars, Rust line)"
    x-axis "Points" [1M, 5M, 10M]
    y-axis "Mean runtime (ms)" 0 --> 20
    bar [1.331, 6.009, 11.349]
    line [1.827, 7.445, 14.674]
```

### Matrix Multiplication

```mermaid
xychart-beta
    title "Matrix Multiplication Mean Runtime (C bars, Rust line)"
    x-axis "Matrix Size" [128x128, 256x256, 512x512]
    y-axis "Mean runtime (ms)" 0 --> 45
    bar [0.738, 4.572, 35.911]
    line [0.808, 4.692, 35.860]
```

### DNS Lookup

```mermaid
xychart-beta
    title "DNS Lookup Mean Runtime (C bars, Rust line)"
    x-axis "Hostnames" [30, 150, 300]
    y-axis "Mean runtime (ms)" 0 --> 600
    bar [62.720, 249.107, 505.029]
    line [53.988, 253.451, 491.187]
```

<div class="page-break"></div>

## Results Table

| Algorithm | Workload | C mean ms +/- 95% CI | Rust mean ms +/- 95% CI | Lower mean | Speedup | CI Reading |
| --- | --- | --- | --- | --- | --- | --- |
| Monte Carlo Pi | 1M | 1.331 +/- 0.031 | 1.827 +/- 0.044 | C | 1.37x | C likely faster |
| Monte Carlo Pi | 5M | 6.009 +/- 0.187 | 7.445 +/- 0.205 | C | 1.24x | C likely faster |
| Monte Carlo Pi | 10M | 11.35 +/- 0.212 | 14.67 +/- 0.423 | C | 1.29x | C likely faster |
| Matrix Multiplication | 128x128 | 0.738 +/- 0.010 | 0.808 +/- 0.021 | C | 1.09x | C likely faster |
| Matrix Multiplication | 256x256 | 4.572 +/- 0.023 | 4.692 +/- 0.043 | C | 1.03x | C likely faster |
| Matrix Multiplication | 512x512 | 35.91 +/- 0.109 | 35.86 +/- 0.171 | Rust | 1.00x | Overlapping 95% CIs |
| DNS Lookup | 30 | 62.72 +/- 18.15 | 53.99 +/- 3.285 | Rust | 1.16x | Overlapping 95% CIs |
| DNS Lookup | 150 | 249.11 +/- 8.254 | 253.45 +/- 10.56 | C | 1.02x | Overlapping 95% CIs |
| DNS Lookup | 300 | 505.03 +/- 13.62 | 491.19 +/- 7.769 | Rust | 1.03x | Overlapping 95% CIs |

## Accuracy And Margin Of Error

The target margin of error for the assignment is around 5-10%. Most current cases are within that range, but DNS Lookup (C, workload 30) is above the target at 28.93%. This should be discussed as timing noise, likely from DNS resolver/cache/network behavior. The largest margin of error is shown in the table below.

| Algorithm | Language | Workload | Runs | Margin Error | Stdev ms |
| --- | --- | --- | --- | --- | --- |
| Monte Carlo Pi | C | 1M | 50 | 2.32% | 0.111 |
| Monte Carlo Pi | Rust | 1M | 50 | 2.39% | 0.158 |
| Monte Carlo Pi | C | 5M | 50 | 3.11% | 0.673 |
| Monte Carlo Pi | Rust | 5M | 50 | 2.76% | 0.740 |
| Monte Carlo Pi | C | 10M | 50 | 1.87% | 0.764 |
| Monte Carlo Pi | Rust | 10M | 50 | 2.88% | 1.525 |
| Matrix Multiplication | C | 128x128 | 50 | 1.42% | 0.038 |
| Matrix Multiplication | Rust | 128x128 | 50 | 2.65% | 0.077 |
| Matrix Multiplication | C | 256x256 | 50 | 0.50% | 0.083 |
| Matrix Multiplication | Rust | 256x256 | 50 | 0.92% | 0.155 |
| Matrix Multiplication | C | 512x512 | 50 | 0.30% | 0.393 |
| Matrix Multiplication | Rust | 512x512 | 50 | 0.48% | 0.618 |
| DNS Lookup | C | 30 | 50 | 28.93% | 65.47 |
| DNS Lookup | Rust | 30 | 50 | 6.09% | 11.85 |
| DNS Lookup | C | 150 | 50 | 3.31% | 29.78 |
| DNS Lookup | Rust | 150 | 50 | 4.17% | 38.11 |
| DNS Lookup | C | 300 | 50 | 2.70% | 49.12 |
| DNS Lookup | Rust | 300 | 50 | 1.58% | 28.03 |

## Draft Interpretation

The strongest current evidence is from the Monte Carlo workload. C has a lower mean runtime at every tested input size, and the 95% confidence intervals do not overlap. That supports saying C pthreads were faster than Rust threads for this CPU-bound Monte Carlo implementation on this machine.

Matrix multiplication is much closer. C has a small advantage for the smallest matrix size, but the larger matrix sizes have overlapping confidence intervals. This suggests that for the matrix workload, memory access patterns and compiler optimization may matter more than the thread API itself.

DNS lookup should be interpreted carefully. The means are close and the confidence intervals overlap for all DNS input sizes. Because DNS depends on the operating system resolver, cache state, and network behavior, this workload is useful as a real OS-flavored threaded task, but it is not as clean as the CPU-bound workloads.

## Conclusion Draft

Based on the current results, C pthreads performed better for Monte Carlo, were roughly comparable to Rust for matrix multiplication, and were roughly comparable for DNS lookup. The answer is therefore workload-dependent: C showed a clear advantage in one CPU-bound benchmark, but the other workloads did not show a consistently statistically meaningful difference.

## Learning Outcome Notes

- Thread performance is not only about the language; workload design, memory behavior, OS services, and timing noise matter.
- Repeated trials are necessary because a single run could give a misleading result.
- DNS is a good example of an operating-system-related workload, but it is harder to control than pure CPU work.
- Rust's thread API adds safety and ergonomics, while still mapping to native OS threads.
- Confidence intervals helped separate strong evidence from small differences that may just be noise.

## References And Citation Reminders

- Cite the class final project prompt.
- Cite POSIX pthread documentation and `getaddrinfo` documentation.
- Cite Rust `std::thread`, `std::time::Instant`, and `std::net::ToSocketAddrs` documentation.
- Cite any code adapted from the earlier DNS assignment.
- Cite AI assistance using `docs/ai-citation-log.md`.
