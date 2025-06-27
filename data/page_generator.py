import json

def load_concordance():
    try:
      with open('data/genesis_concordance_transliterated.json', 'r') as f:
        genesis_concordance = json.load(f)
      return genesis_concordance
    except FileNotFoundError:
      print("Error: The file was not found.")
      return None
    except json.JSONDecodeError:
      print("Error: Could not decode JSON from the file.")
      return None
    except Exception as e:
      print(f"An error occurred: {e}")
      return None
from collections import defaultdict

def get_improved_translation(chapter_number, bible_project_translation, niv_translation):
    improved_translation = []
    for entry in bible_project_translation:
        if entry['chapter'] == chapter_number:
            improved_translation.append(entry['text'])
    
    # Add NIV translation for the same verses
    for entry in niv_translation:
        if entry['chapter'] == chapter_number:
            improved_translation.append(entry['text'])
    
    return improved_translation

def generate_chapter_html(chapter_number, concordance_data, improved_translation_list):
    chapter_data = [entry for entry in concordance_data if entry['chapter'] == chapter_number]
    verse_data = defaultdict(list)
    for entry in chapter_data:
        verse_data[entry['verse']].append(entry)

    chapter_html = ""
    next_verse = 0
    for verse_number, words in verse_data.items():
        chapter_html += f'                  <div class="english-line"><span class="verse">{verse_number + 1}</span>{improved_translation_list[next_verse]}</div>\n'
        next_verse += 1
        english_line = ""
        hebrew_line = ""
        for word in words:
            english_word = word["english_text"].strip()
            if english_word != "x":
                english_line += f'<span data-id="{word["id"]}" class="{word["strongs_number"]}">{english_word}</span> '
            hebrew_line += f'<span data-id="{word["id"]}" class="{word["strongs_number"]}">{word["hebrew_word"]}</span> '
        chapter_html += f'                  <div class="org-english-line"><span class="verse">{verse_number}</span>{english_line.strip()}</div>\n'
        chapter_html += f'                  <div class="hebrew-line">{hebrew_line.strip()}</div>\n\n'

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Genesis {chapter_number}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&family=Noto+Sans+Hebrew:wght@400;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="main.css">
</head>
<body class="bg-gray-100 text-gray-800">
    <div id="page-container">
        <div id="main-content" class="p-2 sm:p-4">
          <header class="text-center mb-10">
              <h1 class="text-4xl font-bold text-gray-900">Some Literary Unit</h1>
              <p class="text-2xl text-gray-700"><i>A BibleProject Translation</i></p>
              <p class="text-lg text-gray-600 mt-2">Genesis {chapter_number}</p>
          </header>

          <main class="grid grid-cols-1 gap-6">
              <div id="title" class="card">
                <h2 class="card-title"> Chapter {chapter_number}</h2>
                <div class="interlinear-grid">
{chapter_html}
                </div>
              </div>
              <div id="transliteration-tooltip" class="transliteration-tooltip"></div>
          </main>

          <footer class="text-center mt-10 text-gray-500 text-sm">
              <p>Fun Genesis interlinear based on the <a href="https://documents.bibleproject.com/classroom/instructor-translation/adam-to-noah-instructor-translation.pdf">BibleProject translation</a>.</p>
          </footer>
        </div>
        <div id="drawer">        
        </div>
    </div>
    <script src="main.js"></script>
</body>
</html>
"""
    filename = f"public/generated/chapter{chapter_number}.html"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_template)
        return f"Successfully saved HTML to {filename}"
    except IOError as e:
        return f"Error saving HTML to {filename}: {e}"


if __name__ == "__main__":
    genesis_concordance = load_concordance()
    # print(genesis_concordance[0])

    # Load the .json files bible_project_translation.json and niv_translation.json
    # then pass that data into the generate_chapter_html function.

    with open('data/bible_project_translation.json', 'r', encoding='utf-8') as f:
        bible_project_translation = json.load(f)
    with open('data/niv_translation.json', 'r', encoding='utf-8') as f:
        niv_translation = json.load(f)

    # chapter_number = 1
    # improved_translation_list = get_improved_translation(chapter_number, bible_project_translation, niv_translation)
    # print(improved_translation_list)
    # generate_chapter_html(1, genesis_concordance, improved_translation_list)

    # Generate HTML for each chapter
    chapters = set(entry['chapter'] for entry in genesis_concordance)
    for chapter in sorted(chapters):
        improved_translation_list = get_improved_translation(chapter, bible_project_translation, niv_translation)
        result = generate_chapter_html(chapter, genesis_concordance, improved_translation_list)
        print(result)