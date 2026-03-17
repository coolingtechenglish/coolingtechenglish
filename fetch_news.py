import os
import json
import requests
import re
from datetime import datetime

API_KEY = os.environ.get("ANTHROPIC_API_KEY")

PROMPT = """Search for the 5 most important technology news stories from today or the past 2 days.

After searching, respond with ONLY a raw JSON object — no markdown, no backticks, no explanation before or after. Use this exact structure:

{
  "articles": [
    {
      "tag": "category like AI/Hardware/Software/Cybersecurity/Startup",
      "cefr": "B2",
      "title_en": "English title",
      "title_zh": "Traditional Chinese title",
      "summary_en": "2-3 sentence English summary",
      "summary_zh": "2-3 sentence Traditional Chinese summary",
      "source": "source name",
      "date": "today or X days ago"
    }
  ],
  "vocabulary": [
    {
      "word": "English word or phrase",
      "cefr": "B2",
      "zh": "Traditional Chinese translation",
      "definition": "Brief English definition",
      "example": "short example sentence from the news context"
    }
  ]
}

For the "cefr" field on each article, rate the reading difficulty: A1=very simple, A2=simple, B1=intermediate, B2=upper-intermediate, C1=advanced, C2=near-native.
For each vocabulary word, rate the word difficulty on the CEFR scale.

Return exactly 5 articles and exactly 5 vocabulary items. Raw JSON only — nothing else."""


def fetch_news():
    print("Fetching news from Anthropic API...")
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 4000,
            "tools": [{"type": "web_search_20250305", "name": "web_search"}],
            "messages": [{"role": "user", "content": PROMPT}],
        },
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()

    full_text = "\n".join(
        block["text"] for block in data.get("content", []) if block.get("type") == "text"
    )

    # Strip markdown fences
    full_text = re.sub(r"```json\s*", "", full_text, flags=re.IGNORECASE)
    full_text = re.sub(r"```\s*", "", full_text)

    # Extract JSON object
    start = full_text.index("{")
    end = full_text.rindex("}") + 1
    json_str = full_text[start:end]

    # Fix trailing commas
    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)

    news_data = json.loads(json_str)
    print(f"Got {len(news_data.get('articles', []))} articles and {len(news_data.get('vocabulary', []))} vocab items.")
    return news_data


def escape_html(s):
    if not s:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )


CEFR_CLASSES = {
    "A1": "cefr-A1", "A2": "cefr-A2",
    "B1": "cefr-B1", "B2": "cefr-B2",
    "C1": "cefr-C1", "C2": "cefr-C2",
}


def get_cefr_class(level):
    return CEFR_CLASSES.get((level or "B2").upper(), "cefr-B1")


def build_news_html(articles):
    cards = []
    for i, a in enumerate(articles):
        cefr = (a.get("cefr") or "B2").upper()
        card = f"""
    <div class="news-card" style="animation-delay:{i * 0.07}s">
      <div class="card-top">
        <div class="card-tag">{escape_html(a.get('tag',''))}</div>
        <div class="cefr-badge {get_cefr_class(cefr)}" title="CEFR Reading Level: {escape_html(cefr)}">{escape_html(cefr)}</div>
      </div>
      <div class="card-title">{escape_html(a.get('title_en',''))}</div>
      <div class="card-title-zh">{escape_html(a.get('title_zh',''))}</div>
      <div class="card-summary">{escape_html(a.get('summary_en',''))}</div>
      <div class="card-summary-zh">{escape_html(a.get('summary_zh',''))}</div>
      <div class="card-footer">
        <span>📰 {escape_html(a.get('source',''))}</span>
        <span>{escape_html(a.get('date',''))}</span>
      </div>
    </div>"""
        cards.append(card)
    return "\n".join(cards)


def build_vocab_html(vocabulary):
    cards = []
    for i, v in enumerate(vocabulary):
        cefr = (v.get("cefr") or "B2").upper()
        card = f"""
    <div class="vocab-card" style="animation-delay:{i * 0.07}s">
      <div class="vocab-num">0{i+1}</div>
      <div class="vocab-word-line">
        <span class="vocab-word">{escape_html(v.get('word',''))}</span>
        <span class="vocab-cefr {get_cefr_class(cefr)}">{escape_html(cefr)}</span>
      </div>
      <div class="vocab-zh">{escape_html(v.get('zh',''))}</div>
      <div class="vocab-def">{escape_html(v.get('definition',''))}</div>
      <div class="vocab-example">"{escape_html(v.get('example',''))}"</div>
    </div>"""
        cards.append(card)
    return "\n".join(cards)


def inject_into_html(news_data):
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    updated_time = datetime.utcnow().strftime("%b %d, %Y %H:%M UTC")
    news_html = build_news_html(news_data["articles"])
    vocab_html = build_vocab_html(news_data["vocabulary"])

    # Replace markers in HTML
    html = re.sub(
        r"<!-- NEWS_CARDS_START -->.*?<!-- NEWS_CARDS_END -->",
        f"<!-- NEWS_CARDS_START -->\n{news_html}\n<!-- NEWS_CARDS_END -->",
        html,
        flags=re.DOTALL,
    )
    html = re.sub(
        r"<!-- VOCAB_CARDS_START -->.*?<!-- VOCAB_CARDS_END -->",
        f"<!-- VOCAB_CARDS_START -->\n{vocab_html}\n<!-- VOCAB_CARDS_END -->",
        html,
        flags=re.DOTALL,
    )
    html = re.sub(
        r"<!-- UPDATED_TIME -->.*?<!-- /UPDATED_TIME -->",
        f"<!-- UPDATED_TIME -->{updated_time}<!-- /UPDATED_TIME -->",
        html,
    )

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"index.html updated at {updated_time}")


if __name__ == "__main__":
    news_data = fetch_news()
    inject_into_html(news_data)
