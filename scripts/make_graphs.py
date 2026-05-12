#!/usr/bin/env python3
import csv
import math
import sys
from pathlib import Path


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
COLORS = {"c": "#1f77b4", "rust": "#d95f02"}


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def workload_label(algorithm: str, value: int) -> str:
    if algorithm == "monte_carlo" and value >= 1_000_000:
        return f"{value // 1_000_000}M"
    if algorithm == "matrix_mul":
        return f"{value}x{value}"
    return str(value)


def nice_y_max(value: float) -> float:
    if value <= 0:
        return 1.0
    exponent = math.floor(math.log10(value))
    fraction = value / (10 ** exponent)
    if fraction <= 2:
        nice = 2
    elif fraction <= 5:
        nice = 5
    else:
        nice = 10
    return nice * (10 ** exponent)


def fmt(value: float) -> str:
    if value >= 100:
        return f"{value:.0f}"
    if value >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}"


def svg_text(x: float, y: float, text: str, size: int = 13, anchor: str = "middle", weight: str = "400") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" '
        f'fill="#222">{text}</text>'
    )


def make_chart(algorithm: str, rows: list[dict[str, str]], output: Path) -> None:
    width = 920
    height = 520
    left = 88
    right = 36
    top = 70
    bottom = 92
    plot_w = width - left - right
    plot_h = height - top - bottom

    by_language: dict[str, list[dict[str, str]]] = {"c": [], "rust": []}
    for row in rows:
        by_language[row["language"]].append(row)
    for language in by_language:
        by_language[language].sort(key=lambda row: int(row["workload"]))

    workloads = [int(row["workload"]) for row in by_language["c"]]
    y_max = nice_y_max(
        max(
            float(row["mean_ms"]) + float(row["ci95_half_width_ms"])
            for language_rows in by_language.values()
            for row in language_rows
        )
        * 1.12
    )

    def x_for(index: int) -> float:
        if len(workloads) == 1:
            return left + plot_w / 2
        return left + (plot_w * index / (len(workloads) - 1))

    def y_for(value: float) -> float:
        return top + plot_h - (value / y_max * plot_h)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        svg_text(width / 2, 34, f"{ALGORITHM_NAMES.get(algorithm, algorithm)} Mean Runtime", 22, weight="700"),
        svg_text(width / 2, 56, "C and Rust lines include 95% confidence interval error bars", 13),
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#222" stroke-width="1.2"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#222" stroke-width="1.2"/>',
    ]

    for tick in range(0, 6):
        value = y_max * tick / 5
        y = y_for(value)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#e5e5e5" stroke-width="1"/>')
        parts.append(svg_text(left - 12, y + 4, fmt(value), 12, anchor="end"))

    for index, workload in enumerate(workloads):
        x = x_for(index)
        parts.append(f'<line x1="{x:.1f}" y1="{top + plot_h}" x2="{x:.1f}" y2="{top + plot_h + 6}" stroke="#222" stroke-width="1"/>')
        parts.append(svg_text(x, top + plot_h + 26, workload_label(algorithm, workload), 13))

    parts.append(svg_text(left + plot_w / 2, height - 24, WORKLOAD_NAMES.get(algorithm, "Workload"), 14, weight="700"))
    parts.append(
        f'<text x="22" y="{top + plot_h / 2:.1f}" transform="rotate(-90 22 {top + plot_h / 2:.1f})" '
        'font-family="Arial, sans-serif" font-size="14" font-weight="700" text-anchor="middle" fill="#222">Mean runtime (ms)</text>'
    )

    for language, label in (("c", "C"), ("rust", "Rust")):
        points = []
        color = COLORS[language]
        for index, row in enumerate(by_language[language]):
            x = x_for(index)
            mean = float(row["mean_ms"])
            ci = float(row["ci95_half_width_ms"])
            y = y_for(mean)
            y_low = y_for(mean - ci)
            y_high = y_for(mean + ci)
            points.append(f"{x:.1f},{y:.1f}")
            parts.append(f'<line x1="{x:.1f}" y1="{y_high:.1f}" x2="{x:.1f}" y2="{y_low:.1f}" stroke="{color}" stroke-width="1.5"/>')
            parts.append(f'<line x1="{x - 7:.1f}" y1="{y_high:.1f}" x2="{x + 7:.1f}" y2="{y_high:.1f}" stroke="{color}" stroke-width="1.5"/>')
            parts.append(f'<line x1="{x - 7:.1f}" y1="{y_low:.1f}" x2="{x + 7:.1f}" y2="{y_low:.1f}" stroke="{color}" stroke-width="1.5"/>')
        parts.append(f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{" ".join(points)}"/>')
        for index, row in enumerate(by_language[language]):
            x = x_for(index)
            y = y_for(float(row["mean_ms"]))
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}" stroke="white" stroke-width="1.5"/>')

        legend_x = left + 30 + (0 if language == "c" else 100)
        legend_y = top - 16
        parts.append(f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x + 28}" y2="{legend_y}" stroke="{color}" stroke-width="3"/>')
        parts.append(f'<circle cx="{legend_x + 14}" cy="{legend_y}" r="4.5" fill="{color}"/>')
        parts.append(svg_text(legend_x + 38, legend_y + 4, label, 13, anchor="start", weight="700"))

    parts.append("</svg>")
    output.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: make_graphs.py <summary_csv> <output_dir>")

    summary_csv = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = load_rows(summary_csv)
    algorithms = sorted({row["algorithm"] for row in rows})
    for algorithm in algorithms:
        algorithm_rows = [row for row in rows if row["algorithm"] == algorithm]
        output = output_dir / f"{algorithm}.svg"
        make_chart(algorithm, algorithm_rows, output)
        print(f"Wrote {output}")


if __name__ == "__main__":
    main()
