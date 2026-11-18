#!/usr/bin/env python3
"""Country ranking for the plant-microbiome vocabulary survey, updated automatically.

Reads the survey's public statistics page on LimeSurvey (country question only), draws the
ranking, and writes a small thank-you page with the chart into docs/. LimeSurvey sends
participants to that page when they submit the survey.

Runs every 15 minutes on GitHub (see .github/workflows/leaderboard.yml); nothing to do by hand.
To try it on your own computer:   pip install matplotlib   then   python3 update_leaderboard.py
"""
import datetime
import html
import json
import os
import re
import sys
import urllib.request
from html.parser import HTMLParser

# ---------------------------------------------------------------- settings
LIMESURVEY       = os.environ.get("LIMESURVEY", "https://limesurvey.zhaw.ch")
SURVEY_ID        = os.environ.get("SURVEY_ID", "746251")      # the ID LimeSurvey shows after import
LANGUAGE         = "en"
TOP_N            = 0      # bars in the chart; 0 = every country with MIN_PARTICIPANTS or more
MIN_PARTICIPANTS = 1      # countries with fewer participants are not shown (anonymity)
TERMS            = 10     # terms per participant, for the thank-you text
OUT_DIR          = "docs"
PAGE_TITLE       = "Plant-microbiome vocabulary challenge"
# -------------------------------------------------------------------------

STATS_URL = "%s/index.php/statistics_user/%s?language=%s" % (LIMESURVEY.rstrip("/"), SURVEY_ID, LANGUAGE)


class Rows(HTMLParser):
    """Collects the text of every table cell, row by row."""
    def __init__(self):
        super().__init__()
        self.rows, self.row, self.cell = [], None, None
    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []
    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None
    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)


def read_counts():
    req = urllib.request.Request(STATS_URL, headers={"User-Agent": "terminology-survey-leaderboard"})
    with urllib.request.urlopen(req, timeout=60) as r:
        page = r.read().decode("utf-8", "replace")
    parser = Rows()
    parser.feed(page)
    counts = {}
    for row in parser.rows:
        if len(row) < 2:
            continue
        m = re.fullmatch(r"(.+?) \(([A-Z]{2})\)", row[0])
        n = re.fullmatch(r"\d+", row[1].replace(",", ""))
        if m and n:
            counts[m.group(1)] = counts.get(m.group(1), 0) + int(row[1].replace(",", ""))
    if not counts:
        raise SystemExit("No country counts found at %s. Is public statistics switched on for the survey, "
                         "and the country question marked for public statistics?" % STATS_URL)
    return counts


def draw(ranking, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(5.2, 0.42 * max(len(ranking), 1) + 1.2), dpi=200)
    if ranking:
        names = [c for c, _ in ranking][::-1]
        values = [n for _, n in ranking][::-1]
        bars = ax.barh(names, values, color="#4a8f3c", height=0.62)
        for bar, v in zip(bars, values):
            ax.text(bar.get_width() + max(values) * 0.02, bar.get_y() + bar.get_height() / 2,
                    str(v), va="center", fontsize=9, color="#333333")
        ax.set_xlim(0, max(values) * 1.18)
        ax.tick_params(axis="y", length=0, labelsize=10)
    else:
        ax.text(0.5, 0.5, "The ranking appears once %d people\nfrom the same country have taken part."
                % MIN_PARTICIPANTS, ha="center", va="center", fontsize=10, color="#555555", transform=ax.transAxes)
        ax.set_yticks([])
    ax.set_xticks([])
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(False)
    ax.set_title("Participants per country", fontsize=11, loc="left", color="#222222", pad=10)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def write_page(stamp, path):
    page = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<style>
  body { margin: 0; padding: 32px 16px; background: #ffffff; color: #222222;
         font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.5; }
  main { max-width: 560px; margin: 0 auto; }
  h1 { font-size: 1.4rem; margin: 0 0 0.6rem; }
  .note { border-left: 4px solid #4a8f3c; background: #f3f8f1; padding: 0.6em 1em; margin: 1rem 0 1.5rem; }
  img { max-width: 100%%; height: auto; display: block; }
  .small { color: #666666; font-size: 0.85rem; margin-top: 0.5rem; }
</style>
</head>
<body>
<main>
  <h1>Thank you, all %(terms)d terms are done.</h1>
  <div class="note">Your ratings now count for your country. You may close this window.</div>
  <img src="leaderboard.png?v=%(v)s" alt="Participants per country">
  <p class="small">Countries with at least %(min)d participants. Last change: %(stamp)s UTC. Updated every hour.</p>
</main>
</body>
</html>
""" % {"title": html.escape(PAGE_TITLE), "terms": TERMS, "v": re.sub(r"\D", "", stamp),
       "min": MIN_PARTICIPANTS, "stamp": stamp}
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    counts = read_counts()
    ranking = sorted(((c, n) for c, n in counts.items() if n >= MIN_PARTICIPANTS), key=lambda x: (-x[1], x[0]))
    if TOP_N:
        ranking = ranking[:TOP_N]
    data_path = os.path.join(OUT_DIR, "leaderboard.json")
    previous = None
    if os.path.exists(data_path):
        with open(data_path, encoding="utf-8") as f:
            previous = json.load(f).get("ranking")
    if previous == [list(x) for x in ranking] and os.path.exists(os.path.join(OUT_DIR, "index.html")):
        print("No change since the last run.")
        return
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
    draw(ranking, os.path.join(OUT_DIR, "leaderboard.png"))
    write_page(stamp, os.path.join(OUT_DIR, "index.html"))
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump({"updated": stamp, "ranking": ranking}, f, ensure_ascii=False, indent=1)
    print("Updated %s:" % stamp)
    for i, (c, n) in enumerate(ranking, 1):
        print("  %d. %s: %d" % (i, c, n))
    hidden = sum(1 for n in counts.values() if 0 < n < MIN_PARTICIPANTS)
    if hidden:
        print("%d countr%s not shown (fewer than %d participants)." % (hidden, "y" if hidden == 1 else "ies", MIN_PARTICIPANTS))


if __name__ == "__main__":
    main()
