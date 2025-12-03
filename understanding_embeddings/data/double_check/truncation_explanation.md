# What Happens When Text Exceeds 128 Tokens in BERiT?

## The Short Answer

**Yes, the overflow tokens "fall on the floor" - they are completely discarded and never processed by the model.**

## How Truncation Works

### Step-by-Step Process

1. **Tokenization**: Your text is converted into tokens
   ```
   Example: A pericope with 341 tokens
   [token_1, token_2, token_3, ..., token_128, token_129, ..., token_341]
   ```

2. **Truncation**: The tokenizer cuts it down to 128 tokens
   ```python
   # In the code (models.py line 46-51):
   encoded = self.tokenizer(
       batch_texts,
       truncation=True,  # ← This tells it to cut off excess
       max_length=128     # ← Cut to this length
   )
   ```
   
   **Result**: Only the first 128 tokens are kept
   ```
   [token_1, token_2, token_3, ..., token_128]
   ```
   
   **Lost**: `token_129` through `token_341` are **completely discarded**

3. **Model Processing**: The model only sees the 128 tokens
   - The model has no knowledge that there was more text
   - It processes only what it receives
   - The embedding is generated from these 128 tokens only

4. **Embedding Generation**: Mean pooling averages the 128 token embeddings
   - The final embedding represents **only the first 128 tokens**
   - Information from tokens 129-341 is **completely absent**

## Which Tokens Get Kept?

By default, HuggingFace tokenizers use **"right truncation"** (truncate from the end):
- **Kept**: First 128 tokens (the beginning of your text)
- **Lost**: Everything after token 128 (the end of your text)

### Example with a Pericope

Let's say you have a pericope that's 341 tokens:

```
Original text (341 tokens):
[Beginning of pericope...] ... [Middle...] ... [End of pericope...]
     ↑ tokens 1-128          ↑ tokens 129-213    ↑ tokens 214-341
     ✅ KEPT                ❌ LOST              ❌ LOST
```

**What the model sees:**
```
[Beginning of pericope...]
     ↑ Only these 128 tokens
```

**What gets lost:**
- The middle and end of the pericope
- Any semantic information, context, or meaning in those tokens
- The model has no way to recover this information

## Real-World Impact

### For a Pericope (341 tokens average)

**What you think you're embedding:**
- Complete pericope with full context
- Beginning, middle, and end
- Full semantic meaning

**What BERiT actually embeds:**
- Only the first 128 tokens (~37% of the text)
- Missing ~63% of the content
- The embedding represents an incomplete fragment

### The Embedding Represents What?

The embedding is a mathematical representation of the **mean/average** of the 128 token embeddings:

```python
# Simplified version of what happens (models.py lines 82-91):
embeddings = mean_pooling(outputs.last_hidden_state, attention_mask)
# This averages the 128 token vectors into one vector
```

**Important**: This single embedding vector tries to capture the meaning of only those 128 tokens. It cannot represent information that was never processed.

## Why This Matters

### 1. **Information Loss**
- If important information is at the end of your text, it's completely lost
- The model has no "memory" of what was truncated

### 2. **Semantic Distortion**
- The embedding represents a fragment, not the complete text
- Search results may match based on the beginning, but miss relevant content from the end

### 3. **Inconsistent Representations**
- Different chunks with the same beginning but different endings will have identical embeddings
- You lose the ability to distinguish between texts that differ only in their later tokens

## Can You Control Which Tokens Are Kept?

Yes! You can configure truncation strategy:

```python
# Keep the END instead of the beginning
encoded = tokenizer(
    text,
    truncation=True,
    max_length=128,
    truncation_side='left'  # Keep last 128 tokens instead
)
```

**But this has trade-offs:**
- You'd lose the beginning instead of the end
- Still losing 63% of your content
- Not a real solution for long texts

## The Real Solution

**Use appropriate chunking:**
- For BERiT: Use verse-level chunks (47 tokens average)
- This ensures **no truncation** and **complete information preservation**

## Visual Summary

```
Text: 341 tokens
[████████████████████████████████████████████████████████████████████████████]
     ↑ First 128 tokens (37%)          ↑ Remaining 213 tokens (63%)
     ✅ Processed by model             ❌ Discarded, never seen
     
Embedding: Represents only the first 128 tokens
```

## Key Takeaways

1. **Truncation = Permanent Loss**: Tokens beyond 128 are discarded before the model ever sees them
2. **No Recovery**: The model cannot reconstruct or infer what was lost
3. **Embedding Incompleteness**: Your embedding represents a fragment, not the whole text
4. **Solution**: Chunk appropriately to avoid truncation entirely

