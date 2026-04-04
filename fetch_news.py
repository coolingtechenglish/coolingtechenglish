import os
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError
from html import unescape

from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY")

# RSS feeds from the 4 target sources
RSS_FEEDS = {
    "TechCrunch": "https://techcrunch.com/feed/",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Wired": "https://www.wired.com/feed/rss",
    "CNBC Tech": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CoolingTechEnglish/1.0)"
}


def strip_html(text):
    """Remove HTML tags and decode entities."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    return text.strip()


def fetch_rss_articles():
    """Fetch real articles from RSS feeds and return a list of dicts."""
    all_articles = []

    for source, url in RSS_FEEDS.items():
        try:
            print(f"Fetching RSS from {source}...")
            req = Request(url, headers=HEADERS)
            with urlopen(req, timeout=15) as resp:
                xml_bytes = resp.read()

            root = ET.fromstring(xml_bytes)

            # Handle both RSS 2.0 and Atom feeds
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            items = root.findall(".//item")  # RSS 2.0
            if not items:
                items = root.findall(".//atom:entry", ns)  # Atom

            count = 0
            for item in items:
                if count >= 5:  # max 5 per source
                    break

                # RSS 2.0 fields
                title = item.findtext("title")
                link = item.findtext("link")
                desc = item.findtext("description")
                pub_date = item.findtext("pubDate")

                # Atom fields (fallback)
                if not title:
                    title = item.findtext("atom:title", namespaces=ns)
                if not link:
                    link_el = item.find("atom:link", ns)
                    if link_el is not None:
                        link = link_el.get("href")
                if not desc:
                    desc = item.findtext("atom:summary", namespaces=ns)
                    if not desc:
                        desc = item.findtext("atom:content", namespaces=ns)
                if not pub_date:
                    pub_date = item.findtext("atom:updated", namespaces=ns)

                if not title or not link:
                    continue

                # The Verge Atom: link text might be empty, get from href
                if link and not link.startswith("http"):
                    continue

                all_articles.append({
                    "source": source,
                    "title": strip_html(title).strip(),
                    "url": link.strip(),
                    "description": strip_html(desc or "")[:500],
                    "pub_date": (pub_date or "").strip(),
                })
                count += 1

        except (URLError, ET.ParseError, Exception) as e:
            print(f"Warning: Failed to fetch {source}: {e}")
            continue

    print(f"Total RSS articles fetched: {len(all_articles)}")
    return all_articles


def build_gemini_prompt(rss_articles):
    """Build prompt with real article data for Gemini to process."""
    articles_text = ""
    for i, a in enumerate(rss_articles, 1):
        articles_text += f"""
Article {i}:
- Source: {a['source']}
- Title: {a['title']}
- URL: {a['url']}
- Description: {a['description']}
- Published: {a['pub_date']}
"""

    return f"""You are an English teacher specializing in tech English for Taiwanese learners.

Below are REAL tech news articles fetched from RSS feeds today. Select the 5 most interesting and diverse articles from this list. Use ONLY the URLs provided — do NOT invent or modify any URL.

{articles_text}

For EACH of the 5 selected articles, create English learning materials:

IMPORTANT CEFR difficulty requirements:
- 4 articles must be simplified to A1-B1 level (use short, simple sentences; common vocabulary)
- 1 article can be B2 level (more complex sentences allowed)
- For A1-A2: only simple present/past tense, short sentences (under 15 words), basic vocabulary
- For B1: slightly longer sentences OK, but avoid complex grammar

For EACH article, provide:
1. An 8-12 sentence English summary (around 120-150 words) rewritten at the appropriate CEFR level. Cover the full story: what happened, why it matters, who is involved, and what comes next.
2. A 4-6 sentence Traditional Chinese summary of the same content.
3. Exactly 3 key vocabulary words (with CEFR level, Chinese translation, definition, example sentence)
4. Exactly 2 useful phrases (with Chinese translation and example sentence)
5. Exactly 2 reading comprehension questions, each with the correct answer AND 2 plausible but wrong distractors (total 3 options). Shuffle the 3 options so the correct one is not always first.

Respond with ONLY a raw JSON object — no markdown, no backticks, no explanation:

{{
  "articles": [
    {{
      "tag": "category like AI/Hardware/Software/Cybersecurity/Startup",
      "cefr": "A2",
      "title_en": "Simplified English title at the CEFR level",
      "title_zh": "繁體中文標題",
      "summary_en": "8-12 sentence English summary (120-150 words) written at the specified CEFR level. Cover what happened, why it matters, who is involved, and what comes next.",
      "summary_zh": "4-6 sentence 繁體中文摘要",
      "source": "exact source name from the RSS data",
      "url": "exact URL from the RSS data — DO NOT change it",
      "date": "Mar 14, 2026",
      "vocabulary": [
        {{
          "word": "English word",
          "zh": "繁體中文翻譯",
          "cefr": "A2",
          "definition": "Brief English definition using simple words",
          "example": "Example sentence using the word"
        }}
      ],
      "phrases": [
        {{
          "phrase": "English phrase",
          "zh": "繁體中文翻譯",
          "example": "Example sentence using the phrase"
        }}
      ],
      "quiz": [
        {{
          "question": "Reading comprehension question in English",
          "answer": "The correct answer (must match one of the options exactly)",
          "options": ["Option A", "Option B (correct one goes here at a random position)", "Option C"]
        }}
      ]
    }}
  ],
  "vocabulary": [
    {{
      "word": "English word or phrase",
      "cefr": "B1",
      "zh": "繁體中文翻譯",
      "definition": "Brief English definition",
      "example": "Example sentence from the news context"
    }}
  ]
}}

CRITICAL RULES:
- Use ONLY the exact URLs from the RSS data above. NEVER invent a URL.
- Each article MUST have exactly 3 vocabulary items, 2 phrases, and 2 quiz questions. Each quiz question MUST have an "options" array of exactly 3 strings (1 correct + 2 wrong distractors, shuffled).
- The top-level "vocabulary" array should contain 5 of the most useful words across all articles.
- 4 articles at A1-B1 level, 1 article at B2 level.
- All Chinese must be Traditional Chinese (繁體中文).
- summary_en must be 8-12 sentences (120-150 words), not shorter.
- Return raw JSON only — nothing else."""


def fetch_news():
    # Step 1: Get real articles from RSS
    rss_articles = fetch_rss_articles()
    if len(rss_articles) < 5:
        raise RuntimeError(f"Only got {len(rss_articles)} articles from RSS. Need at least 5.")

    # Step 2: Send to Gemini for processing into learning materials
    print("Sending articles to Gemini for learning material generation...")
    client = genai.Client(api_key=API_KEY)

    prompt = build_gemini_prompt(rss_articles)

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        ),
    ]

    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="MINIMAL"),
    )

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=contents,
        config=config,
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

    # Verify URLs are from RSS (safety check)
    rss_urls = {a["url"] for a in rss_articles}
    for article in articles:
        if article.get("url") not in rss_urls:
            print(f"WARNING: URL not from RSS: {article.get('url')}")
            # Try to find a matching article by title similarity
            for ra in rss_articles:
                if ra["title"].lower()[:30] in article.get("title_en", "").lower() or \
                   article.get("source", "") == ra["source"]:
                    article["url"] = ra["url"]
                    print(f"  -> Fixed to: {ra['url']}")
                    break

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
                  <button class="speak-btn" onclick="speakWord('{escape_html(v.get('word',''))}',this)" title="Listen to pronunciation">&#128266;</button>
                  <button class="bookmark-btn" onclick="toggleBookmark('{escape_html(v.get('word',''))}','{escape_html(v.get('zh',''))}','{escape_html(v.get('definition',''))}','{escape_html(v.get('example',''))}','{v_cefr}',this)" title="Save to My Words">&#9734;</button>
                  <span class="cefr-badge-sm {get_cefr_class(v_cefr)}">{escape_html(v_cefr)}</span>
                  <span class="card-learn-zh">{escape_html(v.get('zh',''))}</span>
                </div>
                <div class="card-learn-def">{escape_html(v.get('definition',''))}</div>
                <div class="card-learn-ex">&ldquo;{escape_html(v.get('example',''))}&rdquo;</div>
                <div class="vocab-sr-row">
                  <button class="sr-btn sr-know" onclick="srMark('{escape_html(v.get('word',''))}','{escape_html(v.get('zh',''))}','{escape_html(v.get('definition',''))}','{escape_html(v.get('example',''))}','{v_cefr}',1,this)">&#10003; Know it</button>
                  <button class="sr-btn sr-learn" onclick="srMark('{escape_html(v.get('word',''))}','{escape_html(v.get('zh',''))}','{escape_html(v.get('definition',''))}','{escape_html(v.get('example',''))}','{v_cefr}',0,this)">&#8635; Still learning</button>
                </div>
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

        # Build quiz HTML (multiple-choice)
        quiz = a.get("quiz", [])
        quiz_html = ""
        for qi, q in enumerate(quiz):
            correct = escape_html(q.get('answer', ''))
            options = q.get('options', [q.get('answer', '')])
            options_html = ""
            for opt in options:
                is_correct = "1" if opt == q.get('answer', '') else "0"
                options_html += f"""<button class="quiz-option" data-correct="{is_correct}" onclick="checkQuizAnswer(this)">{escape_html(opt)}</button>"""
            quiz_html += f"""
              <div class="card-quiz-item">
                <div class="card-quiz-q">Q{qi+1}: {escape_html(q.get('question',''))}</div>
                <div class="card-quiz-options">{options_html}</div>
                <div class="card-quiz-result"></div>
              </div>"""

        card = f"""
    <div class="news-card" data-cefr="{cefr}" style="animation-delay:{i * 0.07}s">
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
        <button class="speak-btn" onclick="speakWord('{escape_html(v.get('word',''))}',this)" title="Listen to pronunciation">&#128266;</button>
        <button class="bookmark-btn" onclick="toggleBookmark('{escape_html(v.get('word',''))}','{escape_html(v.get('zh',''))}','{escape_html(v.get('definition',''))}','{escape_html(v.get('example',''))}','{cefr}',this)" title="Save to My Words">&#9734;</button>
        <span class="vocab-cefr {get_cefr_class(cefr)}">{escape_html(cefr)}</span>
      </div>
      <div class="vocab-zh">{escape_html(v.get('zh',''))}</div>
      <div class="vocab-def">{escape_html(v.get('definition',''))}</div>
      <div class="vocab-example">&ldquo;{escape_html(v.get('example',''))}&rdquo;</div>
      <div class="vocab-sr-row">
        <button class="sr-btn sr-know" onclick="srMark('{escape_html(v.get('word',''))}','{escape_html(v.get('zh',''))}','{escape_html(v.get('definition',''))}','{escape_html(v.get('example',''))}','{cefr}',1,this)">&#10003; Know it</button>
        <button class="sr-btn sr-learn" onclick="srMark('{escape_html(v.get('word',''))}','{escape_html(v.get('zh',''))}','{escape_html(v.get('definition',''))}','{escape_html(v.get('example',''))}','{cefr}',0,this)">&#8635; Still learning</button>
      </div>
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
