name: Update News

on:
  schedule:
    - cron: '0 */6 * * *'  # every 6 hours
  workflow_dispatch:         # manual trigger button

jobs:
  update:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install requests

      - name: Fetch and inject news
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python3 fetch_news.py

      - name: Commit updated index.html
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add index.html
          git diff --cached --quiet || git commit -m "Auto-update news $(date -u '+%Y-%m-%d %H:%M')"
          git push
