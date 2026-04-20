#!/usr/bin/env python3
"""
Build four CSV files: Genesis and Leviticus, each by chapters and by pericope.
Word counts and sheva-word counts. Uses genesis.json and bible/leviticus.json.
Sheva words: Strong's derived from שבע (seven / swear).
"""

import json
import csv
from pathlib import Path
from collections import defaultdict

# Sheva-related words (שבע): seven, swear, oath, week, and names/forms derived from them.
# Full list (from core roots + hebrew.json deriv field):
#
#   Strong's   Notes (from deriv/word)
#   --------   ----------------------
#   h472       Elisheba (from h7651/h7650)
#   h791       Ashbea (from h7650)
#   h884       Beersheba (well of the oath/seven)
#   h1339      Bath-sheba
#   h1340      Bath-shua (same as h1339)
#   h3089      Jehosheba (Jehovah-sworn)
#   h3090      Jehoshabeath (form of h3089)
#   h7620      seven, week
#   h7621      oath (shevuʿah)
#   h7627      week (shevuaʿ)
#   h7637      seventh (e.g. seventh day)
#   h7650      to swear, take an oath (shāvaʿ)
#   h7651      seven (shevaʿ)
#   h7652      seven (alt form, sheba)
#   h7655      seven (Aramaic corr. to h7651)
#   h7656      shebah, seven(-th) (masc. of h7651)
#   h7657      seventy
#   h7658      seventh (adj)
#   h7659      seventh (n), seventh portion
#
SHEVA_STRONGS = {"h472", "h791", "h884", "h1339", "h1340", "h3089", "h3090", "h7620", "h7621", "h7627", "h7637", "h7650", "h7651", "h7652", "h7655", "h7656", "h7657", "h7658", "h7659"}

# Genesis pericope (verse ranges inclusive)
GENESIS_MELODY_RANGES = [
    ((1, 1), (7, 24), "1. Template: Creation to the Flood"),
    ((8, 1), (11, 32), "2. Ark Exit, Ham, Nimrod, Nations, Tower"),
    ((12, 1), (14, 16), "3. Avram Called, Egypt, Lot, 9 Kings Sodom #1"),
    ((14, 17), (16, 6), "4. Covenant, Hagar taken, Hagar Wilderness #1"),
    ((16, 7), (19, 26), "5. Go back, Name Change, Tent Promise, Sodom #2"),
    ((19, 27), (21, 16), "6. Avimelek, Isaac Born, Hagar Wilderness #2"),
    ((21, 17), (22, 19), "7. Hagar at BeerSheva, Avimelek BeerSheva, Binding of Isaac"),
]


# Genesis chapters to include (1-25)
GENESIS_CHAPTERS_END = 25

# Leviticus pericope (chapter ranges)
LEVITICUS_PERICOPES = [
    (1, 7, "Ritual Sacrifices"),
    (8, 10, "Priests Ordained"),
    (11, 15, "Ritual Purity"),
    (16, 17, "Day of Atonement"),
    (18, 20, "Moral Purity"),
    (21, 22, "Qualifications for Priests"),
    (23, 25, "Ritual Feasts"),
    (26, 27, "Epilog"),
]


def in_range(ch, v, start, end):
    """True if (ch, v) is in [start, end] inclusive (chapter, verse order)."""
    s_ch, s_v = start
    e_ch, e_v = end
    if ch < s_ch or ch > e_ch:
        return False
    if ch == s_ch and v < s_v:
        return False
    if ch == e_ch and v > e_v:
        return False
    return True


def count_sheva_in_verses(vobjs):
    """Return (total_words, sheva_count, list of 'text (ch:v)' for sheva words)."""
    total_words = 0
    sheva_count = 0
    sheva_texts = []
    for vobj in vobjs:
        vid = vobj["id"]
        ch = int(vid[2:5])
        v = int(vid[5:8])
        for w in vobj["verse"]:
            total_words += 1
            num = (w.get("number") or "").strip().lower()
            if num in SHEVA_STRONGS:
                sheva_count += 1
                text = (w.get("text") or "").strip()
                sheva_texts.append(f"{text} ({ch}:{v})" if text else f"({ch}:{v})")
    return total_words, sheva_count, sheva_texts


def build_genesis_by_chapter(verses):
    """Genesis ch 1-25, one row per chapter."""
    by_ch = defaultdict(list)
    for vobj in verses:
        ch = int(vobj["id"][2:5])
        if 1 <= ch <= GENESIS_CHAPTERS_END:
            by_ch[ch].append(vobj)
    rows = []
    for ch in sorted(by_ch.keys()):
        vobjs = by_ch[ch]
        first_v = int(vobjs[0]["id"][5:8])
        last_v = int(vobjs[-1]["id"][5:8])
        total_words, sheva_count, sheva_texts = count_sheva_in_verses(vobjs)
        which_sheva = "; ".join(sheva_texts) if sheva_texts else ""
        pct = round((sheva_count / total_words) * 100, 4) if total_words else 0
        rows.append({
            "Chapter": ch,
            "Verse Range": f"{ch}:{first_v} - {ch}:{last_v}",
            "Title": f"Chapter {ch}",
            "Total Words": total_words,
            "Sheva Words": sheva_count,
            "Percentage": pct,
            "Which Sheva words": which_sheva,
        })
    return rows


def build_genesis_by_pericope(verses):
    """Genesis 7 laps by verse range."""
    rows = []
    for lap_num, (start, end, title) in enumerate(GENESIS_MELODY_RANGES, start=1):
        range_str = f"{start[0]}:{start[1]} - {end[0]}:{end[1]}"
        vobjs = [v for v in verses if in_range(int(v["id"][2:5]), int(v["id"][5:8]), start, end)]
        total_words, sheva_count, sheva_texts = count_sheva_in_verses(vobjs)
        which_sheva = "; ".join(sheva_texts) if sheva_texts else ""
        pct = round((sheva_count / total_words) * 100, 4) if total_words else 0
        rows.append({
            "Lap number": lap_num,
            "Verse Range": range_str,
            "Title": title,
            "Total Words": total_words,
            "Sheva Words": sheva_count,
            "Percentage": pct,
            "Which Sheva words": which_sheva,
        })
    return rows


def build_leviticus_by_chapter(by_chapter):
    """Leviticus ch 1-27, one row per chapter."""
    rows = []
    for ch in sorted(by_chapter.keys()):
        vobjs = by_chapter[ch]
        first_v = int(vobjs[0]["id"][5:8])
        last_v = int(vobjs[-1]["id"][5:8])
        total_words, sheva_count, sheva_texts = count_sheva_in_verses(vobjs)
        which_sheva = "; ".join(sheva_texts) if sheva_texts else ""
        pct = round((sheva_count / total_words) * 100, 4) if total_words else 0
        rows.append({
            "Chapter": ch,
            "Verse Range": f"{ch}:{first_v} - {ch}:{last_v}",
            "Title": f"Chapter {ch}",
            "Total Words": total_words,
            "Sheva Words": sheva_count,
            "Percentage": pct,
            "Which Sheva words": which_sheva,
        })
    return rows


def build_leviticus_by_pericope(by_chapter):
    """Leviticus 8 parts by chapter range."""
    rows = []
    for part_num, (start_ch, end_ch, title) in enumerate(LEVITICUS_PERICOPES, start=1):
        first_v = int(by_chapter[start_ch][0]["id"][5:8])
        last_v = int(by_chapter[end_ch][-1]["id"][5:8])
        range_str = f"{start_ch}:{first_v} - {end_ch}:{last_v}"
        vobjs = []
        for ch in range(start_ch, end_ch + 1):
            vobjs.extend(by_chapter[ch])
        total_words, sheva_count, sheva_texts = count_sheva_in_verses(vobjs)
        which_sheva = "; ".join(sheva_texts) if sheva_texts else ""
        pct = round((sheva_count / total_words) * 100, 4) if total_words else 0
        rows.append({
            "Part": part_num,
            "Verse Range": range_str,
            "Title": title,
            "Total Words": total_words,
            "Sheva Words": sheva_count,
            "Percentage": pct,
            "Which Sheva words": which_sheva,
        })
    return rows


def main():
    data_dir = Path(__file__).resolve().parent
    genesis_path = data_dir / "genesis.json"
    leviticus_path = data_dir / "bible" / "leviticus.json"

    with open(genesis_path, "r", encoding="utf-8") as f:
        genesis_verses = json.load(f)
    with open(leviticus_path, "r", encoding="utf-8") as f:
        leviticus_verses = json.load(f)

    by_chapter_lev = defaultdict(list)
    for vobj in leviticus_verses:
        ch = int(vobj["id"][2:5])
        by_chapter_lev[ch].append(vobj)

    # Output paths
    out_gen_ch = data_dir / "looking_for_sevens_genesis_chapters.csv"
    out_gen_per = data_dir / "looking_for_sevens_genesis_pericope.csv"
    out_lev_ch = data_dir / "looking_for_sevens_leviticus_chapters.csv"
    out_lev_per = data_dir / "looking_for_sevens_leviticus_pericope.csv"

    # Genesis chapters
    rows_gen_ch = build_genesis_by_chapter(genesis_verses)
    with open(out_gen_ch, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Chapter", "Verse Range", "Title", "Total Words", "Sheva Words", "Percentage", "Which Sheva words"])
        w.writeheader()
        w.writerows(rows_gen_ch)
    print(f"Wrote {out_gen_ch} ({len(rows_gen_ch)} rows)")

    # Genesis pericope
    rows_gen_per = build_genesis_by_pericope(genesis_verses)
    with open(out_gen_per, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Lap number", "Verse Range", "Title", "Total Words", "Sheva Words", "Percentage", "Which Sheva words"])
        w.writeheader()
        w.writerows(rows_gen_per)
    print(f"Wrote {out_gen_per} ({len(rows_gen_per)} rows)")

    # Leviticus chapters
    rows_lev_ch = build_leviticus_by_chapter(by_chapter_lev)
    with open(out_lev_ch, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Chapter", "Verse Range", "Title", "Total Words", "Sheva Words", "Percentage", "Which Sheva words"])
        w.writeheader()
        w.writerows(rows_lev_ch)
    print(f"Wrote {out_lev_ch} ({len(rows_lev_ch)} rows)")

    # Leviticus pericope
    rows_lev_per = build_leviticus_by_pericope(by_chapter_lev)
    with open(out_lev_per, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Part", "Verse Range", "Title", "Total Words", "Sheva Words", "Percentage", "Which Sheva words"])
        w.writeheader()
        w.writerows(rows_lev_per)
    print(f"Wrote {out_lev_per} ({len(rows_lev_per)} rows)")


if __name__ == "__main__":
    main()
