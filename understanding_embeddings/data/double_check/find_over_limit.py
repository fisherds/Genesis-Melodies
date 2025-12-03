#!/usr/bin/env python3
"""Find records that exceed token limits for all three models."""

import csv
from pathlib import Path

# Model limits
LIMITS = {
    'BERiT': 128,
    'Hebrew ST': 512,
    'English ST': 384  # Note: English ST uses all-mpnet-base-v2 which has max_seq_length of 384
}

# Analytics files to check
ANALYTICS_FILES = [
    ('pericope_analytics.csv', 'Pericopes'),
    ('agentic_berit_analytics.csv', 'Agentic BERiT'),
    ('agentic_hebrew_st_analytics.csv', 'Agentic Hebrew ST'),
    ('agentic_english_st_analytics.csv', 'Agentic English ST')
]

script_dir = Path(__file__).parent

for csv_file, label in ANALYTICS_FILES:
    csv_path = script_dir / csv_file
    if not csv_path.exists():
        print(f"⚠️  {csv_file} not found, skipping...\n")
        continue
    
    print(f"\n{'=' * 100}")
    print(f"{label} - Records exceeding limits:")
    print(f"{'=' * 100}")
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        over_limit = []
        for row in reader:
            berit_tokens = int(row.get('number of Tokens (BERiT)', 0))
            hebrew_st_tokens = int(row.get('number of Tokens (Hebrew ST)', 0))
            english_tokens = int(row.get('number of Tokens (English)', 0))
            
            # Check all three limits
            berit_over = berit_tokens > LIMITS['BERiT']
            hebrew_st_over = hebrew_st_tokens > LIMITS['Hebrew ST']
            english_st_over = english_tokens > LIMITS['English ST']
            
            if berit_over or hebrew_st_over or english_st_over:
                over_limit.append({
                    'id': row['record id'],
                    'title': row['title'],
                    'berit': berit_tokens,
                    'hebrew_st': hebrew_st_tokens,
                    'english': english_tokens,
                    'berit_over': berit_over,
                    'hebrew_st_over': hebrew_st_over,
                    'english_st_over': english_st_over
                })
    
    if not over_limit:
        print(f"✅ All records are within limits!")
    else:
        print(f"\n{'Record ID':<20} {'BERiT':<8} {'Heb ST':<8} {'Eng ST':<8} {'Title'}")
        print('-' * 100)
        for item in sorted(over_limit, key=lambda x: max(x['berit'], x['hebrew_st'], x['english']), reverse=True):
            berit_mark = '❌' if item['berit_over'] else '✅'
            hebrew_mark = '❌' if item['hebrew_st_over'] else '✅'
            english_mark = '❌' if item['english_st_over'] else '✅'
            print(f"{item['id']:<20} {item['berit']:<4} {berit_mark:<3} {item['hebrew_st']:<4} {hebrew_mark:<3} {item['english']:<4} {english_mark:<3} {item['title']}")
        
        print(f"\n📊 Summary:")
        berit_count = sum(1 for item in over_limit if item['berit_over'])
        hebrew_st_count = sum(1 for item in over_limit if item['hebrew_st_over'])
        english_st_count = sum(1 for item in over_limit if item['english_st_over'])
        print(f"  BERiT (>128): {berit_count} records")
        print(f"  Hebrew ST (>512): {hebrew_st_count} records")
        print(f"  English ST (>384): {english_st_count} records")
        print(f"  Total records over limit: {len(over_limit)}")

print(f"\n{'=' * 100}")
print("Note: Limits are BERiT=128, Hebrew ST=512, English ST=384 tokens")

