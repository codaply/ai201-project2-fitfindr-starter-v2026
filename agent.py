"""The FitFindr planning loop."""

import re

import trace
from generate import ModelUnavailable
from mcp_client import call_tool
from tools import suggest_outfit, create_fit_card


def new_session(query: str, wardrobe: dict) -> dict:
    """Create session state for one run."""
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


def run_agent(query: str, wardrobe: dict) -> dict:
    """Run the tools in order, stopping when a branch requires it."""
    session = new_session(query, wardrobe)
    trace.start_trace()

    price_pattern = (
        r"\b(?:under|below|max(?:imum)?(?:\s+price)?|up\s+to)"
        r"\s*\$?\s*(\d+(?:\.\d+)?)\b"
    )
    size_pattern = r"\bsize\s+([a-z0-9]+(?:[/-][a-z0-9]+)*)\b"

    price_match = re.search(
        price_pattern, query, flags=re.IGNORECASE
    )
    size_match = re.search(
        size_pattern, query, flags=re.IGNORECASE
    )

    description = re.sub(
        price_pattern, " ", query, flags=re.IGNORECASE
    )
    description = re.sub(
        size_pattern, " ", description, flags=re.IGNORECASE
    )
    description = re.sub(
        r"^\s*(?:looking\s+for|find\s+me|find|show\s+me)\s+",
        "",
        description,
        flags=re.IGNORECASE,
    )
    description = re.sub(
        r"\s+", " ", description.replace(",", " ")
    ).strip()

    session["parsed"] = {
        "description": description,
        "size": size_match.group(1) if size_match else None,
        "max_price": float(price_match.group(1)) if price_match else None,
    }

    trace.step(
        "parse_query",
        inputs=query,
        returned=str(session["parsed"]),
        note="Extract description, size, and maximum price.",
    )

    stage = "search"
    count = 0

    while True:
        count += 1
        trace.check_iterations(count)

        if stage == "search":
            session["search_results"] = call_tool(
                "search_listings",
                {
                    "description": session["parsed"]["description"],
                    "size": session["parsed"]["size"],
                    "max_price": session["parsed"]["max_price"],
                },
            )

            trace.step(
                "search_listings (via MCP)",
                inputs=str(session["parsed"]),
                returned=session["search_results"],
                note=(
                    "No matches; stop before suggest_outfit."
                    if not session["search_results"]
                    else "Matches found; choose the first ranked result."
                ),
            )

            if not session["search_results"]:
                session["error"] = (
                    "No listings matched your request. Try broader clothing "
                    "keywords, a different size, or a higher maximum price."
                )
                return session

            session["selected_item"] = session["search_results"][0]

            trace.step(
                "select_item",
                returned=session["selected_item"],
                note=(
                    f"Saved item ID {session['selected_item']['id']} "
                    "in session for the remaining tools."
                ),
            )

            stage = "outfit"

        elif stage == "outfit":
            outfit_inputs = {
                "new_item": session["selected_item"],
                "wardrobe": session["wardrobe"],
            }

            trace.step(
                "suggest_outfit — call",
                inputs=str(outfit_inputs),
                note=(
                    f"Session item ID: {session['selected_item']['id']}; "
                    f"tool input item ID: {outfit_inputs['new_item']['id']}. "
                    "Use general styling advice if the wardrobe is empty."
                ),
            )

            try:
                session["outfit_suggestion"] = suggest_outfit(
                    **outfit_inputs
                )
            except ModelUnavailable as exc:
                session["error"] = str(exc)

                trace.step(
                    "suggest_outfit — error",
                    returned=session["error"],
                    note="Stop before create_fit_card.",
                )
                return session

            trace.step(
                "suggest_outfit — result",
                returned=session["outfit_suggestion"],
                note="Outfit advice received; proceed to create_fit_card.",
            )

            stage = "fit_card"

        elif stage == "fit_card":
            fit_card_inputs = {
                "outfit": session["outfit_suggestion"],
                "new_item": session["selected_item"],
            }

            trace.step(
                "create_fit_card — call",
                inputs=str(fit_card_inputs),
                note=(
                    f"Use saved item ID {session['selected_item']['id']} "
                    "and the outfit advice returned by suggest_outfit."
                ),
            )

            try:
                session["fit_card"] = create_fit_card(
                    **fit_card_inputs
                )
            except ModelUnavailable as exc:
                session["error"] = str(exc)

                trace.step(
                    "create_fit_card — error",
                    returned=session["error"],
                    note="Stop and return the model error message.",
                )
                return session

            trace.step(
                "create_fit_card — result",
                returned=session["fit_card"],
                note="Fit card received; run complete.",
            )

            return session


def _show(session: dict) -> None:
    """Print a session when this file is run directly."""
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(
            f"  fit_card is {session['fit_card']!r} "
            "— it should still be None here"
        )
        return

    item = session["selected_item"] or {}

    print(
        f"  found:    {item.get('title')} "
        f"— ${item.get('price')} on {item.get('platform')}"
    )
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )