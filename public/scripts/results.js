// Firestore instance
let db = null;
let allFeedbackData = []; // Store all feedback for CSV download

// Initialize on window load
window.addEventListener("load", (event) => {
    console.log("Results page loaded");
    
    // Initialize Firestore if Firebase is available
    if (typeof firebase !== 'undefined' && firebase.firestore) {
        db = firebase.firestore();
        console.log("Firestore initialized");
        loadFeedbackData();
    } else {
        console.error("Firebase/Firestore not available");
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').style.display = 'block';
        document.getElementById('error').textContent = 'Error: Firebase not initialized. Please ensure you are accessing this page through Firebase Hosting.';
    }
    
    // Setup CSV download button
    document.getElementById('download-csv-btn').addEventListener('click', downloadCSV);
});

async function loadFeedbackData() {
    const loadingEl = document.getElementById('loading');
    const errorEl = document.getElementById('error');
    const tbody = document.getElementById('results-tbody');
    
    try {
        // Get all documents from SearchFeedback collection, ordered by created timestamp (newest first)
        const snapshot = await db.collection('SearchFeedback')
            .orderBy('created', 'desc')
            .get();
        
        if (snapshot.empty) {
            loadingEl.style.display = 'none';
            tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 20px;">No feedback data found.</td></tr>';
            return;
        }
        
        // Store all data for CSV download
        allFeedbackData = [];
        
        // Process each document
        snapshot.forEach((doc) => {
            const data = doc.data();
            allFeedbackData.push(data);
            
            // Format search verses compactly
            const searchVerses = formatSearchVerses(data.search_verses || []);
            
            // Get results and ratings
            const results = data.results_and_ranking || [];
            const resultCells = [];
            
            // Create cells for up to 5 results
            for (let i = 0; i < 5; i++) {
                if (i < results.length) {
                    const result = results[i];
                    const rating = result.rating !== undefined ? result.rating : '';
                    const title = result.result ? (result.result.title || result.result.id || '') : '';
                    resultCells.push(`${rating} / ${title}`);
                } else {
                    resultCells.push('');
                }
            }
            
            // Create table row
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${data.endpoint || ''}</td>
                <td>${data.model_name || ''}</td>
                <td>${data.chunking_level || ''}</td>
                <td>${searchVerses}</td>
                <td>${resultCells[0]}</td>
                <td>${resultCells[1]}</td>
                <td>${resultCells[2]}</td>
                <td>${resultCells[3]}</td>
                <td>${resultCells[4]}</td>
            `;
            tbody.appendChild(row);
        });
        
        loadingEl.style.display = 'none';
        console.log(`Loaded ${allFeedbackData.length} feedback records`);
        
    } catch (error) {
        console.error('Error loading feedback data:', error);
        loadingEl.style.display = 'none';
        errorEl.style.display = 'block';
        errorEl.textContent = 'Error loading feedback data: ' + error.message;
    }
}

function formatSearchVerses(verses) {
    if (!Array.isArray(verses) || verses.length === 0) {
        return '';
    }
    
    // Format as compact string like "1:1, 1:2, 2:1"
    return verses.map(v => {
        const chapter = v.chapter || '';
        const verse = v.verse || '';
        return `${chapter}:${verse}`;
    }).join(', ');
}

function downloadCSV() {
    if (allFeedbackData.length === 0) {
        alert('No data to download');
        return;
    }
    
    // Convert all feedback data to CSV format
    // Include all fields from Firestore documents
    const headers = [
        'created',
        'endpoint',
        'model_name',
        'chunking_level',
        'top_k',
        'search_verses',
        'results_and_ranking'
    ];
    
    // Create CSV content
    let csvContent = headers.join(',') + '\n';
    
    allFeedbackData.forEach((doc) => {
        // Handle Firestore timestamp
        let createdStr = '';
        if (doc.created) {
            if (doc.created.toDate) {
                createdStr = doc.created.toDate().toISOString();
            } else if (doc.created instanceof Date) {
                createdStr = doc.created.toISOString();
            } else if (typeof doc.created === 'string') {
                createdStr = doc.created;
            } else if (doc.created.seconds) {
                // Firestore Timestamp object
                createdStr = new Date(doc.created.seconds * 1000).toISOString();
            }
        }
        
        const row = [
            createdStr,
            doc.endpoint || '',
            doc.model_name || '',
            doc.chunking_level || '',
            doc.top_k || '',
            JSON.stringify(doc.search_verses || []),
            JSON.stringify(doc.results_and_ranking || [])
        ];
        
        // Escape commas and quotes in CSV
        const escapedRow = row.map(cell => {
            const cellStr = String(cell);
            // If cell contains comma, quote, or newline, wrap in quotes and escape quotes
            if (cellStr.includes(',') || cellStr.includes('"') || cellStr.includes('\n')) {
                return '"' + cellStr.replace(/"/g, '""') + '"';
            }
            return cellStr;
        });
        
        csvContent += escapedRow.join(',') + '\n';
    });
    
    // Create download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `search_feedback_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

