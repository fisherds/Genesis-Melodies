import os
import shutil

# Assumes the file is only in comparisons folder.
# Removes the middle column
copy_file = False
filename = "chapter1"
destination_filename = f"public/chapters/{filename}.html"

# Assumes the file is here in this folder.
# inserts sections (cards) with title when the marker 
# Example:
# card - Day 1
insert_sections = False


# Assumes the file is here in this folder.
# Example:
# line_break
insert_line_breaks = False


# Adds a blank line after the verses in both the English and Hebrew text.
# Example:
# br
insert_my_br = True

if copy_file:
    source_filename = f"public/comparisons/{filename}.html"
    destination_filename = f"public/chapters/{filename}.html"

    # Copy the file
    shutil.copyfile(source_filename, destination_filename)

    # Remove lines with org-english-line div
    with open(destination_filename, "r") as infile:
        lines = infile.readlines()

    with open(destination_filename, "w") as outfile:
        for line in lines:
            if '<div class="org-english-line"' not in line:
                outfile.write(line)

if insert_sections:
    with open(destination_filename, "r") as infile:
        lines = infile.readlines()

    with open(destination_filename, "w") as outfile:
        for line in lines:
            if line.strip().startswith("card"):
                card_title = line.strip().split(' - ')[1]
                outfile.write(f"""</div>
              </div>
              <div id="" class="card">
                <h2 class="card-title">{card_title}</h2>
                <div class="interlinear-grid">
""")
            else:
                outfile.write(line)

def get_data_id(word):
    if "data-id" in word:
        chapter = word.split('data-id="')[1].split(':')[0]
        verse = word.split('data-id="')[1].split(':')[1].split('.')[0]
        index = word.split('data-id="')[1].split(':')[1].split('.')[1].split('"')[0]
        return int(chapter) * 1000000 + int(verse) * 1000 + int(index)
    return 0

# print(get_data_id('<span data-id="1:25.1" class="h430">Elohim</span>'))
# print(get_data_id('<div class="hebrew-line"><span data-id="1:25.0" class="h6213">וַיַּ֣עַשׂ</span>'))

def write_line_carefully(line, class_name, outfile):
    if f'<div class="{class_name}">' in line:
        outfile.write(f'                  {line.strip()}</div>\n')
    elif '</div>' in line:
        outfile.write(f'                  <div class="{class_name}">{line.strip()}\n')
    else:
        outfile.write(f'                  <div class="{class_name}">{line.strip()}</div>\n')


def write_split_lines(english_words, hebrew_words, outfile):
    english_line = ""
    hebrew_line = ""
    highest_id = 0
    while len(english_words) > 0:
        word = english_words.pop(0)
        if word.strip() == "line_break":
            write_line_carefully(english_line, "english-line", outfile)
            hebrew_word = "" # so that the final word is available after the loop
            while len(hebrew_words) > 0:
                hebrew_word = hebrew_words.pop(0)
                if "data-id" in hebrew_word:
                    current_id = get_data_id(hebrew_word)
                    if current_id > highest_id:
                        hebrew_line = hebrew_line[:-6] # removes the last '<span '
                        break
                hebrew_line += hebrew_word + " "

            write_line_carefully(hebrew_line, "hebrew-line", outfile)
            outfile.write('\n')
            english_line = ""
            hebrew_line = "<span " + hebrew_word + " "
            continue
        
        if "data-id" in word:
            highest_id = get_data_id(word)
            
        english_line += word + " "

    write_line_carefully(english_line, "english-line", outfile)
    write_line_carefully("<span " + hebrew_word + " " + " ".join(hebrew_words), "hebrew-line", outfile)

if insert_line_breaks:

    # Copy the file to make a backup (note, for this to be useful you should do a git commit after running this script)
    shutil.copyfile(destination_filename, f"public/chapters/{filename}_line_break_backup.html")

    with open(destination_filename, "r") as infile:
        lines = infile.readlines()

    # destination_filename = f"public/chapters/{filename}_line_break.html"  # for development purposes don't mess with the original file at all.
    with open(destination_filename, "w") as outfile:
        english_words = []
        hebrew_words = []
        splits_coming = False
        for k in range(len(lines)):
            line = lines[k]
            if '<div class="english-line">' in line and " line_break " in line:
                english_words = line.split(" ")
                splits_coming = True
                continue

            if '<div class="hebrew-line">' in line and splits_coming:
                hebrew_words = line.split(" ")
                splits_coming = False
                write_split_lines(english_words, hebrew_words, outfile)                        
                continue
            if not splits_coming:
                outfile.write(line)

