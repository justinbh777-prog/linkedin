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

    return f"""You are writing a LinkedIn post for Stuart Levenberg — a franchise M&A advisor and resale specialist with 20+ years of experience and 100+ franchise transactions closed.

Stuart's audience: franchise owners with 1-20 units who may be considering selling in the next 1-5 years.

Stuart's goal: become the most-followed source for franchise transactions, valuations, acquisitions, and private equity activity. Every post should attract franchise owners thinking about their exit.

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

1. HOOK (1 line — the financial or contrarian opener)

2. CONTEXT (2-4 micro-paragraphs — summarize the story with focus on: transaction size, unit count, growth rate, EBITDA, industry trend. One or two sentences per paragraph. Heavy white space.)

3. ANALYSIS (pattern recognition — why buyers are interested, what PE sees, why franchisees should care, what this means for valuations)

4. MY TAKE (Stuart's broker perspective — 2-3 short paragraphs starting with "As someone who works with franchise buyers and sellers every day..." — add real insight only a broker would have)

5. THREE THINGS TO WATCH (always exactly three bullet points)

6. CTA (one of the following — pick the most relevant to this article's topic):
   - "Curious what your franchise is worth today? Send me a message."
   - "If you own a franchise and have ever thought about an exit — even 3-5 years out — now is the time to understand your number. DM me."
   - "I work with franchise owners thinking about a future exit. If this story resonates, let's talk."
   - "Want to know how deals like this impact your franchise valuation? Send me a note."

---

STYLE RULES:
- No fluff. No motivational language. No guru phrases.
- Data-driven, analytical, operator-focused.
- Never use em-dashes. Use a regular hyphen or restructure the sentence instead.
- Max 2 sentences per paragraph. Aggressive white space.
- Use franchise vocabulary: unit economics, royalty stream, EBITDA, acquisition multiple, enterprise value, platform acquisition, roll-up, consolidation, same-store sales, SBA financeability.
- Total length: 180-250 words for standard posts, up to 400 for complex M&A stories.
- Do NOT use hashtags.
- Do NOT use emojis.
- Do NOT start with "I" — start with the hook.

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
