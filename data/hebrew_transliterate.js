// transliterate.js

// Import the necessary modules
// The 'fs' module is used for file system operations, like reading and writing files.
// The 'hebrew-transliteration' module is used to transliterate the Hebrew text.
const fs = require('fs');
const { transliterate } = require('hebrew-transliteration');

// Define the input and output file names
const inputFile = './genesis_concordance.json';
const outputFile = './genesis_concordance_transliterated.json';

// Read the input JSON file
fs.readFile(inputFile, 'utf8', (err, data) => {
    // If there's an error reading the file, log it to the console and exit
    if (err) {
        console.error("Error reading the input file:", err);
        return;
    }

    try {
        // Parse the JSON data from the file
        const jsonData = JSON.parse(data);

        // Map over the JSON data to add the new 'simple_transliteration' field
        const transliteratedData = jsonData.map(wordInfo => {
            const hebrewWord = wordInfo.hebrew_word;
            // Transliterate the Hebrew word. 
            // The second argument 'false' keeps the vowel pointing in the transliteration.
            const simpleTransliteration = transliterate(hebrewWord, false);
            
            // Return a new object with all the old info plus the new transliteration
            return {
                ...wordInfo,
                gloss_transliteration: simpleTransliteration
            };
        });

        // Write the updated data to the output file
        // The 'JSON.stringify' function is used to convert the JavaScript object back to a JSON string.
        // The 'null, 2' arguments are used to format the JSON file with an indentation of 2 spaces for readability.
        fs.writeFile(outputFile, JSON.stringify(transliteratedData, null, 2), 'utf8', (err) => {
            if (err) {
                console.error("Error writing to the output file:", err);
                return;
            }
            console.log(`Successfully created ${outputFile} with the transliterated data.`);
        });

    } catch (parseError) {
        console.error("Error parsing JSON data:", parseError);
    }
});
