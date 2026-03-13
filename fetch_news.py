import os
import json
import re
from datetime import datetime

from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY")

PROMPT = """You are a tech English teacher. Search for the 5 most important technology news stories from today or the past 2 days.

Recommended sources: TechCrunch, The Verge, Ars Technica, Wired, Reuters Technology, BBC Technology, CNBC Tech, Engadget.

IMPORTANT CEFR difficulty requirements:
- 4 articles must be simplified to A1-B1 level (use short, simple sentences; common vocabulary)
- 1 article can be B2 level (more complex sentences allowed)
- For A1-A2 articles: use only simple present/past tense, short sentences (under 15 words), basic vocabulary
- For B1 articles: slightly longer sentences OK, but avoid complex grammar

For EACH article, provide:
1. The news summary in BOTH English and Traditional Chinese
2. Exactly 3 key vocabulary words from the article (with CEFR level, Chinese translation, definition, example sentence)
3. Exactly 2 useful phrases from the article (with Chinese translation and example sentence)
4. Exactly 2 reading comprehension questions with answers

Respond with ONLY a raw JSON object — no markdown, no backticks, no explanation. Use this exact structure:

{
  "articles": [
    {
      "tag": "category like AI/Hardware/Software/Cybersecurity/Startup",
      "cefr": "A2",
      "title_en": "English title (simplified for the CEFR level)",
      "title_zh": "Traditional Chinese title",
      "summary_en": "2-3 sentence English summary written at the specified CEFR level",
      "summary_zh": "2-3 sentence Traditional Chinese summary",
      "source": "source name like TechCrunch",
      "url": "https://full-url-to-the-original-article",
      "date": "Mar 13, 2026",
      "vocabulary": [
        {
          "word": "English word",
          "zh": "Traditional Chinese translation",
          "cefr": "A2",
          "definition": "Brief English definition using simple words",
          "example": "Example sentence using the word"
        }
      ],
      "phrases": [
        {
          "phrase": "English phrase",
          "zh": "Traditional Chinese translation",
          "example": "Example sentence using the phrase"
        }
      ],
      "quiz": [
        {
          "question": "Reading comprehension question in English",
          "answer": "Short answer in English"
        }
      ]
    }
  ],
  "vocabulary": [
    {
      "word": "English word or phrase",
      "cefr": "B1",
      "zh": "Traditional Chinese translation",
      "definition": "Brief English definition",
      "example": "Example sentence from the news context"
    }
  ]
}

Rules:
- Each article MUST have exactly 3 vocabulary items, 2 phrases, and 2 quiz questions.
- Each article MUST include the full URL to the original source article (not a search URL).
- The top-level "vocabulary" array should contain 5 of the most useful words across all articles.
- 4 articles at A1-B1 level, 1 article at B2 level.
- All Chinese must be Traditional Chinese (繁體中文).
- Return raw JSON only — nothing else."""


def fetch_news():
    print("Fetching news from Gemini API with Google Search grounding...")
    client = genai.Client(api_key=API_KEY)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=PROMPT,
        config=types.GenerateContentConfig(
            tools=[
                types.Tool(google_search=types.GoogleSearch())
            ],
            temperature=0.7,
        ),
    )

    full_text = response.text

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
    articles = news_data.get("articles", [])
    vocab = news_data.get("vocabulary", [])
    print(f"Got {len(articles)} articles and {len(vocab)} vocab items.")
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
    return CEFR_CLASSES.get((level or "B1").upper(), "cefr-B1")


def build_news_html(articles):
    cards = []
    for i, a in enumerate(articles):
        cefr = (a.get("cefr") or "B1").upper()

        # Build vocabulary HTML for this article
        vocab_items = a.get("vocabulary", [])
        vocab_html = ""
        for v in vocab_items:
            v_cefr = (v.get("cefr") or "A2").upper()
            vocab_html += f"""
              <div class="card-learn-item">
                <div class="card-learn-word">
                  <span class="card-learn-term">{escape_html(v.get('word',''))}</span>
                  <span class="cefr-badge-sm {get_cefr_class(v_cefr)}">{escape_html(v_cefr)}</span>
                  <span class="card-learn-zh">{escape_html(v.get('zh',''))}</span>
                </div>
                <div class="card-learn-def">{escape_html(v.get('definition',''))}</div>
                <div class="card-learn-ex">&ldquo;{escape_html(v.get('example',''))}&rdquo;</div>
              </div>"""

        # Build phrases HTML
        phrases = a.get("phrases", [])
        phrases_html = ""
        for p in phrases:
            phrases_html += f"""
              <div class="card-learn-item">
                <div class="card-learn-word">
                  <span class="card-learn-term">{escape_html(p.get('phrase',''))}</span>
                  <span class="card-learn-zh">{escape_html(p.get('zh',''))}</span>
                </div>
                <div class="card-learn-ex">&ldquo;{escape_html(p.get('example',''))}&rdquo;</div>
              </div>"""

        # Build quiz HTML
        quiz = a.get("quiz", [])
        quiz_html = ""
        for qi, q in enumerate(quiz):
            quiz_html += f"""
              <div class="card-quiz-item">
                <div class="card-quiz-q">Q{qi+1}: {escape_html(q.get('question',''))}</div>
                <div class="card-quiz-a" style="display:none">{escape_html(q.get('answer',''))}</div>
                <button class="card-quiz-btn" onclick="this.previousElementSibling.style.display=this.previousElementSibling.style.display==='none'?'block':'none'; this.textContent=this.previousElementSibling.style.display==='none'?'Show Answer':'Hide Answer'">Show Answer</button>
              </div>"""

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
        <span>&#128240; <a href="{escape_html(a.get('url','#'))}" target="_blank" rel="noopener" style="color:inherit;text-decoration:underline">{escape_html(a.get('source',''))}</a></span>
        <span>{escape_html(a.get('date',''))}</span>
      </div>
      <button class="card-expand-btn" onclick="var el=this.nextElementSibling; el.classList.toggle('open'); this.textContent=el.classList.contains('open')?'&#9650; Hide Study Materials':'&#9660; Study Materials'">&#9660; Study Materials</button>
      <div class="card-learn-section">
        <div class="card-learn-block">
          <div class="card-learn-heading">&#128214; Key Vocabulary</div>
          {vocab_html}
        </div>
        <div class="card-learn-block">
          <div class="card-learn-heading">&#128172; Useful Phrases</div>
          {phrases_html}
        </div>
        <div class="card-learn-block">
          <div class="card-learn-heading">&#10067; Comprehension Check</div>
          {quiz_html}
        </div>
      </div>
    </div>"""
        cards.append(card)
    return "\n".join(cards)


def build_vocab_html(vocabulary):
    cards = []
    for i, v in enumerate(vocabulary):
        cefr = (v.get("cefr") or "B1").upper()
        card = f"""
    <div class="vocab-card" style="animation-delay:{i * 0.07}s">
      <div class="vocab-num">0{i+1}</div>
      <div class="vocab-word-line">
        <span class="vocab-word">{escape_html(v.get('word',''))}</span>
        <span class="vocab-cefr {get_cefr_class(cefr)}">{escape_html(cefr)}</span>
      </div>
      <div class="vocab-zh">{escape_html(v.get('zh',''))}</div>
      <div class="vocab-def">{escape_html(v.get('definition',''))}</div>
      <div class="vocab-example">&ldquo;{escape_html(v.get('example',''))}&rdquo;</div>
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
