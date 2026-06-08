"""
Generates a daily personal post from Stuart's perspective as a franchise broker.
No article needed - draws from Stuart's 20+ years of experience and daily observations.
Modeled on Alex Smereczniak's LinkedIn style.
"""
import anthropic
import os
import random


PERSONAL_POST_TOPICS = [
    "A mistake franchise owners make when thinking about selling",
    "What buyers actually look for that most sellers never prepare",
    "The difference between owners who get top dollar and those who don't",
    "Why waiting until you're burned out is the worst time to sell",
    "What 20 years of franchise resale transactions has taught me",
    "The most common thing that kills a franchise deal at the last minute",
    "Why your franchise is worth more than you think - or less",
    "What SBA lenders look for that most sellers never think about",
    "The one thing that separates a good exit from a great one",
    "Why franchise owners underestimate how long a sale takes",
    "What buyers pay a premium for that has nothing to do with revenue",
    "The conversation every franchise owner should have 3 years before selling",
    "Why some franchise brands are much easier to sell than others",
    "What I tell every franchise owner who calls me in a panic to sell fast",
    "The valuation mistake I see franchise owners make over and over",
    "Why building a business that runs without you is the best exit strategy",
    "What happens when a franchise owner's lease runs out during a sale",
    "The difference between franchise transfer and franchise resale",
    "Why your franchisor relationship matters more than you think in a sale",
    "What I wish every franchise owner knew about SBA financing",
    "The real reason most franchise deals fall apart",
    "Why the best time to think about your exit is right now",
    "What 100+ franchise transactions taught me about what buyers really want",
    "Why owner-dependent businesses always sell for less",
    "The three numbers every franchise owner should know before they sell",
]


def generate_personal_post() -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)
    topic = random.choice(PERSONAL_POST_TOPICS)

    prompt = f"""You are writing a personal LinkedIn post for Stuart Levenberg.

Stuart is a franchise resale broker and M&A advisor. 20+ years of experience. 100+ transactions closed. He works with franchise owners who have 1-20 units and are thinking about selling.

TODAY'S TOPIC: {topic}

STYLE MODEL - Alex Smereczniak's LinkedIn approach:
- Opens with one short punchy line that stops the scroll
- Short paragraphs. One or two sentences each. Lots of white space.
- Writes from personal experience. Uses "I" naturally and confidently.
- Shares real observations from his work. Not generic advice.
- Makes the reader feel like they're getting insider knowledge.
- Ends with a soft CTA that invites conversation, not a hard sell.
- No fluff. No motivational quotes. No guru language.
- Reads like a smart friend texting you something they just realized.

STRUCTURE:
1. Hook - one line. Make a franchise owner stop scrolling.
2. The insight - 3-5 short paragraphs from Stuart's real experience
3. A specific example or observation (no names, just the situation)
4. What owners should take away from this
5. CTA - one of these, pick whichever fits:
   - "Curious what your franchise is worth today? Send me a message."
   - "If you are thinking about an exit - even years from now - let's talk."
   - "DM me if you want to understand what your business is actually worth."
   - "Happy to have a no-pressure conversation if this resonates."

RULES:
- Write in first person as Stuart
- Never use em-dashes. Use hyphens or rewrite.
- No hashtags. No emojis.
- 150-200 words total. Tight and punchy.
- Simple words. A 10th grader should follow every sentence.
- Do not start with "I"

Write ONLY the post text. Nothing else.
"""

    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )

    post_text = message.content[0].text.strip()

    return {
        "topic": topic,
        "post": post_text,
        "type": "Personal"
    }


if __name__ == "__main__":
    result = generate_personal_post()
    print(f"Topic: {result['topic']}\n")
    print(result["post"])
