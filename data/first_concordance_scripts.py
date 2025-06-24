import json

class HebrewWord:
    def __init__(self, hebrew_word, english_text, chapter, verse, word_index, strongs_number, strongs_word, strongs_data):
        """
         Creates a Hebrew Word using data available from the _concordance.json (plus dictionary file optional addition).
         """
        self.hebrew_word = hebrew_word.rstrip(",")
        self.english_text = english_text
        self.chapter = chapter
        self.verse = verse
        self.word_index = word_index
        self.id = f"{chapter}:{verse}.{word_index}"
        self.strongs_number = strongs_number.upper()
        self.strongs_word = strongs_word  # Unused at present
        self.strongs_data = strongs_data  # Unused at present

    @property
    def verse_index(self):
        return f"{self.chapter}:{self.verse}.{self.word_index}"

    def __repr__(self):
        return f"{self.hebrew_word} - {self.english_text} ({self.id}) {self.strongs_number}"


def print_range(all_words: list[HebrewWord], ch, v, end_ch=None, end_v=None):
    if end_ch is None:
        end_ch = ch
    if end_v is None:
        end_v = v
    start_id = ch * 1000 + v
    end_id = end_ch * 1000 + end_v
    for word in all_words:
        verse_id = word.chapter * 1000 + word.verse
        if start_id <= verse_id <= end_id:
            print(word)

def load_concordance():
    try:
      with open('data/genesis.json', 'r') as f:
        genesis_concordance = json.load(f)
    except FileNotFoundError:
      print("Error: The file was not found.")
    except json.JSONDecodeError:
      print("Error: Could not decode JSON from the file.")
    except Exception as e:
      print(f"An error occurred: {e}")

    hebrew_words = []
    for single_verse in genesis_concordance:
        current_chapter = int(single_verse["id"][2:5])
        current_verse = int(single_verse["id"][5:])
        words = single_verse["verse"]

        word_index = 0
        for json_word in words:
            hebrew_word = json_word["word"]
            english_text = json_word["text"]
            if english_text is None or english_text == "":
                english_text = " x "
            # chapter = chapter
            # verse = verse
            i = json_word["i"]  # really not that useful, similar to word_index but different for repeated words (i becomes the final word_index)
            strongs_number = json_word["number"]
            # strongs_word = strongs_word
            # strongs_data = strongs_data
            hebrew_word = HebrewWord(hebrew_word, english_text, current_chapter, current_verse, word_index, strongs_number, None, None)
            hebrew_words.append(hebrew_word)
            word_index += 1

    return hebrew_words


print("Loading Genesis Concordance")
all_words = load_concordance()
# print_range(all_words, ch=1, v=2, end_ch=1, end_v=4)

def add_hebrew_dictionary_data(all_words):
    # Load the Hebrew dictionary
    try:
        with open('data/hebrew.json', 'r', encoding='utf-8') as f:
            hebrew_json = json.load(f)
    except FileNotFoundError:
        print("Error: hebrew.json file not found.")
        hebrew_json = {}
    except json.JSONDecodeError:
        print("Error: Could not decode JSON from hebrew.json.")
        hebrew_json = {}
    except Exception as e:
        print(f"An error occurred while loading hebrew.json: {e}")

    hebrew_dictionary = {item['topic']: item for item in hebrew_json}

    genesis_data = []
    print_counter = 0
    word_counter = 0

    for word in all_words:
        # Find definition from hebrew dictionary and add these fields
        definition =  "Definition not found"
        transliteration = ""
        lexeme = ""
        pronunciation = ""
        short_definition = ""
        words = ""

        if word.strongs_number in hebrew_dictionary:
            definition = hebrew_dictionary[word.strongs_number]['definition']
            transliteration = hebrew_dictionary[word.strongs_number]['transliteration']
            lexeme = hebrew_dictionary[word.strongs_number]['lexeme']
            pronunciation = hebrew_dictionary[word.strongs_number]['pronunciation']
            short_definition = hebrew_dictionary[word.strongs_number]['short_definition']
            words = hebrew_dictionary[word.strongs_number]['word']
            if print_counter < 5:
                print(word)
                print_counter += 1

        word_counter += 1
        genesis_data.append({
            "id": word.id,
            "chapter": word.chapter,
            "verse": word.verse,
            "word_index": word.word_index,
            "hebrew_word": word.hebrew_word,
            "english_text": word.english_text,
            "strongs_number": word.strongs_number,
            "definition": definition,
            "transliteration": transliteration,
            "lexeme": lexeme,
            "pronunciation": pronunciation,
            "short_definition": short_definition,
            "words": words
        })


print("Adding Hebrew Dictionary Data")
genesis_concordance = add_hebrew_dictionary_data(all_words)


if False:
    output_file_path = 'data/genesis_concordance.json'
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(genesis_concordance, f, ensure_ascii=False, indent=2)
        print(f"Successfully wrote data to {output_file_path}")
    except Exception as e:
        print(f"Error writing to {output_file_path}: {e}")