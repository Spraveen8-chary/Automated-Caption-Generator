// State management
let state = {
    uploadedFile: null,
    uploadedFilename: null,
    selectedStyles: ['meme'],
    selectedLanguage: 'en',
    srtFilenames: []
};

// DOM elements
const uploadArea = document.getElementById('uploadArea');
const videoInput = document.getElementById('videoInput');
const selectFileBtn = document.getElementById('selectFileBtn');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const changeFileBtn = document.getElementById('changeFileBtn');

const styleSection = document.getElementById('styleSection');
const styleCards = document.querySelectorAll('.style-card');
const styleChecks = document.querySelectorAll('input[name="captionStyle"]');

const languageSection = document.getElementById('languageSection');
const languageSelect = document.getElementById('languageSelect');

const actionSection = document.getElementById('actionSection');
const generateBtn = document.getElementById('generateBtn');

const progressSection = document.getElementById('progressSection');
const progressBar = document.getElementById('progressBar');
const progressTitle = document.getElementById('progressTitle');
const progressText = document.getElementById('progressText');

const resultsSection = document.getElementById('resultsSection');
const previewList = document.getElementById('previewList');
const newVideoBtn = document.getElementById('newVideoBtn');

const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');
const retryBtn = document.getElementById('retryBtn');

// Event listeners
selectFileBtn.addEventListener('click', () => videoInput.click());
uploadArea.addEventListener('click', () => videoInput.click());
videoInput.addEventListener('change', handleFileSelect);
changeFileBtn.addEventListener('click', () => videoInput.click());

// Drag and drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
});
uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('drag-over');
});
uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

// Style selection (checkboxes)
styleCards.forEach(card => {
    const cb = card.querySelector('input[type="checkbox"]');
    cb.addEventListener('change', handleStyleSelection);
    card.addEventListener('click', function(event) {
        if (event.target !== cb) cb.checked = !cb.checked;
        card.classList.toggle('selected');
        handleStyleSelection();
    });
});
function handleStyleSelection() {
    const checked = [];
    styleChecks.forEach(cb => {
        if (cb.checked) checked.push(cb.value);
    });
    state.selectedStyles = checked;
}

// Language selection
languageSelect.addEventListener('change', (e) => {
    state.selectedLanguage = e.target.value;
});

// Generate button
generateBtn.addEventListener('click', processVideo);

// New video button
newVideoBtn.addEventListener('click', reset);

// Retry button
retryBtn.addEventListener('click', reset);

// File select handlers
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) handleFile(file);
}
function handleFile(file) {
    // Validate file type and size
    const validTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska', 'video/webm'];
    if (!validTypes.includes(file.type)) {
        showError('Invalid file type. Please upload MP4, MOV, AVI, MKV, or WebM.');
        return;
    }
    const maxSize = 100 * 1024 * 1024;
    if (file.size > maxSize) {
        showError('File too large. Maximum size is 100MB.');
        return;
    }
    state.uploadedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    fileInfo.style.display = 'flex';
    styleSection.style.display = 'block';
    languageSection.style.display = 'block';
    actionSection.style.display = 'block';
    uploadArea.style.display = 'none';
}
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Main process
async function processVideo() {
    try {
        // Check at least one style selected
        if (!state.selectedStyles || state.selectedStyles.length === 0) {
            showError('Please select at least one caption style.');
            return;
        }
        generateBtn.disabled = true;
        actionSection.style.display = 'none';
        errorSection.style.display = 'none';
        progressSection.style.display = 'block';
        updateProgress(0, 'Uploading video...');

        // Upload video
        const formData = new FormData();
        formData.append('video', state.uploadedFile);
        const uploadResponse = await fetch('/upload', { method: 'POST', body: formData });
        if (!uploadResponse.ok) {
            const error = await uploadResponse.json();
            throw new Error(error.error || 'Upload failed');
        }
        const uploadData = await uploadResponse.json();
        state.uploadedFilename = uploadData.filename;
        updateProgress(33, 'Video uploaded. Processing...');

        // Multi-style process request
        const processResponse = await fetch('/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: state.uploadedFilename,
                styles: state.selectedStyles,       // Array of styles
                language: state.selectedLanguage
            })
        });
        if (!processResponse.ok) {
            const error = await processResponse.json();
            throw new Error(error.error || 'Processing failed');
        }
        const processData = await processResponse.json();
        updateProgress(100, 'Complete!');
        setTimeout(() => {
            showMultiStyleResults(processData);
        }, 500);
    } catch (error) {
        console.error('Error:', error);
        showError(error.message);
        generateBtn.disabled = false;
    }
}

function updateProgress(percent, text) {
    progressBar.style.width = percent + '%';
    progressText.textContent = text;
}

// Show multi-style preview
function showMultiStyleResults(data) {
    progressSection.style.display = 'none';
    previewList.innerHTML = '';
    if (data.results && data.results.length > 0) {
        data.results.forEach((result, i) => {
            const title = document.createElement('h4');
            title.textContent = `Style: ${capitalize(result.style)}`;
            previewList.appendChild(title);
            (result.captions.slice(0, 5)).forEach((caption, idx) => {
                const item = document.createElement('div');
                item.className = 'preview-item';
                item.textContent = `${idx + 1}. ${caption.text}`;
                previewList.appendChild(item);
            });
            // Download SRT button
            const download = document.createElement('button');
            download.className = 'btn btn--primary btn--sm';
            download.textContent = `Download SRT (${result.style})`;
            download.addEventListener('click', () => {
                window.location.href = `/download/${result.srt_filename}`;
            });
            previewList.appendChild(download);
            if (i < data.results.length - 1) {
                const hr = document.createElement('hr');
                previewList.appendChild(hr);
            }
        });
    }
    resultsSection.style.display = 'block';
}

function showError(message) {
    errorMessage.textContent = message;
    errorSection.style.display = 'block';
    progressSection.style.display = 'none';
    actionSection.style.display = 'block';
}

function reset() {
    state = {
        uploadedFile: null,
        uploadedFilename: null,
        selectedStyles: ['meme'],
        selectedLanguage: 'en',
        srtFilenames: []
    };
    videoInput.value = '';
    fileInfo.style.display = 'none';
    uploadArea.style.display = 'block';
    styleSection.style.display = 'none';
    languageSection.style.display = 'none';
    actionSection.style.display = 'none';
    progressSection.style.display = 'none';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
    generateBtn.disabled = false;

    // Reset style selection
    styleCards.forEach(card => card.classList.remove('selected'));
    styleChecks.forEach((cb, idx) => {
        cb.checked = (cb.value === 'meme');
        if (cb.value === 'meme') styleCards[idx].classList.add('selected');
    });

    languageSelect.value = 'en';
}

function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}
