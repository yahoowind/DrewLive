name: Update UDPTV Playlist

on:
  schedule:
    - cron: '*/5 * * * *'  # Every 5 minutes
  workflow_dispatch:        # Manual run support

jobs:
  update-playlist:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'

      - name: Install dependencies
        run: pip install requests

      - name: Run UDPTV playlist update script
        run: python udptv.py

      - name: Force commit every time with trigger file
        run: |
          echo "$(date -u) — forced update trigger" > .trigger
          git config user.name "github-actions"
          git config user.email "github-actions@users.noreply.github.com"
          git add UDPTV.m3u .trigger
          git commit -m "Forced update with timestamp"
          git push
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}