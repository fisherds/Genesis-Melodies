// Global state
let textVisuals = [];
let currentVisualIndex = -1;
let selectedVerses = new Set(); // Store as "chapter:verse" strings

// Suppress console warnings from iframe content (Tailwind CSS warnings, etc.)
const originalWarn = console.warn;
console.warn = function(...args) {
    const message = args.join(' ');
    // Filter out Tailwind CDN warnings from iframe content
    if (message.includes('cdn.tailwindcss.com') || message.includes('Tailwind CSS')) {
        return; // Suppress this warning
    }
    originalWarn.apply(console, args);
};

// Suppress console errors from browser extensions trying to observe iframes
const originalError = console.error;
console.error = function(...args) {
    const message = args.join(' ');
    // Filter out MutationObserver errors from browser extensions
    if (message.includes('web-client-content-script') || 
        (message.includes('MutationObserver') && message.includes('observe'))) {
        return; // Suppress this error
    }
    originalError.apply(console, args);
};

window.addEventListener("load", (event) => {
    console.log("page is fully loaded");
    setupButtonListeners();
    loadTextVisuals();
    setupResizer();
    setupPanelToggles();
});

async function loadTextVisuals() {
    try {
        const response = await fetch('scripts/text_visuals.json');
        textVisuals = await response.json();
        console.log(`Loaded ${textVisuals.length} text visuals`);
        populateNavigation();
        // Select first item by default
        if (textVisuals.length > 0) {
            selectVisual(0);
        }
    } catch (error) {
        console.error("Error loading text visuals:", error);
        alert("Error loading text visuals: " + error.message);
    }
}

function populateNavigation() {
    const navList = document.getElementById('nav-list');
    navList.innerHTML = '';
    
    let currentHeader = null;
    
    textVisuals.forEach((visual, index) => {
        // Add header if this visual has one and it's different from current
        if (visual.header && visual.header !== currentHeader) {
            const headerDiv = document.createElement('div');
            headerDiv.className = 'nav-section-header';
            headerDiv.textContent = visual.header;
            navList.appendChild(headerDiv);
            currentHeader = visual.header;
        }
        
        const navItem = document.createElement('div');
        navItem.className = 'nav-item';
        navItem.textContent = visual.verse_range;
        navItem.dataset.index = index;
        navItem.addEventListener('click', () => selectVisual(index));
        navList.appendChild(navItem);
    });
}

function selectVisual(index) {
    if (index < 0 || index >= textVisuals.length) return;
    
    currentVisualIndex = index;
    const visual = textVisuals[index];
    
    // Update navigation selection
    document.querySelectorAll('.nav-item').forEach((item, i) => {
        if (i === index) {
            item.classList.add('selected');
        } else {
            item.classList.remove('selected');
        }
    });
    
    // Update iframe
    const iframe = document.getElementById('bible-visual-iframe');
    iframe.src = visual.url;
    
    // Populate verse selection column
    populateVerseSelection(visual.verses);
    
    // Update navigation buttons
    updateNavButtons();
}

function populateVerseSelection(verses) {
    const verseList = document.getElementById('verse-list');
    const selectAllBtn = document.getElementById('select-all-btn');
    verseList.innerHTML = '';
    
    if (verses.length === 0) {
        selectAllBtn.style.display = 'none';
        return;
    }
    
    // Show "All" button if there are verses
    selectAllBtn.style.display = 'block';
    
    verses.forEach(verse => {
        const verseKey = `${verse.chapter}:${verse.verse}`;
        const isSelected = selectedVerses.has(verseKey);
        
        const verseItem = document.createElement('div');
        verseItem.className = 'verse-checkbox-item' + (isSelected ? ' selected' : '');
        verseItem.dataset.chapter = verse.chapter;
        verseItem.dataset.verse = verse.verse;
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = isSelected;
        checkbox.addEventListener('change', (e) => {
            e.stopPropagation();
            toggleVerseSelection(verse.chapter, verse.verse, e.target.checked);
        });
        
        const verseText = document.createTextNode(`${verse.chapter}:${verse.verse}`);
        verseItem.appendChild(checkbox);
        verseItem.appendChild(verseText);
        
        verseItem.addEventListener('click', (e) => {
            if (e.target !== checkbox) {
                checkbox.checked = !checkbox.checked;
                toggleVerseSelection(verse.chapter, verse.verse, checkbox.checked);
            }
        });
        
        verseList.appendChild(verseItem);
    });
    
    // Update select all button state
    updateSelectAllButton();
}

function toggleVerseSelection(chapter, verse, isSelected) {
    const verseKey = `${chapter}:${verse}`;
    
    if (isSelected) {
        selectedVerses.add(verseKey);
    } else {
        selectedVerses.delete(verseKey);
    }
    
    // Update UI
    const verseItem = document.querySelector(`.verse-checkbox-item[data-chapter="${chapter}"][data-verse="${verse}"]`);
    if (verseItem) {
        if (isSelected) {
            verseItem.classList.add('selected');
        } else {
            verseItem.classList.remove('selected');
        }
    }
    
    // Update Search Verses field
    updateSearchVersesField();
    
    // Update "All" button state
    updateSelectAllButton();
}

function updateSearchVersesField() {
    const searchVersesField = document.getElementById('search_verses');
    const versesArray = Array.from(selectedVerses)
        .map(key => {
            const [chapter, verse] = key.split(':');
            return { chapter: parseInt(chapter), verse: parseInt(verse) };
        })
        .sort((a, b) => {
            if (a.chapter !== b.chapter) return a.chapter - b.chapter;
            return a.verse - b.verse;
        });
    
    searchVersesField.value = JSON.stringify(versesArray, null, 2);
    updateClearVersesButton();
    validateSearchButton(); // Also validate search button when verses change
}

function updateNavButtons() {
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    
    prevBtn.disabled = currentVisualIndex <= 0;
    nextBtn.disabled = currentVisualIndex >= textVisuals.length - 1;
}

function setupButtonListeners() {
    document.querySelector("#search_button").addEventListener("click", performSearch);
    document.getElementById("prev-btn").addEventListener("click", () => {
        if (currentVisualIndex > 0) {
            selectVisual(currentVisualIndex - 1);
        }
    });
    document.getElementById("next-btn").addEventListener("click", () => {
        if (currentVisualIndex < textVisuals.length - 1) {
            selectVisual(currentVisualIndex + 1);
        }
    });
    document.getElementById("clear-all-btn").addEventListener("click", clearAllVerses);
    
    // Add listeners for model and record_level changes to validate combinations
    document.getElementById("model_name").addEventListener("change", validateSearchButton);
    document.getElementById("record_level").addEventListener("change", validateSearchButton);
    
    // Add listener for Clear Verses button
    document.getElementById("clear_verses_button").addEventListener("click", clearSearchVerses);
    
    // Add listener for search_verses textarea changes to enable/disable Clear button and Search button
    document.getElementById("search_verses").addEventListener("input", () => {
        updateClearVersesButton();
        validateSearchButton();
    });
    
    // Add listener for "All" button
    document.getElementById("select-all-btn").addEventListener("click", selectAllVerses);
    
    // Add listener for Full Screen button
    document.getElementById("fullscreen-btn").addEventListener("click", toggleFullScreen);
    
    // Setup mobile functionality
    setupMobileMenu();
    
    // Initial validation
    validateSearchButton();
    updateClearVersesButton();
}

function selectAllVerses() {
    // Get all checkboxes in the current verse list
    const checkboxes = document.querySelectorAll('#verse-list .verse-checkbox-item input[type="checkbox"]');
    
    if (checkboxes.length === 0) return;
    
    // Check if all are already selected
    const allSelected = Array.from(checkboxes).every(cb => cb.checked);
    
    // Toggle all checkboxes
    checkboxes.forEach(checkbox => {
        const verseItem = checkbox.closest('.verse-checkbox-item');
        const chapter = parseInt(verseItem.dataset.chapter);
        const verse = parseInt(verseItem.dataset.verse);
        const shouldSelect = !allSelected;
        
        checkbox.checked = shouldSelect;
        toggleVerseSelection(chapter, verse, shouldSelect);
    });
    
    // Update button text
    updateSelectAllButton();
}

function updateSelectAllButton() {
    const checkboxes = document.querySelectorAll('#verse-list .verse-checkbox-item input[type="checkbox"]');
    const selectAllBtn = document.getElementById('select-all-btn');
    
    if (checkboxes.length === 0) {
        selectAllBtn.style.display = 'none';
        return;
    }
    
    const allSelected = Array.from(checkboxes).every(cb => cb.checked);
    selectAllBtn.textContent = allSelected ? 'Deselect All' : 'All';
}

function clearAllVerses() {
    selectedVerses.clear();
    // Update all checkboxes
    document.querySelectorAll('.verse-checkbox-item input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = false;
    });
    document.querySelectorAll('.verse-checkbox-item').forEach(item => {
        item.classList.remove('selected');
    });
    updateSearchVersesField();
}

let savedLeftWidth = 70; // Default 70%

function setupResizer() {
    const resizer = document.getElementById('resizer');
    const leftPanel = document.getElementById('left-panel');
    const rightPanel = document.getElementById('right-panel');
    
    let isResizing = false;
    
    resizer.addEventListener('mousedown', (e) => {
        isResizing = true;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        e.preventDefault();
    });
    
    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        
        const containerWidth = document.querySelector('.main-container').offsetWidth;
        const newLeftWidth = (e.clientX / containerWidth) * 100;
        
        // Constrain between 20% and 80%
        const minLeftWidth = 20;
        const maxLeftWidth = 80;
        const constrainedWidth = Math.max(minLeftWidth, Math.min(maxLeftWidth, newLeftWidth));
        
        savedLeftWidth = constrainedWidth;
        leftPanel.style.width = `${constrainedWidth}%`;
        rightPanel.style.width = `${100 - constrainedWidth}%`;
    });
    
    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
    });
}

function setupPanelToggles() {
    const leftToggle = document.getElementById('left-panel-toggle');
    const rightToggle = document.getElementById('right-panel-toggle');
    const leftPanel = document.getElementById('left-panel');
    const rightPanel = document.getElementById('right-panel');
    const resizer = document.getElementById('resizer');
    
    // Create restore buttons (initially hidden)
    const leftRestore = document.createElement('button');
    leftRestore.className = 'panel-restore left-restore';
    leftRestore.innerHTML = '☰';
    leftRestore.title = 'Show Bible Reader';
    leftRestore.style.display = 'none';
    document.body.appendChild(leftRestore);
    
    const rightRestore = document.createElement('button');
    rightRestore.className = 'panel-restore right-restore';
    rightRestore.innerHTML = '🔍';
    rightRestore.title = 'Show Search';
    rightRestore.style.display = 'none';
    document.body.appendChild(rightRestore);
    
    leftToggle.addEventListener('click', () => {
        // If right panel is already hidden, don't allow closing left panel
        if (rightPanel.style.display === 'none') {
            rightPanel.style.display = 'block';
            resizer.style.display = 'block';
            leftPanel.style.width = `${savedLeftWidth}%`;
            rightPanel.style.width = `${100 - savedLeftWidth}%`;
            rightRestore.style.display = 'none';
            return;
        }
        
        leftPanel.style.display = 'none';
        resizer.style.display = 'none';
        rightPanel.style.width = '100%';
        leftRestore.style.display = 'flex';
    });
    
    rightToggle.addEventListener('click', () => {
        // If left panel is already hidden, don't allow closing right panel
        if (leftPanel.style.display === 'none') {
            leftPanel.style.display = 'flex';
            resizer.style.display = 'block';
            leftPanel.style.width = `${savedLeftWidth}%`;
            rightPanel.style.width = `${100 - savedLeftWidth}%`;
            leftRestore.style.display = 'none';
            return;
        }
        
        rightPanel.style.display = 'none';
        resizer.style.display = 'none';
        leftPanel.style.width = '100%';
        rightRestore.style.display = 'flex';
    });
    
    leftRestore.addEventListener('click', () => {
        leftPanel.style.display = 'flex';
        resizer.style.display = 'block';
        leftPanel.style.width = `${savedLeftWidth}%`;
        rightPanel.style.width = `${100 - savedLeftWidth}%`;
        rightPanel.style.display = 'block';
        leftRestore.style.display = 'none';
    });
    
    rightRestore.addEventListener('click', () => {
        rightPanel.style.display = 'block';
        resizer.style.display = 'block';
        leftPanel.style.width = `${savedLeftWidth}%`;
        rightPanel.style.width = `${100 - savedLeftWidth}%`;
        rightRestore.style.display = 'none';
    });
}

function setupMobileMenu() {
    const hamburgerBtn = document.getElementById('hamburger-btn');
    const navColumn = document.getElementById('nav-column');
    const verseColumn = document.getElementById('verse-selection-column');
    const navCloseBtn = document.getElementById('nav-close-btn');
    const verseCloseBtn = document.getElementById('verse-close-btn');
    
    let currentOpenPanel = null;
    
    function isMobile() {
        return window.innerWidth <= 600;
    }
    
    function updateMobileVisibility() {
        if (isMobile()) {
            hamburgerBtn.style.display = 'block';
            navCloseBtn.style.display = 'block';
            verseCloseBtn.style.display = 'block';
            // Hide columns by default on mobile
            if (!navColumn.classList.contains('mobile-visible')) {
                navColumn.style.display = 'none';
            }
            if (!verseColumn.classList.contains('mobile-visible')) {
                verseColumn.style.display = 'none';
            }
        } else {
            hamburgerBtn.style.display = 'none';
            navCloseBtn.style.display = 'none';
            verseCloseBtn.style.display = 'none';
            navColumn.style.display = '';
            verseColumn.style.display = '';
            navColumn.classList.remove('mobile-visible');
            verseColumn.classList.remove('mobile-visible');
        }
    }
    
    function closeAllPanels() {
        navColumn.classList.remove('mobile-visible');
        verseColumn.classList.remove('mobile-visible');
        if (isMobile()) {
            navColumn.style.display = 'none';
            verseColumn.style.display = 'none';
        }
        currentOpenPanel = null;
    }
    
    function openPanel(panel) {
        closeAllPanels();
        if (isMobile()) {
            panel.classList.add('mobile-visible');
            panel.style.display = 'flex';
            currentOpenPanel = panel;
        }
    }
    
    function toggleNavPanel() {
        if (!isMobile()) return;
        
        if (currentOpenPanel === navColumn) {
            closeAllPanels();
        } else {
            openPanel(navColumn);
        }
    }
    
    hamburgerBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleNavPanel();
    });
    
    navCloseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        closeAllPanels();
    });
    
    verseCloseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        closeAllPanels();
    });
    
    // Close panels when clicking outside
    document.addEventListener('click', (e) => {
        if (isMobile() && currentOpenPanel && !currentOpenPanel.contains(e.target) && e.target !== hamburgerBtn) {
            closeAllPanels();
        }
    });
    
    // Prevent clicks inside panels from closing them
    navColumn.addEventListener('click', (e) => e.stopPropagation());
    verseColumn.addEventListener('click', (e) => e.stopPropagation());
    
    // Handle window resize
    window.addEventListener('resize', () => {
        updateMobileVisibility();
        if (!isMobile()) {
            closeAllPanels();
        }
    });
    
    // Initial setup
    updateMobileVisibility();
}

// Valid model/record_level combinations
const VALID_COMBINATIONS = {
    'pericope': ['hebrew_st', 'english_st'],
    'verse': ['hebrew_st', 'berit', 'english_st'],
    'agentic_berit': ['berit', 'hebrew_st', 'english_st'],
    'agentic_hebrew_st': ['hebrew_st', 'english_st'],
    'agentic_english_st': ['hebrew_st', 'english_st'],
};

function validateSearchButton() {
    const modelName = document.querySelector("#model_name").value;
    const recordLevel = document.querySelector("#record_level").value;
    const searchButton = document.querySelector("#search_button");
    const searchVersesField = document.getElementById('search_verses');
    
    // Check if combination is valid
    const isValid = VALID_COMBINATIONS[recordLevel] && 
                    VALID_COMBINATIONS[recordLevel].includes(modelName);
    
    // Check if there are verses in the search field
    let hasVerses = false;
    try {
        const verses = JSON.parse(searchVersesField.value);
        hasVerses = Array.isArray(verses) && verses.length > 0;
    } catch (e) {
        hasVerses = false;
    }
    
    const canSearch = isValid && hasVerses;
    
    if (canSearch) {
        searchButton.disabled = false;
        searchButton.style.opacity = '1';
        searchButton.style.cursor = 'pointer';
        searchButton.title = '';
    } else {
        searchButton.disabled = true;
        searchButton.style.opacity = '0.6';
        searchButton.style.cursor = 'not-allowed';
        if (!isValid) {
            const validModels = VALID_COMBINATIONS[recordLevel] || [];
            searchButton.title = `Invalid combination. For ${recordLevel}, valid models are: ${validModels.join(', ')}`;
        } else if (!hasVerses) {
            searchButton.title = 'Please add verses to search';
        }
    }
}

function updateClearVersesButton() {
    const searchVersesField = document.getElementById('search_verses');
    const clearButton = document.getElementById('clear_verses_button');
    
    try {
        const verses = JSON.parse(searchVersesField.value);
        const hasVerses = Array.isArray(verses) && verses.length > 0;
        clearButton.disabled = !hasVerses;
        if (hasVerses) {
            clearButton.style.opacity = '1';
            clearButton.style.cursor = 'pointer';
        } else {
            clearButton.style.opacity = '0.6';
            clearButton.style.cursor = 'not-allowed';
        }
    } catch (e) {
        // If JSON is invalid, check if field is not empty
        const isEmpty = searchVersesField.value.trim() === '[]' || searchVersesField.value.trim() === '';
        clearButton.disabled = isEmpty;
        if (isEmpty) {
            clearButton.style.opacity = '0.6';
            clearButton.style.cursor = 'not-allowed';
        } else {
            clearButton.style.opacity = '1';
            clearButton.style.cursor = 'pointer';
        }
    }
}

function clearSearchVerses() {
    const searchVersesField = document.getElementById('search_verses');
    searchVersesField.value = '[]';
    selectedVerses.clear();
    // Update all checkboxes
    document.querySelectorAll('.verse-checkbox-item input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = false;
    });
    document.querySelectorAll('.verse-checkbox-item').forEach(item => {
        item.classList.remove('selected');
    });
    updateClearVersesButton();
    validateSearchButton(); // Also validate search button when verses are cleared
}

let isFullScreen = false;

function toggleFullScreen() {
    const navColumn = document.getElementById('nav-column');
    const verseColumn = document.getElementById('verse-selection-column');
    const rightPanel = document.getElementById('right-panel');
    const resizer = document.getElementById('resizer');
    const leftPanel = document.getElementById('left-panel');
    const fullscreenBtn = document.getElementById('fullscreen-btn');
    
    isFullScreen = !isFullScreen;
    
    if (isFullScreen) {
        // Hide navigation, verse selection, and search panels
        navColumn.style.display = 'none';
        verseColumn.style.display = 'none';
        rightPanel.style.display = 'none';
        resizer.style.display = 'none';
        leftPanel.style.width = '100%';
        fullscreenBtn.textContent = 'Exit Full Screen';
    } else {
        // Show all panels
        navColumn.style.display = '';
        verseColumn.style.display = '';
        rightPanel.style.display = 'block';
        resizer.style.display = 'block';
        leftPanel.style.width = `${savedLeftWidth}%`;
        rightPanel.style.width = `${100 - savedLeftWidth}%`;
        fullscreenBtn.textContent = 'Full Screen';
        
        // Update mobile visibility if needed
        if (window.innerWidth <= 600) {
            // On mobile, keep columns hidden by default
            navColumn.style.display = 'none';
            verseColumn.style.display = 'none';
        }
    }
}

async function performSearch() {
    console.log("performSearch");
    
    // Clear results and show spinner immediately
    const container = document.querySelector("#results_container");
    container.innerHTML = '<div class="spinner-container"><div class="spinner"></div><div class="spinner-text">Searching...</div></div>';
    
    // Get form values
    const modelName = document.querySelector("#model_name").value;
    const recordLevel = document.querySelector("#record_level").value;
    const topK = document.querySelector("#top_k").value;
    const searchVersesStr = document.querySelector("#search_verses").value;
    
    // Validate combination (should already be validated by button state, but double-check)
    if (!VALID_COMBINATIONS[recordLevel] || !VALID_COMBINATIONS[recordLevel].includes(modelName)) {
        container.innerHTML = '<p style="color: red;">Invalid combination: ' + modelName + ' cannot be used with ' + recordLevel + '</p>';
        return;
    }
    
    // Validate search_verses JSON
    let searchVerses;
    try {
        searchVerses = JSON.parse(searchVersesStr);
    } catch (e) {
        container.innerHTML = '<p style="color: red;">Invalid JSON in Search Verses field: ' + e.message + '</p>';
        return;
    }
    
    // Build URL with query parameters
    const params = new URLSearchParams({
        model_name: modelName,
        record_level: recordLevel,
        top_k: topK,
        search_verses: JSON.stringify(searchVerses)
    });
    
    const url = `/api/search?${params.toString()}`;
    console.log("Making request to: " + url);
    
    try {
        let response = await fetch(url);
        console.log("handling response: " + response.status);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || "Search failed");
        }
        
        let responseData = await response.json();
        console.log("Received response:", responseData);
        
        // Handle both old format (array) and new format (object with english_search_text)
        let results, englishSearchText;
        if (Array.isArray(responseData)) {
            results = responseData;
            englishSearchText = null;
        } else {
            results = responseData.results || [];
            englishSearchText = responseData.english_search_text;
        }
        
        displaySearchInfo(englishSearchText);
        displayResults(results);
        
    } catch (error) {
        console.error("Error performing search:", error);
        container.innerHTML = '<p style="color: red;">Error: ' + error.message + '</p>';
    }
}

function formatVerses(versesStr) {
    try {
        const verses = typeof versesStr === 'string' ? JSON.parse(versesStr) : versesStr;
        if (!Array.isArray(verses) || verses.length === 0) return '';
        
        // Convert to array of {chapter, verse} objects and sort
        const verseObjs = verses.map(v => ({
            chapter: typeof v.chapter === 'number' ? v.chapter : parseInt(v.chapter),
            verse: typeof v.verse === 'number' ? v.verse : parseFloat(v.verse)
        })).sort((a, b) => {
            if (a.chapter !== b.chapter) return a.chapter - b.chapter;
            return a.verse - b.verse;
        });
        
        if (verseObjs.length === 0) return '';
        
        // Group consecutive verses
        const groups = [];
        let currentGroup = [verseObjs[0]];
        
        for (let i = 1; i < verseObjs.length; i++) {
            const prev = verseObjs[i - 1];
            const curr = verseObjs[i];
            
            // Check if consecutive (same chapter and verse number is next)
            const isConsecutive = prev.chapter === curr.chapter && 
                                 Math.floor(curr.verse) === Math.floor(prev.verse) + 1;
            
            if (isConsecutive) {
                currentGroup.push(curr);
            } else {
                groups.push(currentGroup);
                currentGroup = [curr];
            }
        }
        groups.push(currentGroup);
        
        // Format groups
        const formatted = groups.map(group => {
            if (group.length === 1) {
                return `${group[0].chapter}:${group[0].verse}`;
            } else {
                // Check if all in same chapter
                const sameChapter = group.every(v => v.chapter === group[0].chapter);
                if (sameChapter) {
                    return `${group[0].chapter}:${group[0].verse}-${group[group.length - 1].verse}`;
                } else {
                    // Mixed chapters, just join with commas
                    return group.map(v => `${v.chapter}:${v.verse}`).join(', ');
                }
            }
        }).join(', ');
        
        return formatted;
    } catch (e) {
        return String(versesStr);
    }
}

function displaySearchInfo(englishSearchText) {
    const container = document.querySelector("#results_container");
    let infoHtml = '';
    
    if (englishSearchText) {
        infoHtml = `<div class="search-info"><strong>Searching for:</strong> ${englishSearchText}</div>`;
    }
    
    // Store for later use in displayResults
    container.innerHTML = infoHtml;
}

function displayResults(results) {
    const container = document.querySelector("#results_container");
    const recordLevel = document.querySelector("#record_level").value;
    
    // Preserve search info if it exists
    const existingInfo = container.innerHTML;
    
    if (results.length === 0) {
        container.innerHTML = existingInfo + "<p>No results found.</p>";
        return;
    }
    
    // Only show verses field for pericope level
    const showVerses = recordLevel === 'pericope';
    
    let html = existingInfo;
    for (let result of results) {
        let versesHtml = '';
        if (showVerses) {
            const formattedVerses = formatVerses(result.verses || "");
            if (formattedVerses) {
                versesHtml = `<div class="verses"><strong>Verses:</strong> ${formattedVerses}</div>`;
            }
        }
        
        html += `
            <div class="result-item">
                <h3>${result.title || result.id}</h3>
                ${versesHtml}
                <div class="score">Score: ${result.score.toFixed(4)}</div>
                <div class="text">${result.text || ""}</div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}
