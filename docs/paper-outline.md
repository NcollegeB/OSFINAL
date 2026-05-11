# Paper Outline

## Approved Question

How does the performance of threads in C compare to Rust?

This experiment compares C pthreads with Rust standard-library threads across Monte Carlo pi estimation, matrix multiplication, and DNS hostname resolution.

## Experimental Setup

Record:

- CPU model and number of cores/threads
- Memory size
- Operating system and whether it is native, WSL, or a VM
- Compiler versions: `gcc --version`, `rustc --version`, `cargo --version`
- Thread count used in all runs

Discuss possible setup artifacts:

- VM scheduling overhead
- background processes
- CPU frequency scaling
- DNS cache and network variability
- memory/cache behavior for matrix multiplication

## Testing Procedure

Describe:

- How each program was compiled
- The exact command used to run benchmarks
- The workload sizes used for each algorithm
- The number of trials per case
- The timing source: `clock_gettime(CLOCK_MONOTONIC)` in C and `std::time::Instant` in Rust
- The fact that setup/allocation is mostly outside the timed region where practical

## Test Results

Include tables from `results/benchmark_summary.csv`:

- mean execution time
- standard deviation
- min and max
- 95% confidence interval half-width
- margin of error percent

Add charts if possible:

- Mean execution time by workload and language for each algorithm
- Error bars using the 95% confidence interval

## Conclusion / Answer

Answer the question directly:

- Which language was faster for each workload?
- Were the differences large enough to matter given the margin of error?
- Did CPU-bound workloads behave differently from DNS?
- What OS concepts explain the results?

## Learning Outcome

Possible points:

- Threading APIs differ in safety and ergonomics.
- Fair performance comparisons require repeated trials and controlled variables.
- DNS is a useful but noisy workload because it includes OS and network effects.
- Matrix multiplication reveals memory access and cache effects.
- Rust can provide safety while still using native OS threads.

