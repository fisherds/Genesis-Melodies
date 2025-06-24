import json

class HebrewWord:
    def __init__(self, hebrew_word, english_text, chapter, verse, word_index, strongs_number):
        self.hebrew_word = hebrew_word.rstrip(",")
        self.english_text = english_text
        self.chapter = chapter
        self.verse = verse
        self.word_index = word_index
        self.id = f"{chapter}:{verse}.{word_index}"
        self.strongs_number = strongs_number

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
            i = json_word["i"]  # really not that useful, similar to word_index but different for repeated words (i becomes the final word_index)
            strongs_number = json_word["number"]
            hebrew_word = HebrewWord(hebrew_word, english_text, current_chapter, current_verse, word_index, strongs_number)
            hebrew_words.append(hebrew_word)
            word_index += 1

    return hebrew_words


print("Loading Genesis Concordance")
all_words = load_concordance()
# So far we have...
        # self.hebrew_word = hebrew_word.rstrip(",")
        # self.english_text = english_text
        # self.chapter = chapter
        # self.verse = verse
        # self.word_index = word_index
        # self.id = f"{chapter}:{verse}.{word_index}"
        # self.strongs_number = strongs_number

# print_range(all_words, ch=1, v=2, end_ch=1, end_v=4)

# Next add the greek_hebrew_dictionary.json data
        # "topic": "h6060",
        # "definition": "Original: <b><he>\u05e2\u05e0\u05e7</he></b> <p />Transliteration: <b>\u201ba\u0302na\u0302q</b> <p />Phonetic: <b>aw-nawk'</b> <p class=\"bdb_def\"><b>BDB Definition</b>:</p><ol><li>necklace, neck-pendant</li><li>(TWOT) neck</li></ol> <p />Origin: from <a href='S:H6059'>H6059</a> <p />TWOT entry: <a class=\"T\" href=\"S:1658 - 'nq\">1658b</a>,<a class=\"T\" href=\"S:1658 - 'nq\">1658a</a> <p />Part(s) of speech: Noun Masculine ",
        # "lexeme": "\u05e2\u05e0\u05e7",
        # "transliteration": "\u02bb\u00e2n\u00e2q",
        # "pronunciation": "aw-nawk'",
        # "short_definition": "chain"


def trim_definition(definition):
    """
    Removes 'Origin:' and everything after it from the input string.
    """
    origin_index = definition.find('Origin:')
    if origin_index != -1:
        return definition[:origin_index].rstrip()
    return definition


def add_greek_hebrew_dictionary_data(all_words, print_amount=0):
    # Load the Greek-Hebrew dictionary
    try:
        with open('data/greek_hebrew_dictionary.json', 'r', encoding='utf-8') as f:
            greek_hebrew_json = json.load(f)
    except FileNotFoundError:
        print("Error: greek_hebrew_dictionary.json file not found.")
        greek_hebrew_json = {}
    except json.JSONDecodeError:
        print("Error: Could not decode JSON from greek_hebrew_dictionary.json.")
        greek_hebrew_json = {}
    except Exception as e:
        print(f"An error occurred while loading greek_hebrew_dictionary.json: {e}")

    greek_hebrew_dictionary = {item['topic']: item for item in greek_hebrew_json}

    genesis_data = []
    print_counter = 0

    for word in all_words:
        # Find definition from hebrew dictionary and add these fields
        definition =  "Definition not found"
        transliteration = ""
        lexeme = ""
        pronunciation = ""
        short_definition = ""

        if word.strongs_number in greek_hebrew_dictionary:
            definition = greek_hebrew_dictionary[word.strongs_number]['definition']
            if definition:
                definition = trim_definition(definition)
            transliteration = greek_hebrew_dictionary[word.strongs_number]['transliteration']
            lexeme = greek_hebrew_dictionary[word.strongs_number]['lexeme']
            pronunciation = greek_hebrew_dictionary[word.strongs_number]['pronunciation']
            short_definition = greek_hebrew_dictionary[word.strongs_number]['short_definition']
            
        
        new_data = {
            "id": word.id,
            "chapter": word.chapter,
            "verse": word.verse,
            "word_index": word.word_index,
            "hebrew_word": word.hebrew_word,
            "english_text": word.english_text,
            "strongs_number": word.strongs_number,
            # New
            "definition": definition,
            "transliteration": transliteration,
            "lexeme": lexeme,
            "pronunciation": pronunciation,
            "short_definition": short_definition
        }
        if print_counter < print_amount:       
                print(new_data)         
                print_counter += 1
        genesis_data.append(new_data)
    return genesis_data


print("Adding Greek-Hebrew Dictionary Data")
genesis_concordance = add_greek_hebrew_dictionary_data(all_words)


def add_hebrew_dictionary_data(all_words, print_amount=0):
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

    hebrew_dictionary = {item['strongs']: item for item in hebrew_json}

    genesis_data = []
    print_counter = 0
    word_counter = 0

    for word in all_words:
        # Find definition from hebrew dictionary and add these fields
        words = ""

        if word['strongs_number'] in hebrew_dictionary:
            words = hebrew_dictionary[word['strongs_number']]['word']

        new_data = {
            "id": word['id'],
            "chapter": word['chapter'],
            "verse": word['verse'],
            "word_index": word['word_index'],
            "hebrew_word": word['hebrew_word'],
            "english_text": word['english_text'],
            "strongs_number": word['strongs_number'],
            "definition": word['definition'],
            "transliteration": word['transliteration'],
            "lexeme": word['lexeme'],
            "pronunciation": word['pronunciation'],
            "short_definition": word['short_definition'],
            # New
            "words": words
        }
        if print_counter < print_amount:
            print(new_data)
            print_counter += 1
        genesis_data.append(new_data)
    return genesis_data


print("Adding Hebrew Dictionary Data")
genesis_concordance_with_words = add_hebrew_dictionary_data(genesis_concordance, print_amount=1)


if True:
    output_file_path = 'data/genesis_concordance.json'
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(genesis_concordance_with_words, f, ensure_ascii=False, indent=2)
        print(f"Successfully wrote data to {output_file_path}")
    except Exception as e:
        print(f"Error writing to {output_file_path}: {e}")