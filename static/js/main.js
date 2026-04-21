// State management
let state = {
    uploadedFile: null,
    uploadedFilename: null,
    selectedStyle: 'meme',
    selectedLanguages: ['en'],
    primaryLanguage: 'en',
    languageOutputs: [],
    transcriptJobId: null,
    transcript: null,
    latestExport: null
};

const appConfig = window.APP_CONFIG || {};
const freeUserVideoLimit = Number(appConfig.freeUserVideoLimit || 2);

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
const languageCheckboxes = document.querySelectorAll('input[name="outputLanguage"]');

const actionSection = document.getElementById('actionSection');
const generateBtn = document.getElementById('generateBtn');

const progressSection = document.getElementById('progressSection');
const progressBar = document.getElementById('progressBar');
const progressTitle = document.getElementById('progressTitle');
const progressText = document.getElementById('progressText');

const transcriptSection = document.getElementById('transcriptSection');
const transcriptEditor = document.getElementById('transcriptEditor');
const transcriptMeta = document.getElementById('transcriptMeta');
const transcriptStatus = document.getElementById('transcriptStatus');
const saveTranscriptBtn = document.getElementById('saveTranscriptBtn');
const previewStylesBtn = document.getElementById('previewStylesBtn');
const exportTranscriptBtn = document.getElementById('exportTranscriptBtn');
const editTranscriptBtn = document.getElementById('editTranscriptBtn');

const stylePreviewSection = document.getElementById('stylePreviewSection');
const stylePreviewGrid = document.getElementById('stylePreviewGrid');

const resultsSection = document.getElementById('resultsSection');
const previewList = document.getElementById('previewList');
const totalCaptionsEl = document.getElementById('totalCaptions');
const selectedStyleEl = document.getElementById('selectedStyle');
const selectedLanguageEl = document.getElementById('selectedLanguage');
const downloadBtn = document.getElementById('downloadBtn');
const newVideoBtn = document.getElementById('newVideoBtn');

const usageHeading = document.querySelector('.usage-text h3');
const usageParagraph = document.querySelector('.usage-text p');
const usageFill = document.querySelector('.progress-bar-mini__fill');

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
    const cb = card.querySelector('input[type="radio"]');
    cb.addEventListener('change', handleStyleSelection);
    card.addEventListener('click', function(event) {
        if (event.target !== cb) cb.checked = true;
        handleStyleSelection();
    });
});

function handleStyleSelection() {
    const checked = Array.from(styleChecks).find(cb => cb.checked);
    state.selectedStyle = checked ? checked.value : 'meme';

    styleCards.forEach(card => {
        const radio = card.querySelector('input[type="radio"]');
        card.classList.toggle('selected', radio && radio.checked);
    });

    if (state.transcriptJobId) {
        previewStyles();
    }
}

// Language selection
languageCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', syncLanguageSelection);
});

// Generate button
generateBtn.addEventListener('click', processVideo);

// Transcript actions
saveTranscriptBtn.addEventListener('click', saveTranscript);
previewStylesBtn.addEventListener('click', previewStyles);
exportTranscriptBtn.addEventListener('click', exportTranscript);
editTranscriptBtn.addEventListener('click', () => {
    transcriptSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
});

// New video button
newVideoBtn.addEventListener('click', reset);

// Retry button
retryBtn.addEventListener('click', reset);

state.selectedLanguages = Array.from(languageCheckboxes).filter(cb => cb.checked).map(cb => cb.value);
handleStyleSelection();

// File select handlers
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) handleFile(file);
}

function handleFile(file) {
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

function formatTime(seconds) {
    const total = Math.max(0, Number(seconds) || 0);
    const mins = Math.floor(total / 60);
    const secs = Math.floor(total % 60);
    const millis = Math.floor((total - Math.floor(total)) * 1000);
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(millis).padStart(3, '0')}`;
}

function formatLanguageLabel(code) {
    const option = languageSelect.querySelector(`option[value="${code}"]`);
    return option ? option.textContent : code.toUpperCase();
}

function formatLanguageList(codes) {
    if (!codes || codes.length === 0) return 'English';
    return codes.map(formatLanguageLabel).join(', ');
}

function getSelectedLanguages() {
    return Array.from(languageCheckboxes)
        .filter(checkbox => checkbox.checked)
        .map(checkbox => checkbox.value);
}

function syncLanguageSelection() {
    state.selectedLanguages = getSelectedLanguages();
}

// Main process
async function processVideo() {
    try {
        if (!state.selectedStyle) {
            showError('Please select a caption style.');
            return;
        }

        if (!state.selectedLanguages || state.selectedLanguages.length === 0) {
            showError('Please select at least one output language.');
            return;
        }

        generateBtn.disabled = true;
        actionSection.style.display = 'none';
        errorSection.style.display = 'none';
        transcriptSection.style.display = 'none';
        stylePreviewSection.style.display = 'none';
        resultsSection.style.display = 'none';
        progressSection.style.display = 'block';
        updateProgress(0, 'Uploading video...');

        const formData = new FormData();
        formData.append('video', state.uploadedFile);
        const uploadResponse = await fetch('/upload', { method: 'POST', body: formData });
        if (!uploadResponse.ok) {
            const error = await uploadResponse.json();
            throw new Error(error.error || 'Upload failed');
        }
        const uploadData = await uploadResponse.json();
        state.uploadedFilename = uploadData.filename;
        updateProgress(35, 'Video uploaded. Transcribing...');

        const processResponse = await fetch('/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: state.uploadedFilename,
                original_filename: uploadData.original_filename,
                style: state.selectedStyle,
                styles: [state.selectedStyle],
                languages: state.selectedLanguages,
                language: state.selectedLanguages[0]
            })
        });
        if (!processResponse.ok) {
            const error = await processResponse.json();
            throw new Error(error.error || 'Processing failed');
        }

        const processData = await processResponse.json();
        state.transcriptJobId = processData.transcript_job_id;
        state.transcript = processData.transcript;
        state.languageOutputs = processData.outputs || [];
        state.selectedStyle = processData.selected_style || state.selectedStyle;
        state.selectedLanguages = processData.selected_languages || state.selectedLanguages;
        state.primaryLanguage = processData.primary_language || state.selectedLanguages[0];
        state.latestExport = null;
        updateUsageBanner(processData);

        updateProgress(100, 'Transcript ready!');
        setTimeout(() => {
            showTranscriptEditor(processData);
        }, 350);
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

function updateUsageBanner(data) {
    if (!data) return;

    if (usageHeading) {
        usageHeading.textContent = data.is_premium ? 'Premium Account' : 'Free Account';
    }

    if (usageParagraph) {
        if (data.is_premium) {
            usageParagraph.textContent = 'Unlimited video processing';
        } else if (typeof data.videos_processed !== 'undefined') {
            const configuredLimit = Number(data.free_user_video_limit || freeUserVideoLimit || 2);
            usageParagraph.textContent = `${data.videos_processed} of ${configuredLimit} videos used`;
        }
    }

    if (usageFill && typeof data.videos_processed !== 'undefined') {
        const configuredLimit = Number(data.free_user_video_limit || freeUserVideoLimit || 2);
        usageFill.style.width = `${Math.min((data.videos_processed / configuredLimit) * 100, 100)}%`;
    }
}

function renderTranscriptEditor(transcript) {
    transcriptEditor.innerHTML = '';

    if (!transcript || !transcript.segments || transcript.segments.length === 0) {
        transcriptEditor.innerHTML = '<p class="empty-state">No transcript segments were returned.</p>';
        return;
    }

    transcript.segments.forEach((segment, index) => {
        const card = document.createElement('div');
        card.className = 'segment-card';
        card.dataset.index = index;
        card.dataset.start = segment.start;
        card.dataset.end = segment.end;
        card.dataset.duration = segment.duration || Math.max((segment.end || 0) - (segment.start || 0), 0);

        const header = document.createElement('div');
        header.className = 'segment-card__header';

        const title = document.createElement('strong');
        title.textContent = `Segment ${index + 1}`;

        const timestamp = document.createElement('span');
        timestamp.className = 'segment-timestamp';
        timestamp.textContent = `${formatTime(segment.start)} - ${formatTime(segment.end)}`;

        header.appendChild(title);
        header.appendChild(timestamp);

        const textarea = document.createElement('textarea');
        textarea.className = 'segment-textarea';
        textarea.value = segment.text || '';
        textarea.rows = 3;
        textarea.placeholder = 'Edit transcript text';

        card.appendChild(header);
        card.appendChild(textarea);
        transcriptEditor.appendChild(card);
    });
}

function collectTranscriptSegments() {
    return Array.from(transcriptEditor.querySelectorAll('.segment-card')).map(card => {
        const textarea = card.querySelector('.segment-textarea');
        return {
            start: Number(card.dataset.start || 0),
            end: Number(card.dataset.end || 0),
            duration: Number(card.dataset.duration || 0),
            text: textarea ? textarea.value.trim() : ''
        };
    });
}

function showTranscriptEditor(data) {
    progressSection.style.display = 'none';
    resultsSection.style.display = 'none';
    transcriptSection.style.display = 'block';

    const transcript = data.transcript || state.transcript;
    state.transcript = transcript;
    transcriptStatus.textContent = 'Draft';
    const primaryLanguage = data.primary_language || state.primaryLanguage || state.selectedLanguages[0];
    state.selectedStyle = data.selected_style || state.selectedStyle;
    state.selectedLanguages = data.selected_languages || state.selectedLanguages;
    state.primaryLanguage = primaryLanguage;
    transcriptMeta.textContent = `${transcript.original_filename} | ${transcript.segments.length} segments | ${formatLanguageLabel(primaryLanguage)} | ${formatLanguageList(state.selectedLanguages)}`;
    renderTranscriptEditor(transcript);
    previewStyles();
    window.scrollTo({ top: transcriptSection.offsetTop - 20, behavior: 'smooth' });
}

async function saveTranscript() {
    try {
        if (!state.transcriptJobId) {
            showError('No transcript is available to save yet.');
            return;
        }

        saveTranscriptBtn.disabled = true;
        transcriptStatus.textContent = 'Saving...';

        const segments = collectTranscriptSegments();
        const response = await fetch(`/transcripts/${state.transcriptJobId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ segments, language_code: state.primaryLanguage })
        });

        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'Save failed');
        }

        state.transcript = result.transcript;
        transcriptStatus.textContent = 'Saved';
        await previewStyles();
    } catch (error) {
        transcriptStatus.textContent = 'Draft';
        showError(error.message);
    } finally {
        saveTranscriptBtn.disabled = false;
    }
}

async function previewStyles() {
    try {
        if (!state.transcriptJobId) {
            return;
        }

        previewStylesBtn.disabled = true;

        const response = await fetch(`/transcripts/${state.transcriptJobId}/styles`, {
            method: 'POST'
        });

        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'Style preview failed');
        }

        renderStylePreviews(result.styles || []);
    } catch (error) {
        showError(error.message);
    } finally {
        previewStylesBtn.disabled = false;
    }
}

function renderStylePreviews(stylePreviews) {
    stylePreviewGrid.innerHTML = '';

    if (!stylePreviews || stylePreviews.length === 0) {
        stylePreviewSection.style.display = 'none';
        return;
    }

    stylePreviewSection.style.display = 'block';

    stylePreviews.forEach(preview => {
        const card = document.createElement('div');
        card.className = 'style-preview-card';

        const header = document.createElement('div');
        header.className = 'style-preview-card__header';

        const title = document.createElement('h4');
        title.textContent = formatLanguageLabel(preview.language_code || preview.language || preview.style);

        const count = document.createElement('span');
        count.className = 'style-preview-card__count';
        count.textContent = `${preview.total_captions} captions`;

        header.appendChild(title);
        header.appendChild(count);

        const list = document.createElement('div');
        list.className = 'style-preview-card__body';

        (preview.captions || []).forEach((caption, index) => {
            const item = document.createElement('div');
            item.className = 'style-preview-item';
            item.textContent = `${index + 1}. ${caption.text}`;
            list.appendChild(item);
        });

        card.appendChild(header);
        card.appendChild(list);
        stylePreviewGrid.appendChild(card);
    });
}

async function exportTranscript() {
    try {
        if (!state.transcriptJobId) {
            showError('No transcript is available to export yet.');
            return;
        }

        if (!state.selectedStyle) {
            showError('Please select a caption style.');
            return;
        }

        if (!state.selectedLanguages || state.selectedLanguages.length === 0) {
            showError('Please select at least one output language.');
            return;
        }

        exportTranscriptBtn.disabled = true;
        transcriptStatus.textContent = 'Exporting...';

        const segments = collectTranscriptSegments();
        const response = await fetch(`/transcripts/${state.transcriptJobId}/export`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                segments,
                style: state.selectedStyle,
                languages: state.selectedLanguages,
                language_code: state.primaryLanguage
            })
        });

        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'Export failed');
        }

        state.latestExport = result;
        state.transcript = result.transcript;
        transcriptStatus.textContent = 'Exported';
        updateUsageBanner(result);
        showExportResults(result);
    } catch (error) {
        transcriptStatus.textContent = 'Saved';
        showError(error.message);
    } finally {
        exportTranscriptBtn.disabled = false;
    }
}

function showExportResults(data) {
    progressSection.style.display = 'none';
    transcriptSection.style.display = 'block';
    stylePreviewSection.style.display = 'block';
    resultsSection.style.display = 'block';
    previewList.innerHTML = '';

    const results = data.results || [];
    if (results.length > 0) {
        state.selectedStyle = data.selected_style || state.selectedStyle;
        state.selectedLanguages = data.selected_languages || state.selectedLanguages;
        totalCaptionsEl.textContent = results.reduce((sum, result) => sum + (result.total_captions || 0), 0);
        selectedStyleEl.textContent = capitalize(state.selectedStyle);
        selectedLanguageEl.textContent = formatLanguageList(state.selectedLanguages);

        results.forEach((result, i) => {
            const title = document.createElement('h4');
            title.textContent = `Language: ${formatLanguageLabel(result.language)}`;
            previewList.appendChild(title);

            (result.captions || []).forEach((caption, idx) => {
                const item = document.createElement('div');
                item.className = 'preview-item';
                item.textContent = `${idx + 1}. ${caption.text}`;
                previewList.appendChild(item);
            });

            const download = document.createElement('button');
            download.className = 'btn btn--primary btn--sm';
            download.textContent = `Download SRT (${formatLanguageLabel(result.language)})`;
            download.addEventListener('click', () => {
                window.location.href = `/download/${result.srt_filename}`;
            });
            previewList.appendChild(download);

            if (i < results.length - 1) {
                const hr = document.createElement('hr');
                previewList.appendChild(hr);
            }
        });

        downloadBtn.onclick = () => {
            window.location.href = `/download/${results[0].srt_filename}`;
        };
        downloadBtn.style.display = 'inline-flex';
    } else {
        totalCaptionsEl.textContent = '0';
        selectedStyleEl.textContent = capitalize(state.selectedStyle);
        selectedLanguageEl.textContent = formatLanguageList(state.selectedLanguages);
        downloadBtn.style.display = 'none';
    }
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
        selectedStyle: 'meme',
        selectedLanguages: ['en'],
        primaryLanguage: 'en',
        languageOutputs: [],
        transcriptJobId: null,
        transcript: null,
        latestExport: null
    };
    videoInput.value = '';
    fileInfo.style.display = 'none';
    uploadArea.style.display = 'block';
    styleSection.style.display = 'none';
    languageSection.style.display = 'none';
    actionSection.style.display = 'none';
    progressSection.style.display = 'none';
    transcriptSection.style.display = 'none';
    stylePreviewSection.style.display = 'none';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
    generateBtn.disabled = false;
    saveTranscriptBtn.disabled = false;
    exportTranscriptBtn.disabled = false;
    downloadBtn.style.display = 'inline-flex';

    styleCards.forEach(card => card.classList.remove('selected'));
    styleChecks.forEach((cb, idx) => {
        cb.checked = (cb.value === 'meme');
        if (cb.value === 'meme') styleCards[idx].classList.add('selected');
    });

    Array.from(languageCheckboxes).forEach(checkbox => {
        checkbox.checked = checkbox.value === 'en';
    });
    syncLanguageSelection();
    transcriptEditor.innerHTML = '';
    transcriptMeta.textContent = 'Edit the raw transcript before exporting outputs.';
    transcriptStatus.textContent = 'Draft';
    stylePreviewGrid.innerHTML = '';
    previewList.innerHTML = '';
    totalCaptionsEl.textContent = '0';
    selectedStyleEl.textContent = capitalize(state.selectedStyle);
    selectedLanguageEl.textContent = 'English';
}

function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}
