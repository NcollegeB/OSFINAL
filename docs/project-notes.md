# Project Notes

## Can I Use The Existing Threaded Implementation?

## Chosen Workloads

1. Monte Carlo pi estimation
   - CPU-bound and easy to split across threads.
   - Vary number of points.

2. Matrix multiplication
   - CPU-bound and memory/cache sensitive.
   - Vary matrix dimensions.

3. DNS hostname resolution
   - Approved-style workload, but noisier because it depends on resolver caching, network behavior, and OS DNS libraries.
   - Vary number of hostnames.

## Experimental Controls

- Same physical machine or VM for every run.
- Same OS image and compiler optimization level.
- Same number of threads for C and Rust.
- Same workload sizes.
- At least 30 trials per case if time allows.
- Record CPU model, core count, memory, OS, compiler versions, and Rust version.

Useful commands:

```bash
lscpu
free -h
uname -a
gcc --version
rustc --version
cargo --version
```

