"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:

    listings = load_listings()

    if max_price is not None:
        listings = [l for l in listings if l["price"] <= max_price]

    if size is not None:
        listings = [l for l in listings if size.lower() in l["size"].lower()]

    keywords = [w.lower() for w in description.split()]

    def score(listing):
        searchable = (
            listing["title"].lower()
            + " " + listing["description"].lower()
            + " " + " ".join(listing["style_tags"]).lower()
        )
        return sum(1 for kw in keywords if kw in searchable)

    scored = [(score(l), l) for l in listings]
    scored = [(s, l) for s, l in scored if s > 0]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [l for _, l in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:

    client = _get_groq_client()
    item_desc = (
        f"{new_item['title']} — {new_item['category']}, "
        f"{', '.join(new_item.get('colors', []))}, "
        f"style: {', '.join(new_item.get('style_tags', []))}"
    )

    if not wardrobe.get("items"):
        prompt = (
            f"I just thrifted this item: {item_desc}. "
            "I don't have my wardrobe info handy. "
            "Give me 1–2 general outfit ideas — what types of pieces pair well with it, "
            "what vibe or aesthetic it fits, and how I could style it."
        )
    else:
        wardrobe_lines = []
        for w in wardrobe["items"]:
            note = f" ({w['notes']})" if w.get("notes") else ""
            wardrobe_lines.append(f"- {w['name']}{note}")
        wardrobe_text = "\n".join(wardrobe_lines)

        prompt = (
            f"I'm thinking of buying this thrifted item: {item_desc}.\n\n"
            f"Here's what I already own:\n{wardrobe_text}\n\n"
            "Suggest 1–2 complete outfits that use the new item combined with specific pieces "
            "from my wardrobe. Name the exact pieces you're pairing together and describe the vibe."
        )

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    if not outfit or not outfit.strip():
        return "Error: no outfit suggestion available to generate a fit card."

    client = _get_groq_client()
    prompt = (
        f"I thrifted a '{new_item['title']}' for ${new_item['price']} on {new_item['platform']}. "
        f"Here's how I'm styling it:\n\n{outfit}\n\n"
        "Write a 2–4 sentence Instagram caption for this outfit. "
        "Make it sound like a real person wrote it — casual, specific about the vibe, not like a product description. "
        "Mention the item name, price, and platform exactly once each, worked in naturally. "
        "No hashtags."
    )

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=1.0,
    )
    return response.choices[0].message.content.strip()
