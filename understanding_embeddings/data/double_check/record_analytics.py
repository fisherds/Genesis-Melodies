#!/usr/bin/env python3
"""
Analytics script to analyze record files and generate CSV files with:
- record id
- title
- number of Hebrew words
- number of English words
- number of Tokens (Hebrew ST)
- number of Tokens (BERiT)
- number of Tokens (English)
"""

import json
import csv
from pathlib import Path
from transformers import RobertaTokenizerFast
from sentence_transformers import SentenceTransformer

# Model names
HEBREW_ST_MODEL = "odunola/sentence-transformers-bible-reference-final"
BERIT_MODEL = "gngpostalsrvc/BERiT"
ENGLISH_ST_MODEL = "sentence-transformers/all-mpnet-base-v2"


def count_words(text):
    """Count words by splitting on whitespace."""
    if not text:
        return 0
    return len(text.split())


def count_tokens_berit(text, tokenizer):
    """Count tokens using BERiT tokenizer (for Hebrew)."""
    if not text:
        return 0
    encoded = tokenizer(text, return_tensors='pt', truncation=False)
    return encoded['input_ids'].shape[1]


def count_tokens_sentence_transformer(text, model):
    """Count tokens using SentenceTransformer tokenizer."""
    if not text:
        return 0
    # SentenceTransformer models have a tokenizer attribute
    encoded = model.tokenizer(text, return_tensors='pt', truncation=False)
    return encoded['input_ids'].shape[1]


def analyze_records(records_file, output_csv, hebrew_st_model, berit_tokenizer, english_model):
    """
    Analyze records and write to CSV.
    
    Args:
        records_file: Path to JSON records file
        output_csv: Path to output CSV file
        hebrew_st_model: Hebrew SentenceTransformer model
        berit_tokenizer: BERiT tokenizer
        english_model: English SentenceTransformer model
    """
    print(f"\nAnalyzing {records_file.name}...")
    
    with open(records_file, 'r', encoding='utf-8') as f:
        records = json.load(f)
    
    rows = []
    
    for record in records:
        record_id = record.get('id', '')
        title = record.get('title', '')
        hebrew_text = record.get('hebrew', '')
        english_text = record.get('text', '')
        
        # Count words
        hebrew_words = count_words(hebrew_text)
        english_words = count_words(english_text)
        
        # Count tokens using all three models
        hebrew_st_tokens = count_tokens_sentence_transformer(hebrew_text, hebrew_st_model)
        berit_tokens = count_tokens_berit(hebrew_text, berit_tokenizer)
        english_tokens = count_tokens_sentence_transformer(english_text, english_model)
        
        rows.append({
            'record id': record_id,
            'title': title,
            'number of Hebrew words': hebrew_words,
            'number of English words': english_words,
            'number of Tokens (Hebrew ST)': hebrew_st_tokens,
            'number of Tokens (BERiT)': berit_tokens,
            'number of Tokens (English)': english_tokens
        })
    
    # Write to CSV
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    
    print(f"  ✓ Wrote {len(rows)} records to {output_csv}")
    
    # Calculate averages
    if rows:
        avg_hebrew_words = sum(r['number of Hebrew words'] for r in rows) / len(rows)
        avg_english_words = sum(r['number of English words'] for r in rows) / len(rows)
        avg_hebrew_st_tokens = sum(r['number of Tokens (Hebrew ST)'] for r in rows) / len(rows)
        avg_berit_tokens = sum(r['number of Tokens (BERiT)'] for r in rows) / len(rows)
        avg_english_tokens = sum(r['number of Tokens (English)'] for r in rows) / len(rows)
        
        print(f"  Average Hebrew words: {avg_hebrew_words:.2f}")
        print(f"  Average English words: {avg_english_words:.2f}")
        print(f"  Average Tokens (Hebrew ST): {avg_hebrew_st_tokens:.2f}")
        print(f"  Average Tokens (BERiT): {avg_berit_tokens:.2f}")
        print(f"  Average Tokens (English): {avg_english_tokens:.2f}")
    
    return rows


def main():
    """Main function to analyze all three record files."""
    # Get script directory and data directory
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent
    records_dir = data_dir / 'records'
    output_dir = script_dir
    
    # Record files
    record_files = [
        ('quilt_piece_records.json', 'quilt_piece_analytics.csv'),
        ('pericope_records.json', 'pericope_analytics.csv'),
        ('verse_records.json', 'verse_analytics.csv'),
        ('agentic_berit_records.json', 'agentic_berit_analytics.csv'),
        ('agentic_hebrew_st_records.json', 'agentic_hebrew_st_analytics.csv'),
        ('agentic_english_st_records.json', 'agentic_english_st_analytics.csv')
    ]
    
    print("=" * 60)
    print("Record Analytics Script")
    print("=" * 60)
    print("\nLoading tokenizers...")
    
    # Load Hebrew SentenceTransformer model
    print("  Loading Hebrew SentenceTransformer...")
    hebrew_st_model = SentenceTransformer(HEBREW_ST_MODEL)
    print("  ✓ Hebrew ST model loaded")
    
    # Load BERiT tokenizer
    print("  Loading BERiT tokenizer...")
    berit_tokenizer = RobertaTokenizerFast.from_pretrained(BERIT_MODEL)
    print("  ✓ BERiT tokenizer loaded")
    
    # Load English SentenceTransformer model
    print("  Loading English SentenceTransformer...")
    english_model = SentenceTransformer(ENGLISH_ST_MODEL)
    print("  ✓ English ST model loaded")
    
    # Analyze each record file
    all_results = {}
    for record_file_name, output_csv_name in record_files:
        record_file = records_dir / record_file_name
        output_csv = output_dir / output_csv_name
        
        if not record_file.exists():
            print(f"  ⚠ Warning: {record_file} not found, skipping...")
            continue
        
        rows = analyze_records(record_file, output_csv, hebrew_st_model, berit_tokenizer, english_model)
        all_results[record_file_name] = rows
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for record_file_name, rows in all_results.items():
        if rows:
            print(f"\n{record_file_name}:")
            print(f"  Total records: {len(rows)}")
            avg_hebrew = sum(r['number of Hebrew words'] for r in rows) / len(rows)
            avg_english = sum(r['number of English words'] for r in rows) / len(rows)
            avg_hebrew_st = sum(r['number of Tokens (Hebrew ST)'] for r in rows) / len(rows)
            avg_berit = sum(r['number of Tokens (BERiT)'] for r in rows) / len(rows)
            avg_english_tokens = sum(r['number of Tokens (English)'] for r in rows) / len(rows)
            print(f"  Average Hebrew words: {avg_hebrew:.2f}")
            print(f"  Average English words: {avg_english:.2f}")
            print(f"  Average Tokens (Hebrew ST): {avg_hebrew_st:.2f}")
            print(f"  Average Tokens (BERiT): {avg_berit:.2f}")
            print(f"  Average Tokens (English): {avg_english_tokens:.2f}")
    
    print("\n✓ Done! CSV files written to:", output_dir)


if __name__ == '__main__':
    main()

