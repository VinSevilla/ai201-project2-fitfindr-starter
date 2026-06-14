# FitFindr

FitFindr is an AI agent that searches secondhand clothing listings and tells you how to style what it finds with what you already own.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root with your Groq API key (get one free at console.groq.com):

```
GROQ_API_KEY=your_key_here
```

Run the app:

```bash
python app.py
```

Run the tests:

```bash
pytest tests/
```

---

## Tool Inventory

### `search_listings(description, size, max_price)`

**What it does:** Searches the mock listings dataset for items that match what the user typed.

**Inputs:**
- `description` (str) — keywords from the user's query, e.g. `"vintage graphic tee"`
- `size` (str or None) — size to filter by, e.g. `"M"`. Pass `None` to skip size filtering.
- `max_price` (float or None) — highest price to include, e.g. `30.0`. Pass `None` to skip price filtering.

**Output:** A list of listing dicts sorted by relevance (best match first). Returns an empty list if nothing matches.

---

### `suggest_outfit(new_item, wardrobe)`

**What it does:** Asks the LLM to suggest 1–2 outfits using the new item and the user's existing wardrobe.

**Inputs:**
- `new_item` (dict) — a listing dict returned by `search_listings`
- `wardrobe` (dict) — the user's wardrobe, with an `"items"` key containing a list of wardrobe item dicts

**Output:** A non-empty string with outfit suggestions. If the wardrobe is empty, it gives general styling advice instead.

---

### `create_fit_card(outfit, new_item)`

**What it does:** Asks the LLM to write a short, casual Instagram-style caption for the outfit.

**Inputs:**
- `outfit` (str) — the outfit suggestion string from `suggest_outfit`
- `new_item` (dict) — the listing dict, so the caption can mention the item name, price, and platform

**Output:** A 2–4 sentence caption string. If `outfit` is empty, returns an error message string instead of crashing.

---

## Planning Loop

The agent runs through the same steps every time in order. There's only one real decision point — whether `search_listings` found anything.

1. Initialize the session dict (stores everything the agent needs to carry between steps)
2. Parse the query with regex to pull out a description, size, and price
3. Call `search_listings` with those values
   - If the list comes back empty → set `session["error"]` and stop. Never call the next two tools.
   - If the list has results → keep going
4. Set `selected_item = results[0]` (the best match)
5. Call `suggest_outfit` with the selected item and the user's wardrobe
6. Call `create_fit_card` with the outfit suggestion and selected item
7. Return the session

---

## State Management

Everything is stored in a single session dict that gets passed through every step. No tool is called with hardcoded values — each tool gets its input directly from whatever the previous step wrote to the session.

| Session key | Set in step | Read by |
|---|---|---|
| `parsed` | Step 2 | Step 3 (`search_listings`) |
| `search_results` | Step 3 | Step 4 |
| `selected_item` | Step 4 | Steps 5 and 6 |
| `outfit_suggestion` | Step 5 | Step 6 |
| `fit_card` | Step 6 | Returned to user |
| `error` | Step 3 (if empty) | Returned to user |

---

## Error Handling

| Tool | Failure mode | What the agent does |
|---|---|---|
| `search_listings` | No listings match the query | Sets `session["error"]` with a helpful message and returns early. `suggest_outfit` and `create_fit_card` are never called. |
| `suggest_outfit` | The user's wardrobe is empty | The tool handles it internally — calls the LLM for general styling tips instead of outfit combinations. The agent doesn't need a special branch for this. |
| `create_fit_card` | The outfit string is empty or whitespace | Returns a descriptive error message string. Never raises an exception. |

**Concrete examples from testing:**

- Running `search_listings("designer ballgown", size="XXS", max_price=5)` returned `[]` and the agent set `session["error"] = "No listings found..."`, with `session["fit_card"]` staying `None`. A spy function confirmed `suggest_outfit` was never called.
- Running `create_fit_card("", fake_item)` returned `"Error: no outfit suggestion available to generate a fit card."` — no exception, no API call.
- Running `suggest_outfit(item, get_empty_wardrobe())` returned general styling advice (not an empty string) because the empty-wardrobe branch triggers a different LLM prompt.

---

## AI Usage

### Instance 1 — Implementing `search_listings`

**What I gave it:** The Tool 1 spec from `planning.md` (parameter names, types, return value, failure mode) and the `load_listings()` docstring showing every field in a listing dict.

**What it produced:** A working implementation that loaded listings, filtered by price and size, and scored by keyword overlap. The structure matched the spec.

**What I changed:** The original output only checked keywords against `title`. I updated it to also search `description` and `style_tags`, because that's what the spec said and a tee with "graphic tee" only in its tags wouldn't have matched otherwise. I also verified it against three queries manually before trusting it.

---

### Instance 2 — Implementing `suggest_outfit`

**What I gave it:** The Tool 2 spec from `planning.md`, the `suggest_outfit` docstring (including the empty-wardrobe branch), and a printed example wardrobe dict from `get_example_wardrobe()` so it could see the actual field names (`name`, `notes`, `style_tags`, etc.).

**What it produced:** A function with the two-branch structure — one LLM prompt for empty wardrobe, a different one for a wardrobe with items. It formatted wardrobe items as a bulleted list and asked the LLM to name specific pieces.

**What I changed:** The first version didn't include the `notes` field in the wardrobe prompt (e.g. "High-waisted, sits above the hip"). I added that because those notes give the LLM more context to make outfit suggestions specific. I also ran both branches against the real API and checked that the empty-wardrobe response didn't just return an empty string before keeping the output.

---

### Instance 3 — Implementing the planning loop (`run_agent`)

**What I gave it:** The Planning Loop section of `planning.md` (the seven numbered steps), the architecture diagram from `planning_mermaid.png`, and the `_new_session()` function signature from `agent.py`.

**What it produced:** A mostly correct `run_agent()` implementation with the right step order, the early-return branch after `search_listings`, and all session fields being written in the right places.

**What I changed:** The generated version used `session["results"]` in one place instead of `session["search_results"]`, which would have caused a KeyError. I caught this by reviewing the code against the session dict keys in `_new_session()` before running it. I also ran a spy test after to confirm `suggest_outfit` was genuinely never called on the no-results path — not just that the error message looked right.

---

## Spec Reflection

**What matched the spec:** The planning loop matched exactly. The conditional logic (branch on empty search results, early return, pick `results[0]`, pass through session) was designed in `planning.md` before any code was written, and the implementation followed it step by step without needing changes.

**What I had to figure out along the way:** The `create_fit_card` spec only listed `outfit` as a parameter, but `tools.py` also requires `new_item` so the caption can mention the item name and price. I caught this by comparing the spec against the diagram and the actual function signature before implementing.

**One thing that surprised me:** The Groq model `llama3-8b-8192` was decommissioned and had to be swapped for `llama-3.1-8b-instant`. The code structure didn't need to change — just the model name string. Having the model name in one place in the code made that easy to fix.
