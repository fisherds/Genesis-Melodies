/**
 * Embedding generation using @xenova/transformers (for English) and Python fallback (for Hebrew)
 * Supports BERiT, Hebrew ST, and English ST models
 */

import { pipeline } from '@xenova/transformers';
import { execFile } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execFileAsync = promisify(execFile);

// Model configurations
const MODEL_CONFIGS = {
    'berit': {
        modelName: 'gngpostalsrvc/BERiT',
        maxLength: 128,  // BERiT has max_position_embeddings=128
        dimension: 256,
    },
    'hebrew_st': {
        modelName: 'odunola/sentence-transformers-bible-reference-final',
        maxLength: 512,
        dimension: 768,
    },
    'english_st': {
        modelName: 'sentence-transformers/all-mpnet-base-v2',
        maxLength: 384,
        dimension: 768,
    },
};

// Cache for loaded models
const modelCache: Map<string, any> = new Map();

/**
 * Load a model pipeline (cached)
 */
async function loadModel(modelKey: keyof typeof MODEL_CONFIGS): Promise<any> {
    const config = MODEL_CONFIGS[modelKey];
    
    if (modelCache.has(modelKey)) {
        return modelCache.get(modelKey)!;
    }
    
    console.log(`Loading ${modelKey} model: ${config.modelName}...`);
    
    // Use feature-extraction pipeline for all models
    const pipe = await pipeline('feature-extraction', config.modelName, {
        quantized: false,  // Use full precision for accuracy
    });
    
    modelCache.set(modelKey, pipe);
    console.log(`✓ ${modelKey} model loaded`);
    
    return pipe;
}

/**
 * Generate embedding using Python script (fallback for models without ONNX)
 */
async function generateEmbeddingPython(text: string, modelKey: 'berit' | 'hebrew_st'): Promise<number[]> {
    const scriptPath = path.join(__dirname, 'generate_embedding_python.py');
    const pythonCmd = process.env.PYTHON_CMD || 'python3';
    
    try {
        // Call Python script with model key and text
        const { stdout, stderr } = await execFileAsync(pythonCmd, [
            scriptPath,
            modelKey,
            text
        ]);
        
        if (stderr) {
            console.error('Python script stderr:', stderr);
        }
        
        // Parse JSON output
        const embedding = JSON.parse(stdout.trim());
        
        // Check for error in response
        if (embedding.error) {
            throw new Error(embedding.error);
        }
        
        return embedding as number[];
    } catch (error: any) {
        console.error('Error generating embedding with Python:', error);
        throw new Error(`Failed to generate embedding: ${error.message}`);
    }
}

/**
 * Generate embedding for BERiT (RoBERTa-based)
 * Uses Python fallback since ONNX version not available
 */
async function generateBERiTEmbedding(text: string): Promise<number[]> {
    // BERiT doesn't have ONNX version, use Python fallback
    return generateEmbeddingPython(text, 'berit');
}

/**
 * Generate embedding for Hebrew ST
 * Uses Python fallback since ONNX version not available
 */
async function generateHebrewSTEmbedding(text: string): Promise<number[]> {
    // Hebrew ST doesn't have ONNX version, use Python fallback
    return generateEmbeddingPython(text, 'hebrew_st');
}


/**
 * Generate embedding for SentenceTransformer models
 * SentenceTransformers handle pooling internally
 */
async function generateSentenceTransformerEmbedding(
    text: string,
    modelKey: 'hebrew_st' | 'english_st'
): Promise<number[]> {
    if (modelKey === 'hebrew_st') {
        // Hebrew ST doesn't have ONNX version, use Python fallback
        return generateHebrewSTEmbedding(text);
    }
    
    // English ST works with @xenova/transformers
    const pipe = await loadModel(modelKey);
    const config = MODEL_CONFIGS[modelKey];
    
    // SentenceTransformers handle pooling internally
    const output = await pipe(text, {
        padding: true,
        truncation: true,
        max_length: config.maxLength,
        pooling: 'mean',
        normalize: true,
    });
    
    // output is a Tensor with shape [1, hidden_dim] (already pooled and normalized)
    const embedding = Array.from(output.data as Float32Array);
    
    return embedding;
}

/**
 * Generate embedding for a given text and model
 */
export async function generateEmbedding(
    text: string,
    modelKey: 'hebrew_st' | 'berit' | 'english_st'
): Promise<number[]> {
    if (modelKey === 'berit') {
        return generateBERiTEmbedding(text);
    } else {
        return generateSentenceTransformerEmbedding(text, modelKey);
    }
}
