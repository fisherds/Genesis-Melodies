# Chunking Strategy Analysis

## Model Context Windows

- **BERiT**: 128 tokens (max_position_embeddings)
- **Hebrew ST**: ~512 tokens (standard SentenceTransformer)
- **English ST**: ~512 tokens (standard SentenceTransformer)

## Token Count Analysis

### Quilt Piece Records (5 records)
- Average Tokens (Hebrew ST): **3,320.40** ❌ (6.5x over limit)
- Average Tokens (BERiT): **2,970.80** ❌ (23x over limit!)
- Average Tokens (English): **1,948.00** ❌ (3.8x over limit)

**Verdict**: WAY TOO LARGE for all models. Will be heavily truncated.

### Pericope Records (50 records)
- Average Tokens (Hebrew ST): **379.24** ✅ (74% of limit - good!)
- Average Tokens (BERiT): **340.80** ❌ (2.7x over limit)
- Average Tokens (English): **222.52** ✅ (43% of limit - excellent!)

**Verdict**: 
- ✅ Good for Hebrew ST and English models
- ❌ Still too large for BERiT (will truncate ~62% of content)

### Verse Records (304 records)
- Average Tokens (Hebrew ST): **52.64** ✅ (10% of limit - very safe)
- Average Tokens (BERiT): **47.31** ✅ (37% of limit - perfect!)
- Average Tokens (English): **31.73** ✅ (6% of limit - very safe)

**Verdict**: Perfect size for all models, especially BERiT.

## Sweet Spot Analysis

### For BERiT Model (128 token limit - most restrictive)
- **Verse level**: ✅ **47 tokens average** - Perfect! Uses 37% of capacity
- **Pericope level**: ❌ **341 tokens average** - 2.7x over, loses ~62% of content
- **Quilt piece level**: ❌ **2,971 tokens average** - 23x over, loses ~96% of content

**BERiT Recommendation**: **Verse-level chunking** is the only viable option.

### For Hebrew ST Model (512 token limit)
- **Verse level**: ✅ **53 tokens average** - Very safe, but may lose context
- **Pericope level**: ✅ **379 tokens average** - **SWEET SPOT!** Uses 74% of capacity
- **Quilt piece level**: ❌ **3,320 tokens average** - Way too large

**Hebrew ST Recommendation**: **Pericope-level chunking** is the sweet spot.

### For English ST Model (512 token limit)
- **Verse level**: ✅ **32 tokens average** - Very safe, but may lose context
- **Pericope level**: ✅ **223 tokens average** - **SWEET SPOT!** Uses 43% of capacity
- **Quilt piece level**: ❌ **1,948 tokens average** - Way too large

**English ST Recommendation**: **Pericope-level chunking** is the sweet spot.

## Overall Recommendation

### If using BERiT:
**Use verse-level chunking** (304 records)
- Only option that fits within 128 token limit
- Trade-off: More granular, may lose some semantic context

### If using Hebrew ST or English ST:
**Use pericope-level chunking** (50 records)
- **Sweet spot**: Uses ~74% (Hebrew) or 43% (English) of context window
- Good balance between context preservation and model capacity
- Still semantically meaningful units

### Hybrid Approach:
- **Primary**: Pericope-level for Hebrew ST and English ST
- **Alternative**: Verse-level for BERiT (if you need BERiT embeddings)
- Consider: Using different chunking strategies for different models

## Chunking Comparison Table

| Type | Description | Records | Avg Words Hebrew | Avg Words English | Avg Tokens BERiT | Avg Tokens Hebrew ST | Avg Tokens English ST |
|------|-------------|---------|------------------|-------------------|------------------|---------------------|----------------------|
| Quilt Piece | Chunked as 5 GIANT records! | 5 | 714 | 1510 | 2970 | 3320 | 1948 |
| Pericope | 50 records using Classroom Visuals! | 50 | 81 | 171 | 341 | 379 | 223 |
| Verse | Basic 1 verse = 1 record | 304 | 11 | 23 | 47 | 53 | 32 |
| Agentic BERiT | Optimized for BERiT (128 token limit) | 230 | 17 | 62 | 72 | 79 | 81 |
| Agentic Hebrew ST | Optimized for Hebrew ST (512 token limit) | 72 | 57 | 148 | 242 | 269 | 193 |
| Agentic English ST | Optimized for English ST (384 token limit) | 57 | 65 | 134 | 272 | 303 | 175 |

## Key Insights

1. **BERiT is the bottleneck**: Its 128-token limit forces verse-level chunking
2. **Pericopes are optimal** for models with 512-token windows
3. **Quilt pieces are unusable** for embedding generation (too large)
4. **Verse-level is safe** but may fragment semantic meaning
5. **Token efficiency**: Hebrew text tokenizes to ~4.7x more tokens than English text
6. **Agentic chunking** provides model-specific optimization with better token utilization

## Token Efficiency Ratios

- Hebrew ST: ~4.7 tokens per Hebrew word
- BERiT: ~4.2 tokens per Hebrew word  
- English ST: ~1.3 tokens per English word

This explains why Hebrew text needs smaller chunks than English text.

