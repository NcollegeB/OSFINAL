#!/usr/bin/env python3
import csv
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
RAW_CSV = RESULTS_DIR / "benchmark_raw.csv"

THREADS = int(os.environ.get("THREADS", "4"))
TRIALS = int(os.environ.get("TRIALS", "30"))
MONTE_POINTS = [int(x) for x in os.environ.get("MONTE_POINTS", "1000000,5000000,10000000").split(",")]
MATRIX_SIZES = [int(x) for x in os.environ.get("MATRIX_SIZES", "128,256,512").split(",")]
DNS_SIZES = [int(x) for x in os.environ.get("DNS_SIZES", "30,100,150").split(",")]


def run(command: list[str], cwd: Path | None = None) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def build() -> None:
    validate_dns_inputs()
    print("Building C benchmarks...")
    run(["make", "-C", str(ROOT / "c")])
    print("Building Rust benchmarks...")
    run(["cargo", "build", "--release", "--manifest-path", str(ROOT / "rust" / "Cargo.toml")])


def validate_dns_inputs() -> None:
    seen_across_files: dict[str, Path] = {}

    for size in DNS_SIZES:
        input_file = ROOT / "data" / "dns" / f"names_{size}.txt"
        if not input_file.exists():
            raise SystemExit(f"Missing DNS input file: {input_file}")

        names = [
            line.strip()
            for line in input_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if len(names) != size:
            raise SystemExit(
                f"{input_file} contains {len(names)} hostnames, expected {size}"
            )

        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise SystemExit(
                f"{input_file} contains duplicate hostnames: {', '.join(duplicates)}"
            )

        for name in names:
            if name in seen_across_files:
                raise SystemExit(
                    f"Hostname {name} appears in both {seen_across_files[name]} and {input_file}"
                )
            seen_across_files[name] = input_file


def parse_result(line: str) -> dict[str, str]:
    language, algorithm, threads, workload, elapsed_ms, extra = line.split(",", maxsplit=5)
    return {
        "language": language,
        "algorithm": algorithm,
        "threads": threads,
        "workload": workload,
        "elapsed_ms": elapsed_ms,
        "extra": extra,
    }


def commands() -> list[tuple[str, str, int, list[str]]]:
    c_build = ROOT / "c" / "build"
    rust_build = ROOT / "rust" / "target" / "release"
    cases: list[tuple[str, str, int, list[str]]] = []

    for points in MONTE_POINTS:
        cases.append(("c", "monte_carlo", points, [str(c_build / "monte_carlo_c"), str(THREADS), str(points)]))
        cases.append(("rust", "monte_carlo", points, [str(rust_build / "monte_carlo"), str(THREADS), str(points)]))

    for size in MATRIX_SIZES:
        cases.append(("c", "matrix_mul", size, [str(c_build / "matrix_mul_c"), str(THREADS), str(size)]))
        cases.append(("rust", "matrix_mul", size, [str(rust_build / "matrix_mul"), str(THREADS), str(size)]))

    for size in DNS_SIZES:
        input_file = ROOT / "data" / "dns" / f"names_{size}.txt"
        cases.append(("c", "dns_lookup", size, [str(c_build / "dns_lookup_c"), str(THREADS), str(input_file)]))
        cases.append(("rust", "dns_lookup", size, [str(rust_build / "dns_lookup"), str(THREADS), str(input_file)]))

    return cases


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    build()

    fieldnames = [
        "trial",
        "language",
        "algorithm",
        "threads",
        "workload",
        "elapsed_ms",
        "extra",
    ]

    with RAW_CSV.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for trial in range(1, TRIALS + 1):
            print(f"Trial {trial}/{TRIALS}")
            for _language, _algorithm, _workload, command in commands():
                line = run(command)
                row = parse_result(line)
                row["trial"] = trial
                writer.writerow(row)
                file.flush()

    print(f"Wrote {RAW_CSV}")


if __name__ == "__main__":
    main()
