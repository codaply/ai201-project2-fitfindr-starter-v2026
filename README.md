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
