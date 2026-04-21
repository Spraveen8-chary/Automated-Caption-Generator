// State management
let state = {
    uploadedFile: null,
    uploadedFilename: null,
    selectedStyle: 'meme',
    selectedLanguages: ['en'],
    primaryLanguage: 'en',
    transcriptionProvider: null,
    languageOutputs: [],
    transcriptJobId: null,
    transcript: null,
    latestExport: null
};

const appConfig = window.APP_CONFIG || {};
const burnedVideoEnabled = Boolean(appConfig.enableBurnedVideo);

function getConfiguredFreeLimit(data = {}) {
    const fromData = Number(data.free_user_video_limit);
    if (Number.isFinite(fromData) && fromData > 0) {
        return fromData;
    }

    const fromConfig = Number(appConfig.freeUserVideoLimit);
    if (Number.isFinite(fromConfig) && fromConfig > 0) {
        return fromConfig;
    }

    return 0;
}

async function readJsonResponse(response) {
    const text = await response.text();
    if (!text) {
        return null;
    }

    try {
        return JSON.parse(text);
    } catch (error) {
        return { raw: text };
    }
}

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
const selectedProviderEl = document.getElementById('selectedProvider');
const downloadBtn = document.getElementById('downloadBtn');
const newVideoBtn = document.getElementById('newVideoBtn');
const defaultDownloadBtnHtml = downloadBtn ? downloadBtn.innerHTML : '';

const usageHeading = document.querySelector('.usage-text h3');
const usageParagraph = document.querySelector('.usage-text p');
const usageFill = document.querySelector('.progress-bar-mini__fill');
const usageUpdate = document.getElementById('usageUpdate');
const videosProcessedCount = document.getElementById('videosProcessedCount');
const videosLimitCount = document.getElementById('videosLimitCount');
const remainingCount = document.getElementById('remainingCount');

const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');
const retryBtn = document.getElementById('retryBtn');

const paymentModal = document.getElementById('paymentModal');
const paymentQrCode = document.getElementById('paymentQrCode');
const paymentQrFallback = document.getElementById('paymentQrFallback');
const paymentReference = document.getElementById('paymentReference');
const paymentStatus = document.getElementById('paymentStatus');
const markPaidBtn = document.getElementById('markPaidBtn');

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

function getPaymentRequestState() {
    return appConfig.paymentRequest || null;
}

function openPaymentModal() {
    if (!paymentModal) return;
    paymentModal.style.display = 'flex';
    renderPaymentQr();
    updatePaymentModalState();
}

function closePaymentModal() {
    if (!paymentModal) return;
    paymentModal.style.display = 'none';
}

function renderPaymentQr() {
    if (!paymentQrCode) return;

    if (paymentQrFallback) {
        paymentQrFallback.textContent = 'Scan the QR or open the UPI link.';
    }
}

function updatePaymentModalState() {
    const request = getPaymentRequestState();
    if (!markPaidBtn) return;

    if (!request) {
        markPaidBtn.disabled = false;
        markPaidBtn.textContent = 'I have paid';
        return;
    }

    if (request.status === 'pending') {
        markPaidBtn.disabled = true;
        markPaidBtn.textContent = 'Payment Pending';
        if (paymentStatus) {
            paymentStatus.className = 'payment-status payment-status--pending';
            paymentStatus.textContent = 'Your payment request is waiting for admin approval.';
        }
        return;
    }

    if (request.status === 'approved') {
        markPaidBtn.disabled = true;
        markPaidBtn.textContent = 'Premium Activated';
        if (paymentStatus) {
            paymentStatus.className = 'payment-status payment-status--approved';
            paymentStatus.textContent = `Premium approved. Your limit is now ${appConfig.premiumVideoLimit || '50'} videos.`;
        }
        return;
    }

    if (request.status === 'rejected') {
        markPaidBtn.disabled = false;
        markPaidBtn.textContent = 'I have paid';
        if (paymentStatus) {
            paymentStatus.className = 'payment-status payment-status--rejected';
            paymentStatus.textContent = 'Your last payment request was rejected. Please submit a new one.';
        }
    }
}

async function submitPaymentRequest() {
    try {
        if (!markPaidBtn) return;

        markPaidBtn.disabled = true;
        markPaidBtn.textContent = 'Sending...';

        const response = await fetch('/payments/request', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                payment_reference: paymentReference ? paymentReference.value.trim() : ''
            })
        });

        const result = await readJsonResponse(response);
        if (!result) {
            throw new Error('Payment request returned an empty response');
        }
        if (!response.ok) {
            throw new Error((result && result.error) || 'Could not submit payment request');
        }

        appConfig.paymentRequest = result.payment_request || appConfig.paymentRequest;
        if (paymentStatus) {
            paymentStatus.className = 'payment-status payment-status--pending';
            paymentStatus.textContent = result.message || 'Payment request sent to admin for approval.';
        }
        if (paymentReference) {
            paymentReference.value = '';
        }
        updatePaymentModalState();
        markPaidBtn.textContent = 'Request Sent';
    } catch (error) {
        if (markPaidBtn) {
            markPaidBtn.disabled = false;
            markPaidBtn.textContent = 'I have paid';
        }
        if (paymentStatus) {
            paymentStatus.className = 'payment-status payment-status--rejected';
            paymentStatus.textContent = error.message;
        }
        console.error('payment.request.failed', error);
        alert(error.message || 'Could not submit payment request');
    }
}

function initializePaymentModal() {
    updatePaymentModalState();
}

if (markPaidBtn) {
    markPaidBtn.addEventListener('click', submitPaymentRequest);
}

window.openPaymentModal = openPaymentModal;
window.closePaymentModal = closePaymentModal;
window.submitPaymentRequest = submitPaymentRequest;

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
initializePaymentModal();

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
            const error = await readJsonResponse(uploadResponse);
            throw new Error((error && (error.error || error.raw)) || 'Upload failed');
        }
        const uploadData = await readJsonResponse(uploadResponse);
        if (!uploadData) {
            throw new Error('Upload returned an empty response');
        }
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
            const error = await readJsonResponse(processResponse);
            throw new Error((error && (error.error || error.raw)) || 'Processing failed');
        }

        const processData = await readJsonResponse(processResponse);
        if (!processData) {
            throw new Error('Processing returned an empty response');
        }
        state.transcriptJobId = processData.transcript_job_id;
        state.transcript = processData.transcript;
        state.languageOutputs = processData.outputs || [];
        state.selectedStyle = processData.selected_style || state.selectedStyle;
        state.selectedLanguages = processData.selected_languages || state.selectedLanguages;
        state.primaryLanguage = processData.primary_language || state.selectedLanguages[0];
        state.latestExport = null;
        updateUsageBanner(processData);

        updateProgress(100, processData.message || 'Transcript ready!');
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

    const configuredLimit = Number(data.active_video_limit);
    const freeLimit = getConfiguredFreeLimit(data);
    const hasFiniteLimit = Number.isFinite(configuredLimit) && configuredLimit > 0;
    const effectiveLimit = hasFiniteLimit ? configuredLimit : (data.is_premium ? null : freeLimit);
    const planLabel = data.plan_label || (data.is_premium ? 'Premium Account' : 'Free Account');

    if (usageHeading) {
        usageHeading.textContent = planLabel;
    }

    if (usageParagraph) {
        if (typeof data.videos_processed !== 'undefined') {
            usageParagraph.textContent = `${data.videos_processed} of ${effectiveLimit === null ? 'Unlimited' : effectiveLimit} videos used`;
        }
    }

    if (usageUpdate && typeof data.videos_processed !== 'undefined') {
        usageUpdate.style.display = 'block';
        const processedCount = Number(data.videos_processed || 0);
        const videosRemaining = typeof data.videos_remaining !== 'undefined'
            ? data.videos_remaining
            : (effectiveLimit === null ? 'Unlimited' : Math.max(effectiveLimit - processedCount, 0));

        if (videosProcessedCount) {
            videosProcessedCount.textContent = String(processedCount);
        }

        if (videosLimitCount) {
            videosLimitCount.textContent = effectiveLimit === null ? 'Unlimited' : String(effectiveLimit);
        }

        if (remainingCount) {
            remainingCount.textContent = String(videosRemaining);
        }

    }

    if (usageFill && typeof data.videos_processed !== 'undefined') {
        if (effectiveLimit === null) {
            usageFill.style.width = '100%';
        } else {
            usageFill.style.width = `${Math.min((Number(data.videos_processed) / effectiveLimit) * 100, 100)}%`;
        }
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
    state.transcriptionProvider = data.transcription_provider || state.transcriptionProvider || appConfig.transcriptionProvider || null;
    transcriptMeta.textContent = `${transcript.original_filename} | ${transcript.segments.length} segments | ${formatLanguageLabel(primaryLanguage)} | ${formatLanguageList(state.selectedLanguages)} | ${formatProviderLabel(state.transcriptionProvider)}`;
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

        const result = await readJsonResponse(response);
        if (!result) {
            throw new Error('Save returned an empty response');
        }
        if (!response.ok) {
            throw new Error((result && (result.error || result.raw)) || 'Save failed');
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

        const result = await readJsonResponse(response);
        if (!result) {
            throw new Error('Style preview returned an empty response');
        }
        if (!response.ok) {
            throw new Error((result && (result.error || result.raw)) || 'Style preview failed');
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

        const result = await readJsonResponse(response);
        if (!result) {
            throw new Error('Export returned an empty response');
        }
        if (!response.ok) {
            throw new Error((result && (result.error || result.raw)) || 'Export failed');
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
        state.transcriptionProvider = data.transcription_provider || state.transcriptionProvider || appConfig.transcriptionProvider || null;
        totalCaptionsEl.textContent = results.reduce((sum, result) => sum + (result.total_captions || 0), 0);
        selectedStyleEl.textContent = capitalize(state.selectedStyle);
        selectedLanguageEl.textContent = formatLanguageList(state.selectedLanguages);
        if (selectedProviderEl) {
            selectedProviderEl.textContent = formatProviderLabel(state.transcriptionProvider);
        }

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

            if (burnedVideoEnabled && result.burned_video_filename) {
                const downloadVideo = document.createElement('button');
                downloadVideo.className = 'btn btn--secondary btn--sm';
                downloadVideo.textContent = `Download Video (${formatLanguageLabel(result.language)})`;
                downloadVideo.addEventListener('click', () => {
                    window.location.href = `/download/${result.burned_video_filename}`;
                });
                previewList.appendChild(downloadVideo);
            }

            if (i < results.length - 1) {
                const hr = document.createElement('hr');
                previewList.appendChild(hr);
            }
        });

        downloadBtn.onclick = () => {
            const primaryResult = results[0];
            const filename = burnedVideoEnabled && primaryResult.burned_video_filename
                ? primaryResult.burned_video_filename
                : primaryResult.srt_filename;
            window.location.href = `/download/${filename}`;
        };
        downloadBtn.innerHTML = burnedVideoEnabled && results[0].burned_video_filename
            ? `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>Download Captioned Video`
            : `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>Download SRT File`;
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
        transcriptionProvider: null,
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
    if (usageUpdate) usageUpdate.style.display = 'none';
    generateBtn.disabled = false;
    saveTranscriptBtn.disabled = false;
    exportTranscriptBtn.disabled = false;
    downloadBtn.innerHTML = defaultDownloadBtnHtml;
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

function formatProviderLabel(provider) {
    const value = String(provider || '').trim().toLowerCase();
    if (!value) return 'Configured Provider';
    if (value === 'assemblyai') return 'AssemblyAI';
    if (value === 'whisper') return 'Whisper';
    if (value === 'gemini') return 'Gemini';
    return value.charAt(0).toUpperCase() + value.slice(1);
}
