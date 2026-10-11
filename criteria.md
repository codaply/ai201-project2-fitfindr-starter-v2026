# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
An occasional AI-service failure during either model call can interrupt the workflow and leave the run incomplete, even when search finds a matching listing.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
The agent stops after the first tool call returns an empty list, triggering a stop rule in the Python code logic.

---

## 3. Something about state

In 5 of 5 matching-query runs, the ID in session["selected_item"] matches the ID of the item received by suggest_outfit.

**Why this target:**
If the outfit tool receives the incorrect item, it could generate inaccurate outfit advice and affect the final caption. I expect 5 of 5 because the Python code passes the saved item directly to the next too

---

## 4. Fit Card Accuracy
In 5 of 5 generated fit cards, the caption includes both the price and platform, and both match the selected listing.


**Why this target:**
I chose 5 of 5 because incorrect price or platform information makes the fit card unreliable.


---

## 5. 5 second run time

In at least 4 of 5 uncached matching-query runs, the agent returns a completed fit card within five seconds of submitting the query, including any waiting.

**Why this target:**
Anything longer than five seconds feels slow to me. I chose 4 of 5 to allow one slower run due to network latency or AI-service delays.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
