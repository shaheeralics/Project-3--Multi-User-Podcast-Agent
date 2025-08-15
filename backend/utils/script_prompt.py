\
import textwrap

def build_messages(article_title: str, article_text: str, host_name: str, guest_name: str, aussie: bool = True):
    style = "Australian English with natural Aussie expressions and cadence" if aussie else "natural, conversational English"
    system = f"""
You are a veteran podcast producer. Create a two-speaker conversational script between a host and a guest.
Write in {style}. Keep it lively, insightful, and easy to follow.
Return ONLY valid JSON with this shape:
{{
  "script": [
    {{"id": 1, "speaker": "Host", "name": "{host_name}", "text": "..."}},
    {{"id": 2, "speaker": "Guest", "name": "{guest_name}", "text": "..."}}
  ]
}}
Rules:
- Alternate speakers each turn (Host then Guest then Host, etc.).
- Keep lines 1–4 sentences each, no emojis.
- Use the article to drive the discussion (summary + key insights + 1–2 thoughtful takes).
- Include a short intro and a crisp outro.
- No markdown, no backticks.
- Keep it under ~120 turns total.
"""
    user = f"""
ARTICLE TITLE: {article_title}

ARTICLE CONTENT:
{article_text}

Task: Produce the JSON script now.
"""
    messages = [
        {"role": "system", "content": system.strip()},
        {"role": "user", "content": user.strip()},
    ]
    return messages
