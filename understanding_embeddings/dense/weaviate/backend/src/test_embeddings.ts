/**
 * Simple test script to verify embedding generation works
 * Run with: npm run dev -- test_embeddings.ts
 * Or: ts-node src/test_embeddings.ts
 */

import { generateEmbedding } from './embeddings';

async function testEmbeddings() {
    console.log('Testing embedding generation...\n');
    
    // Test English ST
    console.log('1. Testing English ST...');
    const englishText = 'In the beginning, Elohim created the skies and the land';
    try {
        const englishEmbedding = await generateEmbedding(englishText, 'english_st');
        console.log(`   ✓ Generated embedding with dimension: ${englishEmbedding.length}`);
        console.log(`   First 5 values: ${englishEmbedding.slice(0, 5).map(v => v.toFixed(4)).join(', ')}`);
    } catch (error: any) {
        console.error(`   ✗ Error: ${error.message}`);
    }
    
    console.log();
    
    // Test Hebrew ST
    console.log('2. Testing Hebrew ST...');
    const hebrewText = 'בְּרֵאשִׁית בָּרָא אֱלֹהִים';
    try {
        const hebrewEmbedding = await generateEmbedding(hebrewText, 'hebrew_st');
        console.log(`   ✓ Generated embedding with dimension: ${hebrewEmbedding.length}`);
        console.log(`   First 5 values: ${hebrewEmbedding.slice(0, 5).map(v => v.toFixed(4)).join(', ')}`);
    } catch (error: any) {
        console.error(`   ✗ Error: ${error.message}`);
    }
    
    console.log();
    
    // Test BERiT
    console.log('3. Testing BERiT...');
    try {
        const beritEmbedding = await generateEmbedding(hebrewText, 'berit');
        console.log(`   ✓ Generated embedding with dimension: ${beritEmbedding.length}`);
        console.log(`   First 5 values: ${beritEmbedding.slice(0, 5).map(v => v.toFixed(4)).join(', ')}`);
    } catch (error: any) {
        console.error(`   ✗ Error: ${error.message}`);
    }
    
    console.log('\n✓ All tests completed!');
}

// Run tests
testEmbeddings().catch(console.error);

