import json

input_path = "data/bible_project_translation.txt"
output_path = "data/bible_project_translation.json"

verses = []

book = "1"
translation = "BP2025"  # BibleProject 2025 translation
bookname = "Genesis"

with open(input_path, "r", encoding="utf-8") as infile:
    current_id = 1
    current_verse = None
    current_chapter = None
    for line in infile:
        line = line.strip()
        if not line:
            continue
        if line.startswith("Chapter"):
            current_chapter = line.split(" ")[1]
            continue
        
        # print(line)
        current_verse, hyphen, text = line.split(" ", 2)
        new_data = {
            "id": str(current_id),
            "translation": translation,
            "book": book,
            "chapter": int(current_chapter),
            "verse": int(current_verse),
            "text": text.strip(),
            "bookname": bookname
        }
        verses.append(new_data)
        current_id += 1

with open(output_path, "w", encoding="utf-8") as outfile:
    json.dump(verses, outfile, ensure_ascii=False, indent=4)

    # {
    #     "id": "3292331",
    #     "translation": "NIV2011",
    #     "book": 1,
    #     "chapter": 48,
    #     "verse": 2,
    #     "text": "When Jacob was told, \u201cYour son Joseph has come to you,\u201d Israel rallied his strength and sat up on the bed.",
    #     "bookname": "Genesis"
    # },
