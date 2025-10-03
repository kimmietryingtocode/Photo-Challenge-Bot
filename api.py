from fastapi import FastAPI, HTTPException
import requests, bs4, re
from typing import List, TypedDict, Optional
app = FastAPI()

SOURCE_URL = "https://www.thefocalpointhub.com/blog-52/2024"
HEADERS = {"User-Agent": "photo-prompts/1.0 (+contact@example.com)"}

MONTHS = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
]
month_head_re = re.compile(r"^\s*(" + "|".join(MONTHS) + r")\b", re.I)

class Prompt(TypedDict, total=False):
    id: str
    month: str
    week_in_month: int
    week: int
    title: str
    time_hint: str
    tags: List[str]

def fetch_prompts_from_focalpoint():
    r = requests.get(SOURCE_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = bs4.BeautifulSoup(r.text, "html.parser")

    # Strategy: find headings that start with a month name (h2/h3),
    # then collect following <ul><li> bullets until the next month heading.
    out = []
    global_week = 0

    # Both h2 and h3 appear on the page; grab in document order.
    headings = [*soup.find_all(["h2","h3"])]
    for i, h in enumerate(headings):
        text = (h.get_text(" ", strip=True) or "")
        if not month_head_re.match(text):
            continue

        # Normalize the month name from the heading start
        month_name = month_head_re.match(text).group(1).title()

        # Walk sibling elements until the next month heading
        prompts_this_month = []
        sib = h.next_sibling
        while sib:
            # stop if we hit another heading that starts with a month
            if getattr(sib, "name", None) in ("h2","h3"):
                nxt_text = sib.get_text(" ", strip=True) if sib else ""
                if month_head_re.match(nxt_text):
                    break
            # collect bullets
            if getattr(sib, "name", None) == "ul":
                for li in sib.find_all("li", recursive=False):
                    title = li.get_text(" ", strip=True)
                    if title:
                        prompts_this_month.append(title)
            sib = sib.next_sibling

        # Some months have extra paragraphs before/after lists; keep first 4 bullets
        for idx, title in enumerate(prompts_this_month[:4], start=1):
            global_week += 1
            out.append({
                "id": f"{month_name[:3].lower()}-{idx:02d}",
                "month": month_name,
                "week_in_month": idx,
                "week": global_week,
                "title": title,
                "time_hint": "1 week",
                "tags": []
            })

    # Sanity: we expect ~48 (12*4). If the page added/removed items, keep whatever we got.
    return out

ALL: Optional[List[Prompt]] = None

def ensure_cache() -> List[Prompt]:
    global ALL
    if ALL is None:
        ALL = fetch_prompts_from_focalpoint()
    return ALL

@app.get("/prompts/week/{week}")
def get_prompt_by_week(week: int):
    items = ensure_cache()                # items is List[Prompt], not None
    if week < 1:
        raise HTTPException(status_code=400, detail="week must be >= 1")

    n = len(items)
    if n == 0:
        raise HTTPException(status_code=503, detail="no prompts available")

    # clamp or wrap if you have fewer than 52
    if week > n:
        week = n                           # or: week = ((week - 1) % n) + 1

    # return the matching prompt
    for p in items:
        if p["week"] == week:
            return p

    # if week keys are 1..n contiguous, you should never reach here
    raise HTTPException(status_code=404, detail="prompt not found")
