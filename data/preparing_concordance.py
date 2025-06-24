# Starting point from https://github.com/tahmmee/interlinear_bibledata/blob/master/interlinear/bible.tar.gz
# [
#     {
#         "verse": [
#             {
#                 "i": 0,
#                 "text": "In the beginning",
#                 "word": "בְּרֵאשִׁ֖ית",
#                 "number": "h7225"
#             },
#
# Goal:
#   {
#     "id": "469",
#     "hebrew_word": "לַֽעֲשֽׂוֹת",
#     "strongs_number": "h6213",
#     "definition": "Original: <b><he>עשׂה</he></b> <p />Transliteration: <b>‛âśâh</b> <p />Phonetic: <b>aw-saw'</b> <p class=\"bdb_def\">Definition:</p><ol><li>to do, fashion, accomplish, make<ol type='a'><li>(Qal)<ol><li>to do, work, make, produce<ol type='a'><li>to do</li><li>to work</li><li>to deal (with)</li><li>to act, act with effect, effect</li></ol><li>to make<ol type='a'><li>to make</li><li>to produce</li><li>to prepare</li><li>to make (an offering)</li><li>to attend to, put in order</li><li>to observe, celebrate</li><li>to acquire (property)</li><li>to appoint, ordain, institute</li><li>to bring about</li><li>to use</li><li>to spend, pass</li></ol></li></ol><li>(Niphal)<ol><li>to be done</li><li>to be made</li><li>to be produced</li><li>to be offered</li><li>to be observed</li><li>to be used</li></ol><li>(Pual) to be made</li></ol><li>(Piel) to press, squeeze</li></ol> <p />",
#     "transliteration": "ʻâsâh",
#     "gloss_transliteration": "laʿăśôt",
#     "lexeme": "עשה",
#     "pronunciation": "aw-saw'",
#     "short_definition": "accomplish",
#     "english_text": "and made",
#     "chapter": 2,
#     "verse": 3,
#     "word_index": 15,
#   }

# Step #1: Run the first_concordance_scripts.py to generate the initial concordance data.
# Inputs: genesis.json, greek_hebrew_dictionary.json, hebrew.json
# Outputs: genesis_concordance.json
#
#   {
#     "id": "1:1.0",
#     "chapter": 1,
#     "verse": 1,
#     "word_index": 0,
#     "hebrew_word": "בְּרֵאשִׁ֖ית",
#     "english_text": "In the beginning",
#     "strongs_number": "h7225",
#     "definition": "Original: <b><he>ראשׁית</he></b> <p />Transliteration: <b>rê'shı̂yth</b> <p />Phonetic: <b>ray-sheeth'</b> <p class=\"bdb_def\"><b>BDB Definition</b>:</p><ol><li>first, beginning, best, chief<ol type='a'><li>beginning</li><li>first</li><li>chief</li><li>choice part</li></ol></li></ol> <p />",
#     "transliteration": "rêʼshîyth",
#     "lexeme": "ראשית",
#     "pronunciation": "ray-sheeth'",
#     "short_definition": "beginning",
#     "words": "beginning, chief(-est), first(-fruits) (part, time), principal thing"
#   },
#
# missing:     "gloss_transliteration": "laʿăśôt",


# Step #2: Run hebrew_transliterate.js just to add the gloss_transliteration field.
# Inputs: genesis_concordance.json
# Outputs: genesis_concordance_transliterated.json

# Step #3: Run the page_generator.py to create the HTML pages.
# Step #4: Run this file to convert the list to a map.
