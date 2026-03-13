"""
Offline test: inject sample news data into index.html to verify card rendering.
Run this file to see the website with sample data.
"""
import json
import re
import sys
import os

# Add parent dir so we can import helpers
sys.path.insert(0, os.path.dirname(__file__))
from fetch_news import build_news_html, build_vocab_html

SAMPLE_DATA = {
    "articles": [
        {
            "tag": "AI",
            "cefr": "A2",
            "title_en": "Google Makes a New AI Tool for Students",
            "title_zh": "\u8c37\u6b4c\u70ba\u5b78\u751f\u88fd\u4f5c\u65b0\u7684 AI \u5de5\u5177",
            "summary_en": "Google made a new AI tool. It helps students learn faster. The tool can answer questions and explain hard topics in simple words.",
            "summary_zh": "\u8c37\u6b4c\u88fd\u4f5c\u4e86\u4e00\u500b\u65b0\u7684 AI \u5de5\u5177\u3002\u5b83\u5e6b\u52a9\u5b78\u751f\u66f4\u5feb\u5b78\u7fd2\u3002\u9019\u500b\u5de5\u5177\u53ef\u4ee5\u56de\u7b54\u554f\u984c\uff0c\u4e26\u7528\u7c21\u55ae\u7684\u8a5e\u5f59\u89e3\u91cb\u96e3\u61c2\u7684\u4e3b\u984c\u3002",
            "source": "TechCrunch",
            "date": "Mar 13, 2026",
            "vocabulary": [
                {"word": "tool", "zh": "\u5de5\u5177", "cefr": "A1", "definition": "Something you use to do a job", "example": "This AI tool helps you study English."},
                {"word": "explain", "zh": "\u89e3\u91cb", "cefr": "A2", "definition": "To make something clear or easy to understand", "example": "The teacher explains the lesson very well."},
                {"word": "topic", "zh": "\u4e3b\u984c", "cefr": "A2", "definition": "A subject that people talk or write about", "example": "Today's topic is about technology."}
            ],
            "phrases": [
                {"phrase": "learn faster", "zh": "\u5b78\u5f97\u66f4\u5feb", "example": "With this app, you can learn faster than before."},
                {"phrase": "answer questions", "zh": "\u56de\u7b54\u554f\u984c", "example": "The chatbot can answer questions about science."}
            ],
            "quiz": [
                {"question": "What did Google make?", "answer": "Google made a new AI tool for students."},
                {"question": "What can the tool do?", "answer": "It can answer questions and explain hard topics in simple words."}
            ]
        },
        {
            "tag": "Hardware",
            "cefr": "A1",
            "title_en": "Apple Shows a New iPhone",
            "title_zh": "\u860b\u679c\u5c55\u793a\u65b0 iPhone",
            "summary_en": "Apple has a new phone. It is very fast. The camera is better too. Many people want to buy it.",
            "summary_zh": "\u860b\u679c\u6709\u4e00\u652f\u65b0\u624b\u6a5f\u3002\u5b83\u975e\u5e38\u5feb\u3002\u76f8\u6a5f\u4e5f\u66f4\u597d\u3002\u5f88\u591a\u4eba\u60f3\u8cb7\u5b83\u3002",
            "source": "The Verge",
            "date": "Mar 12, 2026",
            "vocabulary": [
                {"word": "fast", "zh": "\u5feb\u7684", "cefr": "A1", "definition": "Moving or working quickly", "example": "The new phone is very fast."},
                {"word": "camera", "zh": "\u76f8\u6a5f", "cefr": "A1", "definition": "A device for taking photos", "example": "I use my phone camera every day."},
                {"word": "buy", "zh": "\u8cb7", "cefr": "A1", "definition": "To get something by paying money", "example": "I want to buy a new laptop."}
            ],
            "phrases": [
                {"phrase": "want to", "zh": "\u60f3\u8981", "example": "I want to learn more about AI."},
                {"phrase": "better than", "zh": "\u6bd4\u2026\u66f4\u597d", "example": "This camera is better than my old one."}
            ],
            "quiz": [
                {"question": "Is the new iPhone fast or slow?", "answer": "The new iPhone is very fast."},
                {"question": "What is better on the new phone?", "answer": "The camera is better."}
            ]
        },
        {
            "tag": "Software",
            "cefr": "B1",
            "title_en": "Microsoft Updates Windows with AI Features",
            "title_zh": "\u5fae\u8edf\u66f4\u65b0 Windows \u52a0\u5165 AI \u529f\u80fd",
            "summary_en": "Microsoft released a big update for Windows. The update includes new AI features that can help users write emails, create presentations, and organize files more efficiently.",
            "summary_zh": "\u5fae\u8edf\u91cb\u51fa\u4e86 Windows \u7684\u91cd\u5927\u66f4\u65b0\u3002\u6b64\u66f4\u65b0\u5305\u542b\u65b0\u7684 AI \u529f\u80fd\uff0c\u53ef\u4ee5\u5e6b\u52a9\u7528\u6236\u5beb\u96fb\u5b50\u90f5\u4ef6\u3001\u5efa\u7acb\u7c21\u5831\u4ee5\u53ca\u66f4\u6709\u6548\u7387\u5730\u7d44\u7e54\u6a94\u6848\u3002",
            "source": "Ars Technica",
            "date": "Mar 13, 2026",
            "vocabulary": [
                {"word": "update", "zh": "\u66f4\u65b0", "cefr": "A2", "definition": "To make something newer or better", "example": "Please update your software to the latest version."},
                {"word": "feature", "zh": "\u529f\u80fd", "cefr": "B1", "definition": "An important part or characteristic of something", "example": "The best feature of this app is voice control."},
                {"word": "efficiently", "zh": "\u6709\u6548\u7387\u5730", "cefr": "B1", "definition": "In a way that works well without wasting time", "example": "AI helps people work more efficiently."}
            ],
            "phrases": [
                {"phrase": "released an update", "zh": "\u91cb\u51fa\u66f4\u65b0", "example": "The company released an update for its software yesterday."},
                {"phrase": "help users", "zh": "\u5e6b\u52a9\u7528\u6236", "example": "The new tool can help users save time on daily tasks."}
            ],
            "quiz": [
                {"question": "What company released the update?", "answer": "Microsoft released the update."},
                {"question": "Name two things the AI features can help with.", "answer": "They can help write emails and create presentations."}
            ]
        },
        {
            "tag": "Cybersecurity",
            "cefr": "A2",
            "title_en": "Hackers Attack a Big Company",
            "title_zh": "\u99ed\u5ba2\u653b\u64ca\u4e00\u5bb6\u5927\u516c\u53f8",
            "summary_en": "Hackers attacked a big tech company last week. They stole some user data. The company says it is fixing the problem now.",
            "summary_zh": "\u99ed\u5ba2\u4e0a\u9031\u653b\u64ca\u4e86\u4e00\u5bb6\u5927\u578b\u79d1\u6280\u516c\u53f8\u3002\u4ed6\u5011\u7aca\u53d6\u4e86\u4e00\u4e9b\u7528\u6236\u8cc7\u6599\u3002\u8a72\u516c\u53f8\u8868\u793a\u6b63\u5728\u4fee\u5fa9\u554f\u984c\u3002",
            "source": "Reuters",
            "date": "Mar 11, 2026",
            "vocabulary": [
                {"word": "hacker", "zh": "\u99ed\u5ba2", "cefr": "A2", "definition": "A person who breaks into computer systems", "example": "The hacker tried to steal passwords."},
                {"word": "data", "zh": "\u8cc7\u6599", "cefr": "A2", "definition": "Information stored on a computer", "example": "Your personal data should be kept safe."},
                {"word": "attack", "zh": "\u653b\u64ca", "cefr": "A2", "definition": "To try to hurt or damage something", "example": "Hackers attack websites to steal information."}
            ],
            "phrases": [
                {"phrase": "fix the problem", "zh": "\u4fee\u5fa9\u554f\u984c", "example": "The IT team is working to fix the problem."},
                {"phrase": "stole data", "zh": "\u7aca\u53d6\u8cc7\u6599", "example": "The hackers stole data from thousands of users."}
            ],
            "quiz": [
                {"question": "What did the hackers steal?", "answer": "They stole some user data."},
                {"question": "Is the company fixing the problem?", "answer": "Yes, the company says it is fixing the problem now."}
            ]
        },
        {
            "tag": "AI",
            "cefr": "B2",
            "title_en": "OpenAI Launches Advanced Reasoning Model for Enterprise Customers",
            "title_zh": "OpenAI \u70ba\u4f01\u696d\u5ba2\u6236\u63a8\u51fa\u9032\u968e\u63a8\u7406\u6a21\u578b",
            "summary_en": "OpenAI has unveiled a sophisticated new reasoning model designed specifically for enterprise applications. The model demonstrates remarkable improvements in complex problem-solving, code generation, and data analysis, potentially transforming how businesses leverage AI technology.",
            "summary_zh": "OpenAI \u63a8\u51fa\u4e86\u4e00\u500b\u5c08\u70ba\u4f01\u696d\u61c9\u7528\u8a2d\u8a08\u7684\u7cbe\u5bc6\u65b0\u63a8\u7406\u6a21\u578b\u3002\u8a72\u6a21\u578b\u5728\u8907\u96dc\u554f\u984c\u89e3\u6c7a\u3001\u7a0b\u5f0f\u78bc\u751f\u6210\u548c\u6578\u64da\u5206\u6790\u65b9\u9762\u8868\u73fe\u51fa\u986f\u8457\u9032\u6b65\uff0c\u6709\u53ef\u80fd\u6539\u8b8a\u4f01\u696d\u5229\u7528 AI \u6280\u8853\u7684\u65b9\u5f0f\u3002",
            "source": "Wired",
            "date": "Mar 13, 2026",
            "vocabulary": [
                {"word": "sophisticated", "zh": "\u7cbe\u5bc6\u7684", "cefr": "B2", "definition": "Complex, advanced, and well-developed", "example": "This is a very sophisticated piece of software."},
                {"word": "leverage", "zh": "\u5229\u7528", "cefr": "B2", "definition": "To use something to maximum advantage", "example": "Companies leverage AI to improve their services."},
                {"word": "enterprise", "zh": "\u4f01\u696d", "cefr": "B2", "definition": "A large business or company", "example": "The software is designed for enterprise customers."}
            ],
            "phrases": [
                {"phrase": "designed specifically for", "zh": "\u5c08\u70ba\u2026\u8a2d\u8a08", "example": "This course is designed specifically for beginners."},
                {"phrase": "potentially transforming", "zh": "\u6709\u53ef\u80fd\u6539\u8b8a", "example": "AI is potentially transforming every industry."}
            ],
            "quiz": [
                {"question": "Who is the new model designed for?", "answer": "It is designed specifically for enterprise customers."},
                {"question": "What three areas does the model improve in?", "answer": "Complex problem-solving, code generation, and data analysis."}
            ]
        }
    ],
    "vocabulary": [
        {"word": "tool", "cefr": "A1", "zh": "\u5de5\u5177", "definition": "Something you use to do a job", "example": "This AI tool helps you study English."},
        {"word": "update", "cefr": "A2", "zh": "\u66f4\u65b0", "definition": "To make something newer or better", "example": "Please update your app to get new features."},
        {"word": "data", "cefr": "A2", "zh": "\u8cc7\u6599", "definition": "Information stored on a computer", "example": "Keep your personal data safe online."},
        {"word": "feature", "cefr": "B1", "zh": "\u529f\u80fd", "definition": "An important part of something", "example": "The best feature is the AI assistant."},
        {"word": "leverage", "cefr": "B2", "zh": "\u5229\u7528", "definition": "To use something to maximum advantage", "example": "Companies leverage AI to grow faster."}
    ]
}


def main():
    from datetime import datetime

    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    updated_time = datetime.utcnow().strftime("%b %d, %Y %H:%M UTC")
    news_html = build_news_html(SAMPLE_DATA["articles"])
    vocab_html = build_vocab_html(SAMPLE_DATA["vocabulary"])

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
        f"<!-- UPDATED_TIME -->{updated_time} (SAMPLE DATA)<!-- /UPDATED_TIME -->",
        html,
    )

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Injected sample data at {updated_time}")
    print("Open index.html in your browser to preview!")


if __name__ == "__main__":
    main()
