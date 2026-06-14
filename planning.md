# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**

<!-- Describe what this tool does in 1–2 sentences -->

> The purpose of FitFindr is to provide users a complete overview of second hand clothing options that match their style and budget. It also suggests how to style the new pieces with their existing wardrobe.

**Input parameters:**

<!-- List each parameter, its type, and what it represents -->

- `description` (str): ...
- `size` (str): ...
- `max_price` (float): ...
  > description: Keywords describing what the user is looking for.
  > size: The size the user wears (e.g., S, M, L).
  > max_price: The maximum price the user is willing to pay.

**What it returns:**

<!-- Describe the return value — what fields does a result contain? -->

> A list of matching listing dicts, sorted by relevance (best match first).

**What happens if it fails or returns nothing:**

<!-- What should the agent do if no listings match? -->

> Returns an empty list if nothing matches — does NOT raise an exception.

---

### Tool 2: suggest_outfit

**What it does:**

<!-- Describe what this tool does in 1–2 sentences -->

> Suggest how to style the new item with the user's existing wardrobe. This tool takes the new item and the user's current wardrobe as input and generates outfit suggestions that incorporate the new piece.

**Input parameters:**

<!-- List each parameter, its type, and what it represents -->

- `new_item` (dict): ...
- `wardrobe` (dict): ...
  > new_item: A listing dict (the item the user is considering buying).
  > wardrobe: A wardrobe dict with an 'items' key containing a list of wardrobe item dicts. May be empty.

**What it returns:**

<!-- Describe the return value -->

> A non-empty string with outfit suggestions.

**What happens if it fails or returns nothing:**

<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->

> If the wardrobe is empty, offer general styling advice for the item rather than raising an exception or returning an empty string.

---

### Tool 3: create_fit_card

**What it does:**

<!-- Describe what this tool does in 1–2 sentences -->

> Generate a short, shareable outfit caption for the thrifted find.

**Input parameters:**

<!-- List each parameter, its type, and what it represents -->

- `outfit` (...): ...
  > The outfit suggestion string from suggest_outfit().

**What it returns:**

<!-- Describe the return value -->

> A short, catchy caption that summarizes the outfit suggestion in a way that's suitable for sharing on social media.
> **What happens if it fails or returns nothing:**

<!-- What should the agent do if the outfit data is incomplete? -->

> If outfit is empty or missing, return a descriptive error message string.

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**

<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->

1. Set up the session state. Create the session dict. Think of it as a backpack the agent carries through every step. This is soley for inisialization,

2. Parse the user Query. Pull out three things from whatever the user typed: a description (keywords), a size, and a max price. If the user didn't mention a price or size, just set those to None.

3. Call search_listings() with the parsed values. Save what comes back into session["search_results"].
   If the list has results, keep going.
   If the list is empty, the agent is done. Set session["error"] to something like "No listings found — try different keywords or a higher budget." and return the session right there. Never call the next two tools.

4. take search_results[0] (the first one, which is the best match) and save it as session["selected_item"]. No decision here.

5. Call suggest_outfit() with the selected item and the user's wardrobe. If the wardrobe is empty, the tool handles that on its own — the agent doesn't need to check. Save the result in session["outfit_suggestion"].

6. Call create_fit_card() with the outfit suggestion. Save the result in session["fit_card"].

7. The agent is done! Return the session, which now has search_results, selected_item, outfit_suggestion, and fit_card for the user to see.

---

## State Management

**How does information from one tool get passed to the next?**

<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool            | Failure mode                          | Agent response |
| --------------- | ------------------------------------- | -------------- |
| search_listings | No results match the query            |                |
| suggest_outfit  | Wardrobe is empty                     |                |
| create_fit_card | Outfit input is missing or incomplete |                |

---

## Architecture

(On planning_mermaid.png)

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

**Tool 1 — `search_listings`:**
I'll paste the Tool 1 spec into Claude and ask it to write the function. I'll tell it to load listings from `load_listings()`, filter by price and size if those are provided, then score each result by how many keywords from the description show up in the title, description, or style tags. Anything with a score of 0 gets dropped, and the rest get sorted best-first. To check it works I'll run it with `"graphic tee", size="M", max_price=30` (should get results), `"designer ballgown", max_price=5` (should get nothing), and once with no size or price to make sure those are actually optional.

**Tool 2 — `suggest_outfit`:**
I'll give Claude the Tool 2 spec and ask it to write the function. The main thing it needs to handle is two cases: if the wardrobe is empty, ask the LLM for general styling tips for the item; if there are wardrobe items, ask the LLM to suggest specific outfits using those pieces. I'll test it by calling it once with `get_example_wardrobe()` to make sure it actually references real pieces, and once with `get_empty_wardrobe()` to make sure it doesn't crash or return an empty string.

**Tool 3 — `create_fit_card`:**
I'll give Claude the Tool 3 spec and ask it to write the function. It should check if the outfit string is empty first, and if so return an error message. Otherwise build a prompt that includes the item details and outfit suggestion and ask the LLM for a short caption that sounds like an actual Instagram post, not a product listing. I'll test it by passing in a real outfit string and making sure the output is 2–4 sentences and mentions the item name and price. I'll also pass in an empty string to make sure it returns an error instead of crashing.

**Milestone 4 — Planning loop and state management:**

I'll paste the Planning Loop section of this file and the architecture diagram into Claude and ask it to implement `run_agent()`. It needs to follow the seven steps: init the session, parse the query to pull out description/size/price, call `search_listings`, return early with an error message if nothing came back, otherwise grab `results[0]` as the selected item, call `suggest_outfit`, call `create_fit_card`, then return the session. I'll verify it by running the two test cases already at the bottom of `agent.py` — the graphic tee query should give back a fit card with no error, and the ballgown query should give back an error with no fit card.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
The agent parses the query to pull out the three things it needs: description = "vintage graphic tee", size = None (user didn't mention one), max_price = 30.0. It stores these in `session["parsed"]` and then calls `search_listings("vintage graphic tee", size=None, max_price=30.0)`. Let's say it comes back with 4 matching listings sorted by relevance. The agent saves those in `session["search_results"]`.

**Step 2:**
Since the results list isn't empty, the agent picks the first one — the best match — and saves it as `session["selected_item"]`. Let's say it's a listing like `{"title": "Vintage Band Tee", "price": 18.0, "platform": "Depop", ...}`. Now it calls `suggest_outfit(new_item=selected_item, wardrobe=wardrobe)`. The wardrobe has baggy jeans and chunky sneakers in it, so the LLM comes back with something like "pair this tee tucked into your baggy jeans with the chunky sneakers for a 90s grunge look." That gets saved in `session["outfit_suggestion"]`.

**Step 3:**
The agent takes that outfit suggestion string and the selected item and calls `create_fit_card(outfit=outfit_suggestion, new_item=selected_item)`. The LLM returns a short Instagram-style caption like "thrifted this vintage band tee on Depop for $18 and it goes with literally everything I own. baggy jeans + chunky sneakers and it's giving all the right energy." That gets saved in `session["fit_card"]` and the session is returned.

**Final output to user:**
The user sees the fit card caption, the outfit suggestion, and the name and price of the item the agent picked. Something like:

> **Found:** Vintage Band Tee — $18 on Depop
>
> **How to style it:** Pair it tucked into your baggy jeans with the chunky sneakers for a 90s grunge look. Add a flannel tied at the waist if you want more layering.
>
> **Fit card:** thrifted this vintage band tee on Depop for $18 and it goes with literally everything I own. baggy jeans + chunky sneakers and it's giving all the right energy.
