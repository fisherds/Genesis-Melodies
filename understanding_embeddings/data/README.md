# Data Files

This directory contains data files and scripts for generating decoder ring records.

## Files

- `decoder_ring_divisions.txt` - Custom chunking of Genesis 1-11 into 50 thematic divisions
- `decoder_ring_record_generator.py` - Script to generate JSON records from the divisions
- `bp_translation_gen_1_25.txt` - BibleProject English translation (Genesis 1-25)
- `WLCa.json` - WLC (Westminster Linengrad Codex) Hebrew text with Strong's numbers
- `decoder_ring_records.json` - Generated output (created by running the generator script)

## Record Structure

Each record contains:
- `id` - Unique identifier (e.g., "decoder_ring_001", "decoder_ring_002", etc.)
- `title` - Thematic title from decoder_ring_divisions.txt
- `verses` - Array of {chapter, verse} objects
- `text` - English text from BP translation (verses separated by spaces)
- `hebrew` - Hebrew text from WLCa (verses separated by spaces)
- `strongs` - Strong's numbers formatted as "h7453" (separated by spaces)

## Usage

Run the generator script from the parent directory:

```bash
python understanding_embeddings/data/decoder_ring_record_generator.py
```

This will create `decoder_ring_records.json` with all 50 records.

