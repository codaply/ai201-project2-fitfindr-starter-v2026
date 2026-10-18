"""Evaluate the complete FitFindr command, including startup and waiting."""

import argparse
import datetime as dt
import os
from pathlib import Path
import subprocess
import sys
import time

from scenarios import SCENARIOS, validate


ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    args = parser.parse_args()

    problems = validate()
    numbers = [scenario.get("criterion") for scenario in SCENARIOS]

    if sorted(number for number in numbers if number is not None) != [
        1, 2, 3, 4, 5
    ]:
        problems.append("Use exactly one scenario for each criterion 1–5.")

    if len(SCENARIOS) != 5:
        problems.append("This evaluation requires exactly five scenarios.")

    if problems:
        for problem in problems:
            print(problem)
        sys.exit(1)

    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)

    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    path = results_dir / f"cli_{stamp}_{args.label}.md"

    environment = os.environ.copy()
    environment["AI201_CACHE"] = "0"
    environment["PYTHONIOENCODING"] = "utf-8"

    lines = [
        f"# Command evaluation — {args.label}",
        "",
        "- Five trials per criterion; caching disabled.",
        "- Timer starts before launching Python and ends after the command exits.",
        "- Includes startup, loading, MCP, model requests, waiting, and output.",
        "- Each trial is a fresh process, matching a separately submitted command.",
        "- In-process pacing history resets between commands; provider limits",
        "  still apply. This differs from the earlier in-process evaluator.",
        "- Score these results manually against the unchanged criteria.",
        "",
    ]

    # Save incrementally so completed trials survive an interrupted evaluation.
    path.write_text("\n".join(lines), encoding="utf-8")

    for scenario in SCENARIOS:
        number = scenario["criterion"]

        lines.extend([
            f"## Criterion {number}: {scenario['name']}",
            "",
            f"- Query: `{scenario['query']}`",
            f"- Wardrobe: {scenario['wardrobe']}",
            "",
        ])

        for attempt in range(1, 6):
            command = [
                sys.executable,
                str(ROOT / "app.py"),
                "ask",
                scenario["query"],
                "--trace",
            ]

            if scenario["wardrobe"] == "empty":
                command.append("--empty-wardrobe")

            print(
                f"Criterion {number}, try {attempt}/5 — running",
                flush=True,
            )

            started = time.perf_counter()
            completed = subprocess.run(
                command,
                cwd=ROOT,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            elapsed = time.perf_counter() - started

            lines.extend([
                f"### Try {attempt}",
                "",
                f"- Elapsed seconds: {elapsed:.6f}",
                f"- Exit code: {completed.returncode}",
                "- Output from `app.py`, `agent.py::run_agent`,",
                "  `tools.py`, and the model adapter:",
                "",
                "```text",
                completed.stdout.rstrip(),
                "```",
                "",
            ])

            path.write_text("\n".join(lines), encoding="utf-8")

            print(
                f"Finished in {elapsed:.6f}s; "
                f"exit code {completed.returncode}",
                flush=True,
            )

    print(f"\nSaved: {path.relative_to(ROOT)}")
    print("Check the full outputs before assigning PASS or FAIL.")


if __name__ == "__main__":
    main()
