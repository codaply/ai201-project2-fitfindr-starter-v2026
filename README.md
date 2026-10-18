# FitFindr

Read [RUNNING.md](RUNNING.md) for setup instructions, commands, and troubleshooting.

## What This Does

FitFindr helps users find clothing by description, size, and budget. It searches local listings, selects the highest-ranked match, and suggests outfits using the user's wardrobe. It then writes a short caption about the selected item and outfit. If no listings match, it stops and suggests what the user could change.

## Tool Inventory

### search_listings(description, size, max_price)

- **Purpose:** Searches local listings and ranks matches by keyword overlap across title, description, category, and style tags.
- **Inputs:** `description` (`str`), `size` (`str | None`, default `None`), `max_price` (`float | None`, default `None`). `None` skips the corresponding filter. Size matching is case-insensitive and accepts slash-separated labels: `M` matches `S/M`, but `S` does not match `US 9` and `L` does not match `XL`. The price ceiling is inclusive.
- **Output:** A list of complete listing dictionaries, highest keyword score first, limited to `config.SEARCH_RESULT_LIMIT`. Fields include `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.
- **Empty case:** Returns an empty list (`[]`) when no listings match or the description contains no keywords.

### suggest_outfit(new_item, wardrobe)

- **Purpose:** Suggests one or two outfits using the selected item and the user's wardrobe.
- **Inputs:** `new_item` (`dict` containing the selected listing), `wardrobe` (`dict` containing an `items` list).
- **Output:** A non-empty string with outfit suggestions naming pieces from the provided wardrobe.
- **Empty case:** When the wardrobe's `items` list is empty, asks the model for general styling advice without claiming the user owns the suggested pieces. If the model returns blank text, raises `ValueError`.

### create_fit_card(outfit, new_item)

- **Purpose:** Writes a short, postable caption about the selected item and outfit.
- **Inputs:** `outfit` (`str` returned by `suggest_outfit`), `new_item` (`dict` containing the selected listing).
- **Output:** A string requested to contain two to four sentences, mentioning the item, its price, and its platform once each and describing the outfit's vibe. These content requirements are checked through evaluation rather than enforced by a validator.
- **Empty case:** If `outfit` is empty or whitespace-only, returns a descriptive message without calling the model. If the model returns blank caption text, raises `ValueError`.

## Planning Loop

**Branch rule:** If `search_listings` returns an empty list, store a message in `session["error"]` suggesting broader keywords, a different size, or a higher maximum price, then stop before calling `suggest_outfit`. Otherwise, store the first result in `session["selected_item"]`, call `suggest_outfit`, and then call `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regular expressions extract an optional size and maximum price. The parser removes those phrases, leading phrases such as "looking for," and extra spaces from the search description. It supports the documented patterns rather than every possible natural-language request.

**What moves through the session:** The agent stores the parsed request in `parsed`, the returned listings in `search_results`, the chosen listing in `selected_item`, the outfit advice in `outfit_suggestion`, and the caption in `fit_card`. Each subsequent tool reads its inputs from these saved fields. The session also retains the original query, wardrobe, and error field.

The loop uses search, outfit, and fit-card stages. It calls `trace.check_iterations(count)` on each iteration to enforce the configured iteration limit.

## Sample Run

The outfit outputs below have been cleaned for readability by removing non-rendering asterisks and replacing asterisk bullets with hyphens. Their wording is unchanged.

### Setup

- Python version: 3.13.15.
- `python test.py` passed.
- Before implementation, the starter reported that the planning loop was not built and made 0 model calls.

### Full Agent Run

The following command runs both example queries through `agent.py::run_agent`.

Command:

```bash
python agent.py
```

Output:

```text
=== A query the data can match ===
  found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop
  outfit:   Here are two practical outfit suggestions featuring your Y2K Butterfly Print Baby Tee and pieces from your wardrobe:

Outfit 1: Y2K Streetwear Contrast
-   Selected Item: Y2K Baby Tee — Butterfly Print
-   Wardrobe Pieces Used:
    -   Baggy straight-leg jeans, dark wash (w_001)
    -   Vintage black denim jacket (w_006)
    -   Chunky white sneakers (w_007)
    -   Black crossbody bag (w_010)
-   Why it works: Pairing the fitted, cropped silhouette of the baby tee with high-waisted baggy jeans creates a balanced Y2K streetwear proportion. Layering the slightly cropped black denim jacket adds edge, while the chunky white sneakers and crossbody bag tie the casual, everyday look together.

Outfit 2: Casual Earth-Tone Mix
-   Selected Item: Y2K Baby Tee — Butterfly Print
-   Wardrobe Pieces Used:
    -   Wide-leg khaki trousers (w_002)
    -   Brown leather belt (w_009)
    -   Chunky white sneakers (w_007)
-   Why it works: The pink and purple tones in the butterfly graphic pop against neutral bottoms. Tucking the baby tee into the wide-leg khaki trousers and accessorizing with the brown leather belt pulls the outfit together for an easy, slightly retro daytime aesthetic, finished off with comfortable white sneakers.
  fit card: Scored this Y2K butterfly print baby tee on Depop for just $18, and it brings the ultimate early 2000s streetwear energy. I'm pairing the fitted crop with baggy dark wash denim, chunky white sneakers, and a black denim jacket for a balanced, edgy vibe.

=== A query it can't ===
  stopped: No listings matched your request. Try broader clothing keywords, a different size, or a higher maximum price.
  fit_card is None — it should still be None here

The second one should stop before the fit card. If both paths look the same,
the branch isn't doing anything yet.
```

### Tool 1: search_listings

Command:

```bash
python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
```

Output:

```text
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}]
```

All six results were within the budget. Some were not graphic tees because keyword overlap includes incidental mentions in descriptions.

### Tool 2: suggest_outfit

Command:

```bash
python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
```

Output:

```text
Here are two outfit suggestions incorporating the selected Vintage Levi's 501 Jeans and pieces from your wardrobe:

### Outfit 1: Casual Streetwear
- Selected Item: Vintage Levi's 501 Jeans — Medium Wash
- Wardrobe Pieces Used:
  - White ribbed tank top (`w_003`)
  - Black cropped zip hoodie (`w_005`)
  - Chunky white sneakers (`w_007`)
  - Black crossbody bag (`w_010`)

Look Details: Pair the medium wash 501s with the fitted white tank top as a base. Layer the black cropped zip hoodie on top for a balanced silhouette between the relaxed jeans and the cropped layer. Finish the look with chunky white sneakers and the black crossbody bag for an effortless, everyday streetwear vibe.

---

### Outfit 2: Vintage Layered Denim
- Selected Item: Vintage Levi's 501 Jeans — Medium Wash
- Wardrobe Pieces Used:
  - White ribbed tank top (`w_003`)
  - Vintage black denim jacket (`w_006`)
  - Black combat boots (`w_008`)
  - Brown leather belt (`w_009`)

Look Details: Tuck the white ribbed tank into the jeans and cinch the waist with the brown leather belt. Add the slightly cropped vintage black denim jacket for a denim-on-denim contrast against the blue wash. Complete the outfit with the black combat boots to lean into a classic, grunge-inflected aesthetic.
```

### Tool 3: create_fit_card

Command:

```bash
python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
```

Output:

```text
Nothing beats the effortless, worn-in street style of these Vintage Levi's 501 Jeans. I paired them with crisp white sneakers for the ultimate laid-back, classic denim vibe. Scoring this exact pair on Depop for just $38.00 was an absolute win.
```

### Empty-Case Checks

No matching listings:

```bash
python -c "from tools import search_listings; print(search_listings('zzzznonexistentitem'))"
```

```text
[]
```

Whitespace-only outfit advice:

```bash
python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('   ', load_listings()[0]))"
```

```text
Cannot create a fit card because outfit advice is missing. Generate an outfit suggestion first.
```

Empty wardrobe:

```bash
python -c "from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_empty_wardrobe()))"
```

```text
Here are two versatile outfit ideas styled around vintage medium-wash Levi's 501 jeans:

1. Casual Everyday Streetwear
-   Top: A relaxed-fit, heavyweight white crewneck t-shirt or a vintage grey heather hoodie.
-   Footwear: Classic retro sneakers like Nike Killshots, Adidas Sambas, or New Balance 550s.
-   Accessories: A simple black leather belt and a canvas tote bag.
-   Why it works: This is a timeless, effortless combination that leans into the classic Americana and streetwear heritage of the 501 fit.

2. Elevated Smart-Casual
-   Top: A crisp, oversized button-down shirt in light blue or classic white, worn either tucked in or open over a fitted white tank top.
-   Outerwear (Optional): An unstructured black or camel blazer to add a touch of polish.
-   Footwear: Black leather loafers or pointed-toe ankle boots.
-   Accessories: A minimalist silver or gold wristwatch and a structured leather shoulder bag.
-   Why it works: Pairing structured, tailored pieces with vintage denim creates a high-low contrast that feels modern and chic.
```

### Session Handoff Check

This check wrapped the real outfit tool to record the item it received.

Command:

```bash
python - <<'PY'
from unittest.mock import patch
import agent
from utils.data_loader import get_example_wardrobe

with patch(
    "agent.suggest_outfit",
    wraps=agent.suggest_outfit,
) as outfit_tool:
    session = agent.run_agent(
        "vintage graphic tee under $30, size M",
        get_example_wardrobe(),
    )

    saved_id = session["selected_item"]["id"]
    received_id = outfit_tool.call_args.kwargs["new_item"]["id"]

    print("Saved item ID:", saved_id)
    print("Received item ID:", received_id)
    print("Handoff matches:", saved_id == received_id)
PY
```

Output:

```text
Saved item ID: lst_002
Received item ID: lst_002
Handoff matches: True
```

### Caption Variation Check

I ran the following command three times with caching disabled for each command:

```bash
AI201_CACHE=0 python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
```

Run 1:

```text
Nothing beats the effortless streetwear vibe of these Vintage Levi's 501 Jeans paired with crisp white sneakers. I found this classic medium wash pair on Depop for just $38.0.
```

Run 2:

```text
Nothing beats the effortless streetwear vibe of these Vintage Levi's 501 Jeans paired with crisp white sneakers. I scored this classic medium-wash pair on Depop for just $38.00.
```

Run 3:

```text
Nothing beats the effortless streetwear vibe of these Vintage Levi's 501 Jeans paired with crisp white sneakers. I found this classic medium wash pair on Depop for just $38.0
```

The three fresh requests produced two similar caption wordings, with punctuation also differing. Fresh model responses can repeat wording even with temperature set to 0.9.

These are development checks, not the five-trial acceptance evaluation for Unit 4.

## How I Used AI

### Moment 1: Implementing the Tools

- **What I asked for:** I provided the starter tool template and model adapter and asked ChatGPT to implement the required sections while preserving the template.
- **What came back:** Implementations for keyword-ranked search, outfit suggestions, and caption generation. The search used complete size labels instead of substring matching and returned an empty list when no listings matched.
- **What I changed:** I added the required imports and replaced the placeholder function bodies in `tools.py`. I then ran each tool separately and checked its normal and empty-case outputs.

### Moment 2: Investigating Repeated Captions

- **What I asked for:** I shared repeated caption outputs and the configuration to understand why the wording stayed the same.
- **What came back:** ChatGPT explained that caching was enabled by default and showed how to disable it for an individual terminal command using `AI201_CACHE=0`.
- **What I changed:** I reran the caption tool three times with caching disabled without changing `config.py`. The outputs showed some variation, but also repeated wording. I recorded that result instead of assuming every fresh response would be different.

## Unit 4: MCP and Failure Tests


I exposed only `search_listings` through FastMCP in `mcp_server.py`. Its typed inputs are `description: str`, `size: str | None`, and `max_price: float | None`. The description documents dollars, the inclusive price ceiling, size matching, ranked results, and the empty-list case. `agent.py::run_agent` now uses `mcp_client.call_tool`; the other two tools remain direct calls. The wrapper delegates to the existing search implementation.

`python mcp_client.py` listed the registered tool and its expected input types. The normal agent query still selected `lst_002`, the $18 Depop butterfly tee, and returned outfit advice and a fit card. Those initial model responses were cached, so that check demonstrated wiring rather than fresh model behavior.

I completed the required features without adding stretch features.

### Empty search

Command:

```bash
python app.py ask 'zzzxxyyqq'
```

Actual output before trace instrumentation:

```text
No listings matched your request. Try broader clothing keywords, a different size, or a higher maximum price.

0 model calls this session
```

The existing empty-search branch supplied actionable advice. The repeated evaluation traces subsequently confirmed that `suggest_outfit` was never called on this path.

### Empty wardrobe

Command:

```bash
python app.py ask 'vintage graphic tee under $30' --empty-wardrobe
```

Actual output excerpt:

```text
(running with an empty wardrobe)

Here are two ways to style a Y2K-inspired butterfly print baby tee:

**Outfit 1: Retro Streetwear**
*   **Bottoms:** Mid-rise or low-rise baggy cargo pants in khaki or light wash denim to balance the fitted silhouette of the crop top.
*   **Footwear:** Chunky platform sneakers or retro skate shoes.
*   **Accessories:** A small nylon shoulder bag and a beaded choker or silver chain necklace.
```

The tool returned general styling advice rather than claiming these were saved wardrobe pieces. The run completed with a fit card and two real model calls (634 prompt tokens and 247 output tokens). This behavior already existed; no new empty-wardrobe handler was needed.

### Model unavailable

Changing the search wording initially failed to trigger this condition because the same selected item and wardrobe produced cached model prompts. A later uncached request still succeeded; the exact source of the valid credential was not established. I then supplied an explicitly invalid credential for one process, leaving the saved key unchanged:

```bash
env AI201_CACHE=0 GEMINI_API_KEY=invalid-test-key python app.py ask 'graphic tee'
```

Before adding the handler, the output included:

```text
1 model calls this session

ModelUnavailable: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.
```

After adding `ModelUnavailable` handlers around both model-calling tools in `agent.py`, the same command returned:

```text
The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.

1 model calls this session
```

This test triggered the error in `suggest_outfit`. I also added a handler to `create_fit_card`, but did not test a failure at that later step separately.

## Evaluation Method

The original five criteria and targets in `criteria.md` remain unchanged. Matching scenarios use `vintage graphic tee under $30` with the example wardrobe. The empty-search scenario uses `zzzxxyyqq`. Each criterion has its own scenario and five trials in each phase; all matching trials selected `lst_002`, the $18 Depop butterfly tee.

I first ran 25 before and 25 after trials using `run_eval.py`. That timer covered only `run_agent()`, so it did not fully measure criterion 5. Those reports remain as supplementary evidence: [initial before](results/run_2026-10-17_195610_before~.md) and [initial after](results/run_2026-10-17_215909_after.md). Their function-interval runtime results were 4/5 in each phase; these are not the final end-to-end verdicts.

I corrected the evaluation using `run_eval_cli.py`, which launches the actual `app.py ask` command and measures from immediately before process launch until the command exits and all output is collected. This includes Python startup, imports, wardrobe loading, MCP startup, model calls, retries, waiting, and final output. It does not include a person's typing time. Both corrected phases used this identical method, five scenarios, five trials each, and `AI201_CACHE=0`. I restored the original prompt for the corrected before phase, then restored the same 120-word improvement for the corrected after phase.

Each corrected trial runs in a fresh process, matching separate CLI submissions. This resets the adapter's in-process pacing history; provider quota limits still apply and caused observed retries. The final comparison uses the two corrected command evaluations. Their timing results are kept separate from the earlier function evaluations. Model `gemini-3.5-flash-lite`, temperature 0.9, data, targets, and request-limit settings were unchanged. There were 100 evaluation trials in total: 50 initial and 50 corrected.

## Run Log — Before

Final baseline evidence: [complete command-level before report](results/cli_2026-10-17_221924_before_cli.md).

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools and returns a fit card | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before suggest_outfit and names what to change | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Session item ID matches item received by suggest_outfit | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Caption includes correct price and platform | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Uncached completed fit card within five seconds, including waiting | 4 of 5 | FAIL | FAIL | PASS | PASS | PASS | MISSED (3/5) |

| Criterion 5 command time | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 |
|---|---|---|---|---|---|
| Seconds | 39.525895 | 61.533515 | 3.817321 | 3.093869 | 3.234040 |

### Actual output examples

#### Criterion 1 — Try 1

Producer: `tools.py::create_fit_card`, called by `agent.py::run_agent` and printed by `app.py::_ask_one`.

```text
Fit card: Channeling major early-2000s energy with this pink, white, and purple butterfly print Y2K Baby Tee. I scored it on Depop for just $18.00, and it's giving the ultimate fitted streetwear contrast when paired with baggy denim and chunky sneakers.
```

#### Criterion 2 — Try 1

Producer: `agent.py::run_agent` empty-search branch, printed by `app.py::_ask_one`.

```text
No listings matched your request. Try broader clothing keywords, a different size, or a higher maximum price.
```

#### Criterion 3 — Try 1

Producer: `agent.py::run_agent`, tracing the actual dictionary passed to `suggest_outfit`.

```text
→    Session item ID: lst_002; tool input item ID: lst_002. Use general styling advice if the wardrobe is empty.
```

#### Criterion 4 — Try 1

Producer: `tools.py::create_fit_card`, printed by `app.py::_ask_one`.

```text
Fit card: Channeling major Y2K streetwear energy with this adorable butterfly print baby tee. I scored it on Depop for just $18.00 and love styling it fitted and cropped against baggy denim.
```

#### Criterion 5 — Try 1

Producer: `run_eval_cli.py::main` for elapsed time and `tools.py::create_fit_card` for the caption.

```text
- Elapsed seconds: 39.525895
  Fit card: Channeling major Y2K streetwear energy with this fitted butterfly print baby tee. I found it on depop for just $18.00 and styled it with baggy dark wash jeans and chunky sneakers for that classic 2000s contrast.
```

## Verdicts and Diagnoses

1. **MET before and after (5/5 against 4/5).** Every criterion-1 trace shows MCP search, outfit generation, and caption generation, followed by a non-empty completed fit card. Exit code alone was not used as proof: actual outputs were checked.
2. **MET before and after (5/5 against 5/5).** Every impossible-query trace ends after the empty MCP search, with no outfit-tool call. Each run prints advice naming keywords, size, and maximum price as changes to try, and reports zero model calls.
3. **MET before and after (5/5 against 5/5).** Every criterion-3 trace records session ID `lst_002` matching the actual `new_item` argument ID. A slow run still passes this state criterion because it has no speed requirement.
4. **MET before and after (5/5 against 5/5).** Each full criterion-4 caption contains the selected listing's $18 price and Depop platform. `$18`, `$18.0`, and `$18.00` are the same monetary value; capitalization does not change the platform identity.
5. **MISSED before (3/5 against 4/5); MET after (4/5 against 4/5).** All timed runs returned completed fit cards. The full command times determine the verdict, including retry waiting. The following identifies every failed runtime trial.

| Phase / failed try | Tool and trace step | Mechanism |
|---|---|---|
| Before, criterion 5 try 1 — 39.525895 s | `create_fit_card`, between steps 6 and 7 | Provider rate limiting caused `generate()` to retry after an announced 36-second wait. |
| Before, criterion 5 try 2 — 61.533515 s | `suggest_outfit`, between steps 4 and 5 | Provider rate limiting caused `generate()` to retry after an announced 57-second wait. |
| After, criterion 5 try 3 — 96.367196 s | Both model tools, between steps 4–5 and 6–7 | Provider rate limiting caused an announced 34-second wait during outfit generation and a 59-second wait during caption generation. |

The recurring issue is request quota and retry delay, not search correctness, session handoff, or an absent caption. Criterion 3 try 4 also took 69.586022 seconds before and 81.311702 seconds after, with provider retries, but the handoff criterion still passed. These are not additional failed runtime-criterion trials because each criterion was scored using its designated five scenarios.

Criteria 1–4 passed, but all matching tests selected one item. This limits the strength of the conclusion. The next criterion I would tighten is price/platform accuracy across five distinct listings and platforms where available. I have not retroactively changed these criteria or results.

## Loop Trace

The following trace is from criterion 1, try 1 of the corrected before test. The trace formatter shortens long values. The report contains the full outfit advice and caption. Each note explains the next step in the code.
```text
[1] parse_query
      in:  vintage graphic tee under $30
      out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      →    Extract description, size, and maximum price.
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    Matches found; choose the first ranked result.
[3] select_item
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
      →    Saved item ID lst_002 in session for the remaining tools.
[4] suggest_outfit — call
      in:  {'new_item': {'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 200…
      →    Session item ID: lst_002; tool input item ID: lst_002. Use general styling advice if the wardrobe is empty.
[5] suggest_outfit — result
      out: Here are two practical outfit suggestions featuring your Y2K Baby Tee with Butterfly Print and pieces from you…
      →    Outfit advice received; proceed to create_fit_card.
[6] create_fit_card — call
      in:  {'outfit': 'Here are two practical outfit suggestions featuring your Y2K Baby Tee with Butterfly Print and pie…
      →    Use saved item ID lst_002 and the outfit advice returned by suggest_outfit.
[7] create_fit_card — result
      out: Channeling major early-2000s energy with this pink, white, and purple butterfly print Y2K Baby Tee. I scored i…
      →    Fit card received; run complete.
```

## The Improvement

The one functional improvement was a change to the system prompt in `tools.py::suggest_outfit`: request no more than 120 words total and keep each outfit explanation brief. The original prompt asked only for clear, non-empty text. The search implementation and fit-card prompt were unchanged. Required MCP wiring, failure handlers, traces, and measurement instrumentation were in place before each baseline.

The initial outputs contained lengthy outfit explanations passed into the second sequential model call. I tested whether limiting this text would reduce generation work and downstream prompt size. I expected shorter advice to reduce the work in both model calls. This would not remove quota waits or reduce the number of calls. The code requests the word limit but does not enforce it.

### Run Log — After

Final improvement evidence: [complete command-level after report](results/cli_2026-10-17_222613_after_cli.md).

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools and returns a fit card | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before suggest_outfit and names what to change | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Session item ID matches item received by suggest_outfit | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Caption includes correct price and platform | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Uncached completed fit card within five seconds, including waiting | 4 of 5 | PASS | PASS | FAIL | PASS | PASS | MET (4/5) |

| Criterion 5 command time | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 |
|---|---|---|---|---|---|
| Seconds | 2.819271 | 2.872902 | 96.367196 | 3.087146 | 2.789907 |

### Actual output examples

#### Criterion 1 — Try 1

Producer: `tools.py::create_fit_card`, called by `agent.py::run_agent` and printed by `app.py::_ask_one`.

```text
Fit card: Channeling pure nostalgic streetwear today with this butterfly graphic baby tee layered under a vintage black denim jacket and baggy dark wash jeans. Finished off with chunky white sneakers, it's the ultimate effortless 2000s look. Snagged this find on Depop for just $18.00!
```

#### Criterion 2 — Try 1

Producer: `agent.py::run_agent` empty-search branch, printed by `app.py::_ask_one`.

```text
No listings matched your request. Try broader clothing keywords, a different size, or a higher maximum price.
```

#### Criterion 3 — Try 1

Producer: `agent.py::run_agent`, tracing the actual dictionary passed to `suggest_outfit`.

```text
→    Session item ID: lst_002; tool input item ID: lst_002. Use general styling advice if the wardrobe is empty.
```

#### Criterion 4 — Try 1

Producer: `tools.py::create_fit_card`, printed by `app.py::_ask_one`.

```text
Fit card: Channeling pure 2000s streetwear energy by pairing this fitted crop tee with baggy dark wash jeans and a black denim jacket. It gives the ultimate effortless, nostalgic vibe for casual days. Snagged this butterfly print baby tee on Depop for just $18.00!
```

#### Criterion 5 — Try 1

Producer: `run_eval_cli.py::main` for elapsed time and `tools.py::create_fit_card` for the caption.

```text
- Elapsed seconds: 2.819271
  Fit card: Channeling total early-2000s streetwear energy with this Y2K Streetwear look, balancing a fitted crop silhouette with relaxed denim. I grabbed this butterfly print Y2K Baby Tee on Depop for just $18.00. It's the ultimate casual contrast piece for building effortless everyday outfits.
```

### Before and After

| Criterion | Target | Before | After |
|---|---|---|---|
| 1. Full completion | 4/5 | MET (5/5) | MET (5/5) |
| 2. Empty-search branch | 5/5 | MET (5/5) | MET (5/5) |
| 3. Item handoff | 5/5 | MET (5/5) | MET (5/5) |
| 4. Price/platform | 5/5 | MET (5/5) | MET (5/5) |
| 5. Full command within five seconds | 4/5 | MISSED (3/5) | MET (4/5) |

The runtime result improved from 3/5 to 4/5. However, the slowest run increased from 61.533515 to 96.367196 seconds. Quota waits occurred in different trials, and model responses vary. These results do not prove that the shorter prompt caused the improved pass count or solved the delays.

In the supplementary initial evaluations, output tokens decreased from 6,411 to 3,479 (45.7%) and prompt tokens from 25,726 to 22,958 (10.8%). Those are aggregate counts across both model tools for that earlier matched pair, not counts from the corrected CLI pair or isolated outfit measurements. Its function-interval pass count stayed 4/5. Together, the evidence supports lower observed text/token usage and an improved final sampled pass count, but not elimination of rate-limit delays.

## What's Still Broken

- **No criterion remains missed in the final after sample, but runtime remains unreliable.** One completed command took 96.367196 seconds because both model tools retried after provider rate limiting. Meeting a 4/5 target does not make that failure disappear. Next I would investigate quota capacity and request scheduling under realistic load. I stopped after the single measured prompt improvement required by this unit.
- **The improvement did not directly repair the dominant failure mechanism.** A response-length request cannot prevent request-count quota exhaustion. The after result therefore does not demonstrate a causal fix for quota delays.
- **Coverage is narrow.** All matching tests selected `lst_002`. Passing these five-trial scenarios does not establish correctness across all catalog items, prices, platforms, sizes, or missing brands. Future evaluation should include varied listings; I preserved the original targets for this submission.
- **Some requirements remain prompt-based.** There is no hard word-count validator or factual-caption validator. These tests checked the stated price/platform criterion, not every unsupported claim. Empty model responses can still raise `ValueError`; only `ModelUnavailable` received the new handlers.

## How I Used AI: Unit 4

I used ChatGPT to help write the MCP wrapper, connect the client call, fix indentation, add error handlers and traces, prepare scenarios, and write the evaluation scripts. It also suggested the 120-word prompt change and helped draft the README. Some assistance came as complete replacement files.

I ran the commands locally and shared the outputs and reports for review. The first timer missed command startup. I kept those reports and repeated both phases with command-level timing. The final results use the actual captions, item IDs, elapsed times, and error messages. I kept the failed trials and original targets.
