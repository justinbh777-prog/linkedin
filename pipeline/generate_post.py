"""
Generates two LinkedIn post variants (A/B) using Claude.
Variant A: Financial/transaction hook
Variant B: Contrarian/pattern-recognition hook
"""
import anthropic
import os
import re


def load_strategy() -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "data", "strategy.md")
    with open(path) as f:
        return f.read()


def build_prompt(article: dict, hook_type: str, strategy: str) -> str:
    hook_instructions = {
        "A": (
            "Open with a FINANCIAL HOOK — lead with a specific dollar amount, transaction size, "
            "unit count, or multiple. Example: 'A 47-unit franchise just sold for 8 figures.' "
            "Make the reader stop scrolling with hard numbers."
        ),
        "B": (
            "Open with a CONTRARIAN OR PATTERN HOOK — lead with a market observation that "
            "challenges conventional thinking or reveals a hidden trend. "
            "Example: 'The smartest franchise buyers aren't buying restaurants anymore.' "
            "Make the reader feel like they're getting insider information."
        ),
    }

    return f"""You are writing a LinkedIn post for Stuart Levenberg — a franchise resale broker and M&A advisor with 20+ years of experience and 100+ transactions closed.

Stuart's audience: everyday franchise owners with 1-20 units in service, fitness, children's, home services, pet, automotive, cleaning, and similar non-food categories. These are owner-operators thinking about their future exit — not Wall Street dealmakers.

Stuart's goal: be the trusted advisor these owners turn to when they start thinking about selling. Every post should feel like advice from someone who has sat across the table from buyers and sellers hundreds of times.

IMPORTANT TONE GUIDANCE:
- Write for a franchise owner who runs a home services, fitness, or service business — not a restaurant chain operator
- Ground insights in what this means for the small operator, not billion-dollar PE deals
- Be direct and practical. These owners are busy. Get to the point.
- Never write from a Wall Street perspective. Write from Main Street.

---

CONTENT STRATEGY:
{strategy}

---

ARTICLE TO ANALYZE:
Title: {article['title']}
Source: {article['source']}
URL: {article['url']}
Summary: {article['summary']}
Full Text: {article.get('full_text', '')[:2000]}

---

HOOK TYPE FOR THIS VARIANT: {hook_instructions[hook_type]}

---

POST STRUCTURE (follow exactly):

1. HOOK (1 punchy line — make a franchise owner stop scrolling)

2. CONTEXT (2-3 micro-paragraphs — what happened, what it means. Focus on: unit count, owner economics, trend, valuation impact. One or two sentences max per paragraph.)

3. ANALYSIS (what this means for the 1-20 unit owner specifically — connect the story to their world)

4. MY TAKE (2-3 short paragraphs starting with "As someone who works with franchise buyers and sellers every day..." — give insight only a broker who has closed 100+ deals would know)

5. THREE THINGS TO WATCH (exactly three bullet points relevant to small franchise owners)

6. CTA (pick the most relevant):
   - "Curious what your franchise is worth today? Send me a message."
   - "If you own a franchise and have ever thought about an exit — even 3-5 years out — now is the time to understand your number. DM me."
   - "I work with franchise owners thinking about a future exit. If this story resonates, let's talk."
   - "Want to know how this trend impacts your franchise valuation? Send me a note."

---

STYLE RULES:
- No fluff. No motivational language. No guru phrases.
- Never use em-dashes. Use a regular hyphen or rewrite the sentence.
- Max 2 sentences per paragraph. Heavy white space.
- Vocabulary: unit economics, SBA financing, seller's discretionary earnings, acquisition multiple, transferability, recast earnings, same-store sales, franchisee profitability.
- Length: 180-250 words standard, up to 350 for complex topics.
- No hashtags. No emojis. Do not start with "I".

Write ONLY the post text. No preamble, no explanation, no title.
"""


def generate_post(article: dict) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)
    strategy = load_strategy()

    results = {}
    for variant, hook_type in [("A", "A"), ("B", "B")]:
        print(f"  Generating variant {variant}...")
        prompt = build_prompt(article, hook_type, strategy)

        message = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        post_text = message.content[0].text.strip()
        hook_line = post_text.split("\n")[0].strip()

        results[f"variant_{variant}"] = post_text
        results[f"hook_type_{variant}"] = "Financial" if hook_type == "A" else "Contrarian"

    return results


def detect_hook_type(text: str) -> str:
    """Classify a hook line for tracking purposes."""
    first_line = text.split("\n")[0].lower()
    if re.search(r'\$[\d,]+|\d+[\s-]unit|\d+\s*(figure|location|store)', first_line):
        return "Financial"
    if any(w in first_line for w in ["isn't", "aren't", "not", "wrong", "quietly", "nobody"]):
        return "Contrarian"
    if any(w in first_line for w in ["just", "filing", "announced", "closes", "acquires"]):
        return "Acquisition"
    return "Pattern"


if __name__ == "__main__":
    sample = {
        "title": "KKR Acquires 200-Unit Home Services Franchise for $450M",
        "source": "Franchise Times",
        "url": "https://franchisetimes.com/example",
        "summary": "Private equity firm KKR has acquired a 200-unit home services franchise in a deal valued at $450 million.",
        "full_text": "KKR completed the acquisition of ServiceMaster brands...",
        "topic_category": "PE/M&A",
    }
    results = generate_post(sample)
    print("\n=== VARIANT A ===")
    print(results["variant_A"])
    print("\n=== VARIANT B ===")
    print(results["variant_B"])
