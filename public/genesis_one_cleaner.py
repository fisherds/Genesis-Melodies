import re

input_path = "public/genesis_one.json"
output_path = "public/genesis_one_edit.json"

with open(input_path, "r", encoding="utf-8") as infile, open(output_path, "w", encoding="utf-8") as outfile:
    for line in infile:
        # Remove 'Origin:' up to the last '",'
        new_line = re.sub(r'Origin:.*?",', '",', line)
        outfile.write(new_line)