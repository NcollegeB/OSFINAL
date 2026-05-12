#!/usr/bin/env python3
import csv
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
RAW_CSV = RESULTS_DIR / "benchmark_raw.csv"
DNS_DIR = ROOT / "data" / "dns"
DNS_TRIALS_DIR = DNS_DIR / "trials"

THREADS = int(os.environ.get("THREADS", "12"))
TRIALS = int(os.environ.get("TRIALS", "50"))
MONTE_POINTS = [int(x) for x in os.environ.get("MONTE_POINTS", "1000000,5000000,10000000").split(",")]
MATRIX_SIZES = [int(x) for x in os.environ.get("MATRIX_SIZES", "128,256,512").split(",")]
DNS_SIZES = [int(x) for x in os.environ.get("DNS_SIZES", "50,200,500").split(",")]
DNS_UNIQUE_PER_TRIAL = os.environ.get("DNS_UNIQUE_PER_TRIAL", "1") != "0"
COMMAND_TIMEOUT_SECONDS = int(os.environ.get("COMMAND_TIMEOUT_SECONDS", "120"))


def run(command: list[str], cwd: Path | None = None) -> str:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        joined = " ".join(command)
        raise SystemExit(
            f"Command timed out after {COMMAND_TIMEOUT_SECONDS} seconds: {joined}"
        ) from error
    return completed.stdout.strip()


def build() -> None:
    validate_dns_inputs()
    print("Building C benchmarks...")
    run(["make", "-C", str(ROOT / "c")])
    print("Building Rust benchmarks...")
    run(["cargo", "build", "--release", "--manifest-path", str(ROOT / "rust" / "Cargo.toml")])


def validate_dns_inputs() -> None:
    seen_across_files: dict[str, Path] = {}

    def validate_file(input_file: Path, size: int) -> None:
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

        unique_names = set(names)
        if len(unique_names) != len(names):
            duplicates = sorted(name for name in unique_names if names.count(name) > 1)
            raise SystemExit(
                f"{input_file} contains duplicate hostnames: {', '.join(duplicates)}"
            )

        for name in names:
            if name in seen_across_files:
                raise SystemExit(
                    f"Hostname {name} appears in both {seen_across_files[name]} and {input_file}"
                )
            seen_across_files[name] = input_file

    for size in DNS_SIZES:
        validate_file(DNS_DIR / f"names_{size}.txt", size)

    if DNS_UNIQUE_PER_TRIAL:
        for trial in range(1, TRIALS + 1):
            for language in ("c", "rust"):
                for size in DNS_SIZES:
                    validate_file(dns_input_file(language, size, trial), size)


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


def dns_input_file(language: str, size: int, trial: int) -> Path:
    if DNS_UNIQUE_PER_TRIAL:
        return DNS_TRIALS_DIR / f"trial_{trial:03d}" / f"{language}_names_{size}.txt"
    return DNS_DIR / f"names_{size}.txt"


def commands(trial: int) -> list[tuple[str, str, int, list[str]]]:
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
        c_input_file = dns_input_file("c", size, trial)
        rust_input_file = dns_input_file("rust", size, trial)
        cases.append(("c", "dns_lookup", size, [str(c_build / "dns_lookup_c"), str(THREADS), str(c_input_file)]))
        cases.append(("rust", "dns_lookup", size, [str(rust_build / "dns_lookup"), str(THREADS), str(rust_input_file)]))

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
            for _language, _algorithm, _workload, command in commands(trial):
                line = run(command)
                row = parse_result(line)
                row["trial"] = trial
                writer.writerow(row)
                file.flush()

    print(f"Wrote {RAW_CSV}")


if __name__ == "__main__":
    main()
