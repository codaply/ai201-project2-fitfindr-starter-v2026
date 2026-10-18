#!/usr/bin/env python3
"""
Run every scenario five times with caching disabled.

Commands:
    python run_eval.py --label before
    python run_eval.py --label after

Records sessions, traces, crashes, and elapsed time.
PASS/FAIL and verdicts are filled in manually against criteria.md.
"""

import argparse
import datetime as dt
import sys
import time
import traceback

import config
import scenarios as scenario_module


def run_once(scenario, use_trace=True):
    """Run one scenario and capture its results and elapsed time."""
    from agent import run_agent
    from utils.data_loader import (
        get_example_wardrobe,
        get_empty_wardrobe,
    )
    import trace as trace_module

    wardrobe = (
        get_empty_wardrobe()
        if scenario["wardrobe"] == "empty"
        else get_example_wardrobe()
    )

    if use_trace:
        trace_module.start_trace()

    record = {
        "error": None,
        "session": None,
        "trace": "",
        "crashed": None,
        "elapsed_seconds": None,
    }

    # Includes parsing, MCP startup, tool calls, and any pacing or retries
    # occurring inside run_agent().
    started = time.perf_counter()

    try:
        record["session"] = run_agent(scenario["query"], wardrobe)
    except Exception as exc:
        record["crashed"] = f"{type(exc).__name__}: {exc}"
        record["traceback"] = traceback.format_exc()
    finally:
        record["elapsed_seconds"] = time.perf_counter() - started

    if use_trace:
        record["trace"] = trace_module.get_trace()

    return record


def main():
    parser = argparse.ArgumentParser(
        description="Run the scenarios and log the results."
    )
    parser.add_argument(
        "--tries",
        "--trials",
        type=int,
        default=5,
        dest="tries",
        help="tries per scenario (default 5)",
    )
    parser.add_argument(
        "--label",
        default="",
        help="a name for this run, e.g. before or after",
    )
    args = parser.parse_args()

    if args.tries < 1:
        parser.error("--tries must be at least 1")

    problems = scenario_module.validate()

    if problems:
        print("scenarios.py has problems:\n", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        sys.exit(1)

    if not scenario_module.SCENARIOS:
        print(
            "scenarios.py is empty. Add your five scenarios first.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.tries < 5:
        print(
            f"Warning: {args.tries} tries. "
            "Your criteria are written out of five.\n"
        )

    config.CACHE_ENABLED = False
    print("Cache is OFF for this run — that's deliberate.\n")

    rows = []

    for scenario in scenario_module.SCENARIOS:
        print(
            f"{scenario['name']} "
            f"({scenario['wardrobe']} wardrobe)"
        )
        print(f"  query: {scenario['query']}")

        tries = []

        for attempt in range(1, args.tries + 1):
            record = run_once(scenario)
            tries.append(record)

            elapsed = record["elapsed_seconds"]

            if record["crashed"]:
                print(
                    f"  try {attempt}: CRASHED — "
                    f"{record['crashed']} "
                    f"({elapsed:.6f}s)"
                )
            else:
                session = record["session"] or {}

                if session.get("error"):
                    print(
                        f"  try {attempt}: stopped early — "
                        f"{str(session['error'])[:60]} "
                        f"({elapsed:.6f}s)"
                    )
                else:
                    card = session.get("fit_card") or ""
                    print(
                        f"  try {attempt}: completed — "
                        f"fit card {len(card)} chars "
                        f"({elapsed:.6f}s)"
                    )

        rows.append({
            "scenario": scenario,
            "tries": tries,
        })
        print()

    write_report(rows, args)


def write_report(rows, args):
    """Write the raw evidence and an unscored run-log table."""
    config.RESULTS_DIR.mkdir(exist_ok=True)

    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    label = f"_{args.label}" if args.label else ""
    path = config.RESULTS_DIR / f"run_{stamp}{label}.md"

    n = args.tries
    headers = " | ".join(
        f"Try {i}" for i in range(1, n + 1)
    )
    divider = "|".join(["---"] * n)

    lines = [
        f"# Run log{f' — {args.label}' if args.label else ''}",
        "",
        "- Produced by: `run_eval.py::main`",
        "- Loop: `agent.py::run_agent` · tools: `tools.py`",
        f"- Tries per scenario: {n}, caching off",
        f"- Model: {config.MODEL}",
        f"- Temperature: {config.TEMPERATURE}",
        f"- When: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "- Timing: elapsed wall time around `run_agent()`, including "
        "MCP startup, tool calls, pacing, and retries.",
        "- Timing excludes Python startup, imports, and wardrobe loading.",
        "",
        "Fill in the Target column from `criteria.md`. Mark each try",
        "PASS or FAIL using the actual output, then count the passes",
        "against the original target to determine the verdict.",
        "",
        f"| Criterion | Target | {headers} | Verdict |",
        f"|---|---|{divider}|---|",
    ]

    for row in rows:
        scenario = row["scenario"]
        number = scenario.get("criterion")

        label_text = (
            f"{number}. {scenario['name']}"
            if number
            else (
                f"{scenario['name']} "
                "_(diagnostic — not one of your five)_"
            )
        )

        cells = " | ".join([" "] * n)
        lines.append(
            f"| {label_text} |  | {cells} |  |"
        )

    lines += [
        "",
        "> The Try and Verdict columns are blank on purpose.",
        "> Apply the original criteria without lowering their targets.",
        "> For criterion 5, a run must return a completed fit card",
        "> within 5.000000 seconds to pass this measured interval.",
        "> A crash or incomplete run fails criterion 5 regardless of speed.",
        "",
        "---",
        "",
        "## What actually happened",
        "",
        "Real outputs and traces follow for every try.",
        "",
    ]

    for row in rows:
        scenario = row["scenario"]

        lines += [
            f"### {scenario['name']}",
            "",
            f"- Criterion: {scenario.get('criterion')}",
            f"- Query: `{scenario['query']}`",
            f"- Wardrobe: {scenario['wardrobe']}",
            "",
        ]

        for i, record in enumerate(row["tries"], 1):
            lines += [
                f"**Try {i}**",
                "",
                f"- Elapsed seconds: {record['elapsed_seconds']:.6f}",
                "",
            ]

            if record["crashed"]:
                lines += [
                    "Crashed:",
                    "",
                    "```text",
                    record["crashed"],
                    "```",
                    "",
                    "Traceback:",
                    "",
                    "```text",
                    record.get("traceback", ""),
                    "```",
                    "",
                ]
            else:
                session = record["session"] or {}
                item = session.get("selected_item") or {}

                stopped = (
                    "yes — " + str(session["error"])
                    if session.get("error")
                    else "no"
                )

                selected = item.get("title", "(none)")
                if item:
                    selected += (
                        f" (${item.get('price')}, "
                        f"{item.get('platform')})"
                    )

                lines += [
                    f"- stopped early: {stopped}",
                    f"- selected_item ID: {item.get('id', '(none)')}",
                    f"- selected_item: {selected}",
                    "- search_results: "
                    f"{len(session.get('search_results') or [])}",
                    "",
                ]

                if session.get("outfit_suggestion"):
                    lines += [
                        "Outfit suggestion:",
                        "",
                        "```text",
                        str(session["outfit_suggestion"]),
                        "```",
                        "",
                    ]

                if session.get("fit_card"):
                    lines += [
                        "Fit card:",
                        "",
                        "```text",
                        str(session["fit_card"]),
                        "```",
                        "",
                    ]

            if record["trace"]:
                lines += [
                    "Trace:",
                    "",
                    "```text",
                    record["trace"],
                    "```",
                    "",
                ]

    path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    import generate

    print(f"Wrote {path.relative_to(config.ROOT)}")
    print(generate.usage())
    print(
        "\nCommit this report. "
        "It is the evidence the test actually happened."
    )

    has_trace = any(
        record["trace"]
        for row in rows
        for record in row["tries"]
    )

    if not has_trace:
        print(
            "\nNo trace was captured. Add trace.step() calls "
            "to agent.py before collecting the final evidence."
        )


if __name__ == "__main__":
    main()