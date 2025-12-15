// Simple password protection (stored in localStorage for session)
const ADMIN_PASSWORD = 'avrahamadmin'; // Change this to your desired password

// Firestore instance
let db = null;
let allFeedbackDocs = []; // Store all feedback documents with IDs

// Check if user is logged in
function isLoggedIn() {
    return localStorage.getItem('admin_logged_in') === 'true';
}

// Initialize on window load
window.addEventListener("load", (event) => {
    console.log("Admin page loaded");
    
    // Initialize Firestore if Firebase is available
    if (typeof firebase !== 'undefined' && firebase.firestore) {
        db = firebase.firestore();
        console.log("Firestore initialized");
    } else {
        console.error("Firebase/Firestore not available");
        document.getElementById('login-screen').style.display = 'none';
        document.getElementById('admin-screen').style.display = 'block';
        document.getElementById('error').style.display = 'block';
        document.getElementById('error').textContent = 'Error: Firebase not initialized. Please ensure you are accessing this page through Firebase Hosting.';
        return;
    }
    
    // Check login status
    if (isLoggedIn()) {
        showAdminScreen();
    } else {
        showLoginScreen();
    }
    
    // Setup login button
    document.getElementById('login-btn').addEventListener('click', handleLogin);
    document.getElementById('password-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleLogin();
        }
    });
    
    // Setup logout button
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    
    // Setup refresh button
    document.getElementById('refresh-btn').addEventListener('click', loadFeedbackData);
    
    // Setup delete selected button
    document.getElementById('delete-selected-btn').addEventListener('click', deleteSelected);
});

function showLoginScreen() {
    document.getElementById('login-screen').style.display = 'block';
    document.getElementById('admin-screen').style.display = 'none';
    document.getElementById('password-input').value = '';
    document.getElementById('password-input').focus();
}

function showAdminScreen() {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('admin-screen').style.display = 'block';
    loadFeedbackData();
}

function handleLogin() {
    const password = document.getElementById('password-input').value;
    const errorEl = document.getElementById('login-error');
    
    if (password === ADMIN_PASSWORD) {
        localStorage.setItem('admin_logged_in', 'true');
        showAdminScreen();
    } else {
        errorEl.style.display = 'block';
        errorEl.textContent = 'Incorrect password';
        document.getElementById('password-input').value = '';
    }
}

function handleLogout() {
    localStorage.removeItem('admin_logged_in');
    showLoginScreen();
}

async function loadFeedbackData() {
    const loadingEl = document.getElementById('loading');
    const errorEl = document.getElementById('error');
    const tbody = document.getElementById('results-tbody');
    const bulkActions = document.querySelector('.bulk-actions');
    
    loadingEl.style.display = 'block';
    errorEl.style.display = 'none';
    tbody.innerHTML = '';
    bulkActions.style.display = 'none';
    
    try {
        // Get all documents from SearchFeedback collection, ordered by created timestamp (newest first)
        const snapshot = await db.collection('SearchFeedback')
            .orderBy('created', 'desc')
            .get();
        
        if (snapshot.empty) {
            loadingEl.style.display = 'none';
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px;">No feedback data found.</td></tr>';
            return;
        }
        
        // Store all documents with IDs
        allFeedbackDocs = [];
        
        // Process each document
        snapshot.forEach((doc) => {
            const data = doc.data();
            allFeedbackDocs.push({
                id: doc.id,
                ...data
            });
            
            // Format created date
            let createdStr = '';
            if (data.created) {
                if (data.created.toDate) {
                    createdStr = data.created.toDate().toLocaleString();
                } else if (data.created instanceof Date) {
                    createdStr = data.created.toLocaleString();
                } else if (data.created.seconds) {
                    createdStr = new Date(data.created.seconds * 1000).toLocaleString();
                }
            }
            
            // Format search verses compactly
            const searchVerses = formatSearchVerses(data.search_verses || []);
            
            // Create table row
            const row = document.createElement('tr');
            row.dataset.docId = doc.id;
            row.innerHTML = `
                <td><input type="checkbox" class="select-doc" data-doc-id="${doc.id}"></td>
                <td>${createdStr}</td>
                <td>${data.endpoint || ''}</td>
                <td>${data.model_name || ''}</td>
                <td>${data.chunking_level || ''}</td>
                <td>${searchVerses}</td>
                <td><button class="btn btn-danger btn-small delete-btn" data-doc-id="${doc.id}">Delete</button></td>
            `;
            tbody.appendChild(row);
        });
        
        // Attach delete button handlers
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const docId = e.target.dataset.docId;
                deleteDocument(docId);
            });
        });
        
        // Attach checkbox handlers
        document.querySelectorAll('.select-doc').forEach(checkbox => {
            checkbox.addEventListener('change', updateBulkActions);
        });
        
        loadingEl.style.display = 'none';
        console.log(`Loaded ${allFeedbackDocs.length} feedback records`);
        
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

function updateBulkActions() {
    const selected = document.querySelectorAll('.select-doc:checked');
    const bulkActions = document.querySelector('.bulk-actions');
    const selectedCount = document.getElementById('selected-count');
    
    if (selected.length > 0) {
        bulkActions.style.display = 'block';
        selectedCount.textContent = `${selected.length} selected`;
    } else {
        bulkActions.style.display = 'none';
    }
}

async function deleteDocument(docId) {
    try {
        await db.collection('SearchFeedback').doc(docId).delete();
        console.log(`Deleted document ${docId}`);
        
        // Remove from UI
        const row = document.querySelector(`tr[data-doc-id="${docId}"]`);
        if (row) {
            row.remove();
        }
        
        // Remove from array
        allFeedbackDocs = allFeedbackDocs.filter(doc => doc.id !== docId);
        
        // Update bulk actions
        updateBulkActions();
        
    } catch (error) {
        console.error('Error deleting document:', error);
        alert('Error deleting document: ' + error.message);
    }
}

async function deleteSelected() {
    const selected = document.querySelectorAll('.select-doc:checked');
    if (selected.length === 0) {
        return;
    }
    
    const docIds = Array.from(selected).map(cb => cb.dataset.docId);
    
    try {
        // Delete all selected documents
        const deletePromises = docIds.map(docId => 
            db.collection('SearchFeedback').doc(docId).delete()
        );
        
        await Promise.all(deletePromises);
        console.log(`Deleted ${docIds.length} documents`);
        
        // Reload data to refresh UI
        loadFeedbackData();
        
    } catch (error) {
        console.error('Error deleting documents:', error);
        alert('Error deleting documents: ' + error.message);
    }
}

