# OSFINAL: C vs Rust Thread Performance

## Project Question

How does the performance of threads in C compare to Rust for parallel workloads?

This project compares C `pthread` programs against Rust `std::thread` programs using the same thread count and increasing workload sizes. The planned workloads are:

- Monte Carlo estimation of pi
- Matrix multiplication
- DNS hostname resolution

The previous DNS assignment in `../CSCI440-DNS-Name-Resolution-Engine-IPC` can still be useful for DNS input files and lookup ideas, but its main implementation is process/IPC based. For this final project, the DNS benchmark should use real threads in both languages so the comparison matches the approved question.

## Folder Layout

- `c/`: C pthread implementations and Makefile
- `rust/`: Rust implementations using `std::thread`
- `scripts/`: benchmark runner, result analyzer, and graph generator
- `data/dns/`: DNS hostname inputs
- `docs/`: project notes, paper outline, references, and AI citation log
- `results/`: generated CSV files and summaries

## Recommended Experiment

Use one thread count for all runs and vary only the amount of work. The current collected results use 12 worker threads:

- Monte Carlo: 1,000,000; 5,000,000; 10,000,000 points
- Matrix multiplication: 128x128; 256x256; 512x512 matrices
- DNS: 50; 200; 500 unique hostnames

Run each case many times. The assignment suggests that 30 or more runs per case is common for meaningful timing results.

## Build and Run

These commands are intended for Ubuntu, WSL, or another Linux environment with `gcc`, `make`, `python3`, and Rust installed.

```bash
cd OSFINAL
make -C c
cargo build --release --manifest-path rust/Cargo.toml
```

Run the full benchmark suite:

```bash
THREADS=12 TRIALS=50 DNS_SIZES=50,200,500 python3 scripts/run_benchmarks.py
python3 scripts/analyze_results.py results/benchmark_raw.csv results/benchmark_summary.csv
python3 scripts/make_graphs.py results/benchmark_summary.csv results/graphs
```

For quick smoke tests:

```bash
THREADS=12 TRIALS=2 DNS_SIZES=50,200,500 python3 scripts/run_benchmarks.py
python3 scripts/analyze_results.py results/benchmark_raw.csv results/benchmark_summary.csv
python3 scripts/make_graphs.py results/benchmark_summary.csv results/graphs
```

From Windows PowerShell on this machine, use WSL:

```powershell
wsl
cd ~/code/OSFINAL
THREADS=12 TRIALS=50 DNS_SIZES=50,200,500 python3 scripts/run_benchmarks.py
python3 scripts/analyze_results.py results/benchmark_raw.csv results/benchmark_summary.csv
python3 scripts/make_graphs.py results/benchmark_summary.csv results/graphs
```

The Obsidian paper embeds the generated SVG graphs from `results/graphs/`.

The DNS inputs are static checked-in files. The simple submission files live in `data/dns/names_50.txt`, `data/dns/names_200.txt`, and `data/dns/names_500.txt`. The actual benchmark uses the fixed per-trial/per-language files in `data/dns/trials/`, which keeps hostnames unique across the benchmark run and reduces repeated-name cache effects.

## Notes For The Paper

Keep the conclusion tied to evidence. Useful things to discuss:

- Whether C or Rust was faster for each workload
- Whether differences were larger than the confidence interval
- Whether the workload was CPU-bound or affected by OS/network behavior
- The cost of thread creation, synchronization, memory access patterns, DNS caching, and resolver latency
- What you did to reduce noise, such as using the same machine, same thread count, same workload sizes, and many repeated trials
