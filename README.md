# OSFINAL: C vs Rust Thread Performance

## Project Question

How does the performance of threads in C compare to Rust for parallel workloads?

This project compares C `pthread` programs against Rust `std::thread` programs using the same thread count and increasing workload sizes. The workloads are:

- Monte Carlo estimation of pi
- Matrix multiplication
- DNS hostname resolution

## Folder Layout

- `c/`: C pthread implementations and Makefile
- `rust/`: Rust implementations using `std::thread`
- `scripts/`: benchmark runner, result analyzer, and graph generator
- `data/dns/`: static DNS hostname inputs, including fixed per-trial files
- `docs/`: final report PDF/Markdown, graph assets, Obsidian styling, and AI citation log
- `results/`: raw and summarized benchmark CSV results

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
python3 scripts/make_graphs.py results/benchmark_summary.csv docs/assets/graphs
```

For quick smoke tests:

```bash
THREADS=12 TRIALS=2 DNS_SIZES=50,200,500 python3 scripts/run_benchmarks.py
python3 scripts/analyze_results.py results/benchmark_raw.csv results/benchmark_summary.csv
python3 scripts/make_graphs.py results/benchmark_summary.csv docs/assets/graphs
```

From Windows PowerShell on this machine, use WSL:

```powershell
wsl
cd ~/code/OSFINAL
THREADS=12 TRIALS=50 DNS_SIZES=50,200,500 python3 scripts/run_benchmarks.py
python3 scripts/analyze_results.py results/benchmark_raw.csv results/benchmark_summary.csv
python3 scripts/make_graphs.py results/benchmark_summary.csv docs/assets/graphs
```

The final report is in `docs/final-report.md`, and the PDF export is `docs/final-report.pdf`. The Markdown report embeds the SVG graphs from `docs/assets/graphs/`.

The DNS inputs are static checked-in files. The simple submission files live in `data/dns/names_50.txt`, `data/dns/names_200.txt`, and `data/dns/names_500.txt`. The actual benchmark uses the fixed per-trial/per-language files in `data/dns/trials/`, which keeps hostnames unique across the benchmark run and reduces repeated-name cache effects.

To open the report cleanly in Obsidian, open `docs/` as the vault instead of opening the whole repository.

## Notes For The Paper

- Keep the conclusion tied to the measured means and confidence intervals.
- Mention that the experiment varies workload size, not thread count.
- Discuss DNS resolver/cache/network behavior as a possible source of noise.

## Submission Checklist

- `docs/final-report.pdf`: paper PDF for submission
- `docs/final-report.md`: editable Markdown copy of the paper
- `c/`, `rust/`, and `scripts/`: source code and scripts needed to rebuild and rerun the project
- `data/dns/`: static DNS input files used by the benchmark
- `results/benchmark_raw.csv` and `results/benchmark_summary.csv`: collected timing data and summarized statistics
- `docs/ai-citation-log.md`: supporting AI citation details

Do not submit compiled binaries or build output directories. They are ignored by `.gitignore` and can be regenerated from the source.
