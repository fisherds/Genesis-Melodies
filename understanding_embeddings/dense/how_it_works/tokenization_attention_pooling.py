#!/usr/bin/env python3
"""
Deep dive into tokenization, attention, and pooling for Genesis 1:1 and 1:3.

This script extracts and analyzes:
1. Initial token embeddings (before attention)
2. Post-attention token embeddings
3. Pooling process and final embeddings

For Hebrew models (BERiT, hebrew_st) and English model (english_st).
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from understanding_embeddings.shared.utils import ensure_correct_working_directory
ensure_correct_working_directory()

import os
import csv
import numpy as np
import torch
from transformers import RobertaModel, RobertaTokenizerFast
from sentence_transformers import SentenceTransformer

# Create output directory
OUTPUT_DIR = Path(__file__).parent / 'tokens_and_pooling'
OUTPUT_DIR.mkdir(exist_ok=True)

# Full verse texts
GENESIS_1_1_HEBREW = "בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃"
GENESIS_1_1_ENGLISH = "In the beginning, Elohim created the skies and the land,"
GENESIS_1_3_HEBREW = "וַיֹּ֥אמֶר אֱלֹהִ֖ים יְהִ֣י א֑וֹר וַֽיְהִי־אֽוֹר׃"
GENESIS_1_3_ENGLISH = "and Elohim said, \"Let there be light\" and there was light."

print("=" * 80)
print("Tokenization, Attention, and Pooling Analysis")
print("=" * 80)
print()

# ============================================================================
# MODEL LOADING
# ============================================================================

print("Loading models...")
print()

# BERiT model
print("Loading BERiT model...")
BERIT_MODEL_NAME = "gngpostalsrvc/BERiT"
tokenizer_berit = RobertaTokenizerFast.from_pretrained(BERIT_MODEL_NAME)
model_berit = RobertaModel.from_pretrained(BERIT_MODEL_NAME)
model_berit.eval()
print("✓ BERiT model loaded!")
print()

# Hebrew SentenceTransformer
print("Loading Hebrew SentenceTransformer model...")
model_hebrew_st = SentenceTransformer('odunola/sentence-transformers-bible-reference-final', device='cpu')
model_hebrew_st.eval()
print("✓ Hebrew SentenceTransformer model loaded!")
print()

# English SentenceTransformer
print("Loading English SentenceTransformer model...")
model_english_st = SentenceTransformer('sentence-transformers/all-mpnet-base-v2', device='cpu')
model_english_st.eval()
print("✓ English SentenceTransformer model loaded!")
print()

# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def analyze_berit(text, prefix):
    """
    Analyze Hebrew text with BERiT model.
    
    Args:
        text: Hebrew text to analyze
        prefix: Prefix for output filenames (e.g., 'gen1' or 'gen13')
    
    Returns:
        tuple: (final_embedding, tokens, initial_embeddings, post_attention_embeddings, token_display)
    """
    model_name = 'berit'
    print(f"Analyzing Hebrew text with BERiT: {text[:50]}...")
    
    # Tokenize first without tensors to get offset mapping
    encoded_no_tensors = tokenizer_berit(
        text,
        padding=False,
        truncation=True,
        return_offsets_mapping=True,
        max_length=128
    )
    
    # Get offset mapping (list of (start, end) tuples)
    offset_mapping = encoded_no_tensors['offset_mapping']
    
    # Now tokenize with tensors for the model
    encoded = tokenizer_berit(
        text,
        padding=False,
        truncation=True,
        return_tensors='pt',
        max_length=128
    )
    
    input_ids = encoded['input_ids'][0]
    attention_mask = encoded['attention_mask'][0]
    tokens = tokenizer_berit.convert_ids_to_tokens(input_ids)
    
    # Map tokens to original text spans
    def get_original_text_span(token_idx, offset_map, original_text):
        if token_idx >= len(offset_map):
            return ""
        start, end = offset_map[token_idx]
        if start == 0 and end == 0:
            return tokens[token_idx]
        try:
            return original_text[start:end]
        except:
            return tokens[token_idx]
    
    token_display = []
    for i, token in enumerate(tokens):
        original_span = get_original_text_span(i, offset_mapping, text)
        if original_span and original_span != token and original_span.strip():
            token_display.append(f"{token} → {original_span}")
        else:
            token_display.append(token)
    
    # Get initial token embeddings
    with torch.no_grad():
        embeddings_layer = model_berit.embeddings
        token_embeddings = embeddings_layer.word_embeddings(input_ids)
        positions = torch.arange(0, len(input_ids), dtype=torch.long)
        max_pos = embeddings_layer.position_embeddings.num_embeddings
        positions = torch.clamp(positions, 0, max_pos - 1)
        position_embeddings = embeddings_layer.position_embeddings(positions)
        initial_embeddings = token_embeddings + position_embeddings
    
    # Save initial token embeddings
    filename = OUTPUT_DIR / f"{prefix}_{model_name}_initial_tokens.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        header = ['token_index', 'token_subword', 'original_text_span'] + [f'embedding_dim_{i}' for i in range(initial_embeddings.shape[1])]
        writer.writerow(header)
        for i, (token, token_disp, embedding) in enumerate(zip(tokens, token_display, initial_embeddings)):
            if ' → ' in token_disp:
                original_span = token_disp.split(' → ')[1]
            else:
                original_span = token_disp
            row = [i, token, original_span] + embedding.tolist()
            writer.writerow(row)
    print(f"  ✓ Saved initial tokens to {filename}")
    
    # Get post-attention embeddings
    seq_length = len(input_ids)
    position_ids = torch.arange(0, seq_length, dtype=torch.long).unsqueeze(0)
    
    with torch.no_grad():
        outputs = model_berit.forward(
            input_ids=input_ids.unsqueeze(0),
            attention_mask=attention_mask.unsqueeze(0),
            position_ids=position_ids
        )
        post_attention_embeddings = outputs.last_hidden_state[0]
    
    # Save post-attention token embeddings
    filename = OUTPUT_DIR / f"{prefix}_{model_name}_post_attention_tokens.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        header = ['token_index', 'token_subword', 'original_text_span'] + [f'embedding_dim_{i}' for i in range(post_attention_embeddings.shape[1])]
        writer.writerow(header)
        for i, (token, token_disp, embedding) in enumerate(zip(tokens, token_display, post_attention_embeddings)):
            if ' → ' in token_disp:
                original_span = token_disp.split(' → ')[1]
            else:
                original_span = token_disp
            row = [i, token, original_span] + embedding.tolist()
            writer.writerow(row)
    print(f"  ✓ Saved post-attention tokens to {filename}")
    
    # Pooling process
    attention_mask_expanded = attention_mask.unsqueeze(-1).expand(post_attention_embeddings.size()).float()
    sum_embeddings = torch.sum(post_attention_embeddings * attention_mask_expanded, dim=0)
    sum_mask = torch.clamp(attention_mask_expanded.sum(dim=0), min=1e-9)
    final_embedding = sum_embeddings / sum_mask
    
    # Save pooling details (columnar format: each token is a column)
    filename = OUTPUT_DIR / f"{prefix}_{model_name}_pooling.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Collect token contributions
        token_contributions = []
        token_numbers = []
        token_texts = []
        
        for i, (token, token_disp, embedding, mask_val) in enumerate(zip(tokens, token_display, post_attention_embeddings, attention_mask)):
            if mask_val > 0:  # Only non-padding tokens
                contribution = embedding * mask_val
                token_contributions.append(contribution.tolist())
                token_numbers.append(f"token_{i:02d}")
                if ' → ' in token_disp:
                    original_span = token_disp.split(' → ')[1]
                else:
                    original_span = token_disp
                token_texts.append(original_span)
        
        # Calculate sum of contributions (should match final_embedding * num_tokens for mean pooling)
        num_tokens = len(token_contributions)
        sum_of_contributions = sum_embeddings.tolist()  # This is the sum before dividing by mask
        
        # Build header: row labels column, then each token column, then final two columns
        header = [''] + token_numbers + ['FINAL_POOLED_EMBEDDING', 'SUM_OF_CONTRIBUTIONS']
        writer.writerow(header)
        
        # Row 1: Token number row
        row = ['Token number'] + token_numbers + ['FINAL_POOLED', 'SUM_OF_CONTRIBUTIONS']
        writer.writerow(row)
        
        # Row 2: Token text row
        row = ['Token text'] + token_texts + ['FINAL_POOLED_EMBEDDING', 'SUM_OF_CONTRIBUTIONS']
        writer.writerow(row)
        
        # Rows for each dimension
        num_dims = len(final_embedding)
        for dim_idx in range(num_dims):
            row = [f'Dimension {dim_idx}']
            # Add contribution for each token at this dimension
            for token_contrib in token_contributions:
                row.append(token_contrib[dim_idx])
            # Add final pooled embedding value for this dimension
            row.append(final_embedding[dim_idx].item())
            # Add sum of contributions for this dimension
            row.append(sum_of_contributions[dim_idx])
            writer.writerow(row)
        
        # Add a row showing the relationship
        relationship_row = ['RELATIONSHIP: FINAL_POOLED = SUM / num_tokens']
        for _ in token_numbers:
            relationship_row.append('')
        relationship_row.append(f'FINAL_POOLED × {num_tokens} = SUM')
        relationship_row.append('(Verify: FINAL_POOLED × num_tokens ≈ SUM)')
        writer.writerow(relationship_row)
        
        # Summary row
        writer.writerow(['Summary', f'Number of tokens: {num_tokens}', f'Embedding dimension: {num_dims}', f'Sum of attention mask: {attention_mask.sum().item()}'])
    print(f"  ✓ Saved pooling details to {filename}")
    
    return final_embedding.numpy(), tokens, initial_embeddings.numpy(), post_attention_embeddings.numpy(), token_display


def analyze_sentence_transformer(text, prefix, model, model_name, is_hebrew=False):
    """
    Analyze text with SentenceTransformer model (works for both Hebrew and English).
    
    Args:
        text: Text to analyze
        prefix: Prefix for output filenames (e.g., 'gen1' or 'gen13')
        model: SentenceTransformer model instance
        model_name: Model name for file naming ('hebrew_st' or 'english_st')
        is_hebrew: Whether this is Hebrew text (affects token display)
    
    Returns:
        tuple: (final_embedding, tokens, initial_embeddings, post_attention_embeddings, token_display)
    """
    print(f"Analyzing text with {model_name}: {text[:50]}...")
    
    transformer_model = model[0].auto_model
    tokenizer = model[0].tokenizer
    
    # Tokenize
    encoded = tokenizer(
        text,
        padding=False,
        truncation=True,
        return_tensors='pt',
        max_length=512
    )
    
    input_ids = encoded['input_ids'][0].to('cpu')
    attention_mask = encoded['attention_mask'][0].to('cpu')
    tokens = tokenizer.convert_ids_to_tokens(input_ids)
    
    # Get token display (for Hebrew, try to get original spans)
    token_display = tokens.copy()
    if is_hebrew:
        # Try to get offset mapping for Hebrew
        try:
            encoded_no_tensors = tokenizer(
                text,
                padding=False,
                truncation=True,
                return_offsets_mapping=True,
                max_length=512
            )
            offset_mapping = encoded_no_tensors['offset_mapping']
            for i, token in enumerate(tokens):
                if i < len(offset_mapping):
                    start, end = offset_mapping[i]
                    if start != 0 or end != 0:
                        try:
                            original_span = text[start:end]
                            if original_span and original_span.strip():
                                token_display[i] = f"{token} → {original_span}"
                        except:
                            pass
        except:
            pass  # Fallback to just tokens
    
    # Get initial token embeddings
    with torch.no_grad():
        embeddings_layer = transformer_model.embeddings
        token_embeddings = embeddings_layer.word_embeddings(input_ids)
        positions = torch.arange(0, len(input_ids), dtype=torch.long)
        max_pos = embeddings_layer.position_embeddings.num_embeddings
        positions = torch.clamp(positions, 0, max_pos - 1)
        position_embeddings = embeddings_layer.position_embeddings(positions)
        initial_embeddings = token_embeddings + position_embeddings
    
    # Save initial token embeddings
    filename = OUTPUT_DIR / f"{prefix}_{model_name}_initial_tokens.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if is_hebrew:
            header = ['token_index', 'token_subword', 'original_text_span'] + [f'embedding_dim_{i}' for i in range(initial_embeddings.shape[1])]
            writer.writerow(header)
            for i, (token, token_disp, embedding) in enumerate(zip(tokens, token_display, initial_embeddings)):
                if ' → ' in token_disp:
                    original_span = token_disp.split(' → ')[1]
                else:
                    original_span = token_disp
                row = [i, token, original_span] + embedding.tolist()
                writer.writerow(row)
        else:
            header = ['token_index', 'token_text'] + [f'embedding_dim_{i}' for i in range(initial_embeddings.shape[1])]
            writer.writerow(header)
            for i, (token, embedding) in enumerate(zip(tokens, initial_embeddings)):
                row = [i, token] + embedding.tolist()
                writer.writerow(row)
    print(f"  ✓ Saved initial tokens to {filename}")
    
    # Get post-attention embeddings
    with torch.no_grad():
        outputs = transformer_model.forward(
            input_ids=input_ids.unsqueeze(0),
            attention_mask=attention_mask.unsqueeze(0)
        )
        post_attention_embeddings = outputs.last_hidden_state[0]
    
    # Save post-attention token embeddings
    filename = OUTPUT_DIR / f"{prefix}_{model_name}_post_attention_tokens.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if is_hebrew:
            header = ['token_index', 'token_subword', 'original_text_span'] + [f'embedding_dim_{i}' for i in range(post_attention_embeddings.shape[1])]
            writer.writerow(header)
            for i, (token, token_disp, embedding) in enumerate(zip(tokens, token_display, post_attention_embeddings)):
                if ' → ' in token_disp:
                    original_span = token_disp.split(' → ')[1]
                else:
                    original_span = token_disp
                row = [i, token, original_span] + embedding.tolist()
                writer.writerow(row)
        else:
            header = ['token_index', 'token_text'] + [f'embedding_dim_{i}' for i in range(post_attention_embeddings.shape[1])]
            writer.writerow(header)
            for i, (token, embedding) in enumerate(zip(tokens, post_attention_embeddings)):
                row = [i, token] + embedding.tolist()
                writer.writerow(row)
    print(f"  ✓ Saved post-attention tokens to {filename}")
    
    # Pooling process
    attention_mask_expanded = attention_mask.unsqueeze(-1).expand(post_attention_embeddings.size()).float()
    sum_embeddings = torch.sum(post_attention_embeddings * attention_mask_expanded, dim=0)
    sum_mask = torch.clamp(attention_mask_expanded.sum(dim=0), min=1e-9)
    final_embedding = sum_embeddings / sum_mask
    
    # Save pooling details (columnar format: each token is a column)
    filename = OUTPUT_DIR / f"{prefix}_{model_name}_pooling.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Collect token contributions
        token_contributions = []
        token_numbers = []
        token_texts = []
        
        for i, (token, embedding, mask_val) in enumerate(zip(tokens, post_attention_embeddings, attention_mask)):
            if mask_val > 0:  # Only non-padding tokens
                contribution = embedding * mask_val
                token_contributions.append(contribution.tolist())
                token_numbers.append(f"token_{i:02d}")
                if is_hebrew:
                    # Use token_display which has original spans
                    if i < len(token_display):
                        token_disp = token_display[i]
                        if ' → ' in token_disp:
                            original_span = token_disp.split(' → ')[1]
                        else:
                            original_span = token_disp
                        token_texts.append(original_span)
                    else:
                        token_texts.append(token)
                else:
                    token_texts.append(token)
        
        # Calculate sum of contributions (should match final_embedding * num_tokens for mean pooling)
        num_tokens = len(token_contributions)
        sum_of_contributions = sum_embeddings.tolist()  # This is the sum before dividing by mask
        
        # Build header: row labels column, then each token column, then final two columns
        header = [''] + token_numbers + ['FINAL_POOLED_EMBEDDING', 'SUM_OF_CONTRIBUTIONS']
        writer.writerow(header)
        
        # Row 1: Token number row
        row = ['Token number'] + token_numbers + ['FINAL_POOLED', 'SUM_OF_CONTRIBUTIONS']
        writer.writerow(row)
        
        # Row 2: Token text row
        row = ['Token text'] + token_texts + ['FINAL_POOLED_EMBEDDING', 'SUM_OF_CONTRIBUTIONS']
        writer.writerow(row)
        
        # Rows for each dimension
        num_dims = len(final_embedding)
        for dim_idx in range(num_dims):
            row = [f'Dimension {dim_idx}']
            # Add contribution for each token at this dimension
            for token_contrib in token_contributions:
                row.append(token_contrib[dim_idx])
            # Add final pooled embedding value for this dimension
            row.append(final_embedding[dim_idx].item())
            # Add sum of contributions for this dimension
            row.append(sum_of_contributions[dim_idx])
            writer.writerow(row)
        
        # Add a row showing the relationship
        relationship_row = ['RELATIONSHIP: FINAL_POOLED = SUM / num_tokens']
        for _ in token_numbers:
            relationship_row.append('')
        relationship_row.append(f'FINAL_POOLED × {num_tokens} = SUM')
        relationship_row.append('(Verify: FINAL_POOLED × num_tokens ≈ SUM)')
        writer.writerow(relationship_row)
        
        # Summary row
        writer.writerow(['Summary', f'Number of tokens: {num_tokens}', f'Embedding dimension: {num_dims}', f'Sum of attention mask: {attention_mask.sum().item()}'])
    print(f"  ✓ Saved pooling details to {filename}")
    
    return final_embedding.numpy(), tokens, initial_embeddings.numpy(), post_attention_embeddings.numpy(), token_display

# ============================================================================
# RUN ANALYSIS
# ============================================================================

print("=" * 80)
print("ANALYZING GENESIS 1:1 ALONE")
print("=" * 80)
print()

# BERiT
gen1_berit_final, gen1_berit_tokens, gen1_berit_initial, gen1_berit_post, gen1_berit_display = analyze_berit(GENESIS_1_1_HEBREW, 'gen1')
print()

# Hebrew ST
gen1_hebrew_st_final, gen1_hebrew_st_tokens, gen1_hebrew_st_initial, gen1_hebrew_st_post, gen1_hebrew_st_display = analyze_sentence_transformer(
    GENESIS_1_1_HEBREW, 'gen1', model_hebrew_st, 'hebrew_st', is_hebrew=True
)
print()

# English ST
gen1_english_st_final, gen1_english_st_tokens, gen1_english_st_initial, gen1_english_st_post, gen1_english_st_display = analyze_sentence_transformer(
    GENESIS_1_1_ENGLISH, 'gen1', model_english_st, 'english_st', is_hebrew=False
)
print()

print("=" * 80)
print("ANALYZING GENESIS 1:1 + 1:3 COMBINED")
print("=" * 80)
print()

gen13_hebrew_text = GENESIS_1_1_HEBREW + " " + GENESIS_1_3_HEBREW
gen13_english_text = GENESIS_1_1_ENGLISH + " " + GENESIS_1_3_ENGLISH

# BERiT
gen13_berit_final, gen13_berit_tokens, gen13_berit_initial, gen13_berit_post, gen13_berit_display = analyze_berit(gen13_hebrew_text, 'gen13')
print()

# Hebrew ST
gen13_hebrew_st_final, gen13_hebrew_st_tokens, gen13_hebrew_st_initial, gen13_hebrew_st_post, gen13_hebrew_st_display = analyze_sentence_transformer(
    gen13_hebrew_text, 'gen13', model_hebrew_st, 'hebrew_st', is_hebrew=True
)
print()

# English ST
gen13_english_st_final, gen13_english_st_tokens, gen13_english_st_initial, gen13_english_st_post, gen13_english_st_display = analyze_sentence_transformer(
    gen13_english_text, 'gen13', model_english_st, 'english_st', is_hebrew=False
)
print()

# ============================================================================
# COMPARATIVE ANALYSIS
# ============================================================================

print("=" * 80)
print("COMPARATIVE ANALYSIS")
print("=" * 80)
print()

def find_gen1_tokens_in_gen13(gen1_tokens, gen13_tokens, tokenizer):
    """Find which tokens from gen1 appear in gen13 (at the start)"""
    special_tokens = set()
    if hasattr(tokenizer, 'special_tokens_map'):
        for key, val in tokenizer.special_tokens_map.items():
            if isinstance(val, str):
                special_tokens.add(val)
            elif isinstance(val, list):
                special_tokens.update(val)
    special_tokens.update(['<s>', '</s>', '<pad>', '[CLS]', '[SEP]', '[PAD]', '<unk>', '[UNK]'])
    
    gen1_content_tokens = [t for t in gen1_tokens if t not in special_tokens]
    gen13_content_tokens = [t for t in gen13_tokens if t not in special_tokens]
    
    match_count = 0
    for i in range(min(len(gen1_content_tokens), len(gen13_content_tokens))):
        if gen1_content_tokens[i] == gen13_content_tokens[i]:
            match_count += 1
        else:
            break
    
    return match_count, gen1_content_tokens, gen13_content_tokens

# BERiT analysis
berit_match_count, gen1_berit_content, gen13_berit_content = find_gen1_tokens_in_gen13(
    gen1_berit_tokens, gen13_berit_tokens, tokenizer_berit
)
print(f"BERiT: {berit_match_count} content tokens from Gen 1:1 match at the start of Gen 1:1+1:3")

gen1_berit_start_idx = 1 if gen1_berit_tokens[0] in ['<s>', tokenizer_berit.bos_token] else 0
gen13_berit_start_idx = 1 if gen13_berit_tokens[0] in ['<s>', tokenizer_berit.bos_token] else 0

gen1_berit_initial_content = gen1_berit_initial[gen1_berit_start_idx:gen1_berit_start_idx+berit_match_count]
gen13_berit_initial_content = gen13_berit_initial[gen13_berit_start_idx:gen13_berit_start_idx+berit_match_count]
initial_diff_berit = np.abs(gen1_berit_initial_content - gen13_berit_initial_content)
print(f"  Initial embeddings difference (max): {np.max(initial_diff_berit):.6f}, (mean): {np.mean(initial_diff_berit):.6f}")

gen1_berit_post_content = gen1_berit_post[gen1_berit_start_idx:gen1_berit_start_idx+berit_match_count]
gen13_berit_post_content = gen13_berit_post[gen13_berit_start_idx:gen13_berit_start_idx+berit_match_count]
post_diff_berit = np.abs(gen1_berit_post_content - gen13_berit_post_content)
print(f"  Post-attention embeddings difference (max): {np.max(post_diff_berit):.6f}, (mean): {np.mean(post_diff_berit):.6f}")
print()

# Save detailed comparison analysis
analysis_filename = OUTPUT_DIR / "comparative_analysis.txt"
with open(analysis_filename, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("COMPARATIVE ANALYSIS: Gen 1:1 vs Gen 1:1+1:3\n")
    f.write("=" * 80 + "\n\n")
    
    f.write("KEY FINDING: Initial token embeddings should be IDENTICAL for matching tokens,\n")
    f.write("but post-attention embeddings should be DIFFERENT due to context!\n\n")
    
    f.write("BERiT ANALYSIS\n")
    f.write("-" * 80 + "\n")
    f.write(f"Matching tokens at start: {berit_match_count}\n")
    f.write(f"Initial embeddings max difference: {np.max(initial_diff_berit):.6f}\n")
    f.write(f"Initial embeddings mean difference: {np.mean(initial_diff_berit):.6f}\n")
    f.write(f"Post-attention embeddings max difference: {np.max(post_diff_berit):.6f}\n")
    f.write(f"Post-attention embeddings mean difference: {np.mean(post_diff_berit):.6f}\n\n")
    
    f.write("INTERPRETATION\n")
    f.write("-" * 80 + "\n")
    f.write("The attention mechanism allows tokens to 'see' and be influenced by other tokens\n")
    f.write("in the sequence. When we add Genesis 1:3 to Genesis 1:1, the tokens from Gen 1:1\n")
    f.write("now have access to the context from Gen 1:3, which changes their representations\n")
    f.write("even though the tokens themselves are the same. This is the power of attention!\n")

print(f"✓ Saved detailed analysis to {analysis_filename}")
print()

print("=" * 80)
print("✓ ANALYSIS COMPLETE!")
print("=" * 80)
print(f"All CSV files saved to: {OUTPUT_DIR}")
print(f"Generated 18 CSV files (3 models × 2 texts × 3 states)")
print()
