"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import suggest_outfit, create_fit_card
from mcp_client import call_tool
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
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


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)

    price_pattern = (
        r"\b(?:under|below|max(?:imum)?(?:\s+price)?|up\s+to)"
        r"\s*\$?\s*(\d+(?:\.\d+)?)\b"
    )
    size_pattern = (
        r"\bsize\s+([a-z0-9]+(?:[/-][a-z0-9]+)*)\b"
    )

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

            if not session["search_results"]:
                session["error"] = (
                    "No listings matched your request. Try broader clothing "
                    "keywords, a different size, or a higher maximum price."
                )
                return session

            session["selected_item"] = session["search_results"][0]
            stage = "outfit"

        elif stage == "outfit":
            session["outfit_suggestion"] = suggest_outfit(
                new_item=session["selected_item"],
                wardrobe=session["wardrobe"],
            )
            stage = "fit_card"

        elif stage == "fit_card":
            session["fit_card"] = create_fit_card(
                outfit=session["outfit_suggestion"],
                new_item=session["selected_item"],
            )
            return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
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