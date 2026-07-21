document.addEventListener('DOMContentLoaded', function () {
    const uploadBtn = document.getElementById('upload-btn');
    const fileInput = document.getElementById('file-input');
    const summarizeBtn = document.getElementById('summarize-btn');
    const recBtn = document.getElementById('recommendations-btn');
    const notesContent = document.getElementById('notes-content');
    const summaryContent = document.getElementById('summary-content');
    const summaryViewArea = document.getElementById('summary-view-area');
    const summaryTitle = document.getElementById('summary-title');

    // --- FILE UPLOAD ---
    if (uploadBtn && fileInput) {
        uploadBtn.addEventListener('click', function () {
            fileInput.click();
        });

        fileInput.addEventListener('change', function () {
            const file = fileInput.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);
            const poolId = fileInput.dataset.poolId;
            if (poolId && poolId !== '0') {
                formData.append('group_id', poolId);
            }

            uploadBtn.disabled = true;
            const btnText = uploadBtn.querySelector('.btn-text');
            if (btnText) btnText.textContent = 'Uploading...';

            fetch('/upload', { method: 'POST', body: formData })
                .then(res => res.json())
                .then(data => {
                    window.location.reload();
                })
                .catch(() => {
                    if (notesContent) {
                        notesContent.innerHTML = `<p class="placeholder-text">Upload failed. Please try again.</p>`;
                    } else {
                        alert("Upload failed. Please try again.");
                    }
                })
                .finally(() => {
                    uploadBtn.disabled = false;
                    if (btnText) btnText.textContent = 'Upload Doc';
                    fileInput.value = '';
                });
        });
    }

    // --- SUMMARIZE ---
    if (summarizeBtn) {
        let isProcessing = false;
        const fallbackIcon = summarizeBtn.querySelector('.btn-icon') ? summarizeBtn.querySelector('.btn-icon').outerHTML : '<span class="btn-icon">&#9776;</span>';

        summarizeBtn.addEventListener('click', function (e) {
            e.preventDefault();

            if (isProcessing || summarizeBtn.disabled) return;

            isProcessing = true;
            summarizeBtn.disabled = true;
            summarizeBtn.innerHTML = '<span class="btn-icon">&#9776;</span> <span class="btn-text">Summarizing...</span>';

            const poolId = fileInput ? fileInput.dataset.poolId : null;
            const parsedPoolId = poolId && poolId !== '0' ? parseInt(poolId, 10) : null;

            fetch('/api/summarize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ group_id: parsedPoolId })
            })
            .then(res => res.json())
            .then(data => {
                resetButtonState();

                if (data.success) {
                    if (summaryTitle) summaryTitle.textContent = "Summary Results";

                    if (summaryViewArea) summaryViewArea.style.display = 'block';
                    if (summaryContent) summaryContent.style.display = 'block';

                    if (Array.isArray(data.summary)) {
                        let htmlContent = data.summary.map(item => `
                            <div style="margin-bottom: 16px;">
                                <strong style="font-size: 1.05rem; display: block; margin-bottom: 4px;">${item.note_name || 'Note'}</strong>
                                <p style="margin: 0; line-height: 1.5; opacity: 0.9;">${item.summary}</p>
                            </div>
                        `).join('<hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.1); margin: 12px 0;">');

                        if (summaryContent) summaryContent.innerHTML = htmlContent;
                    } else if (typeof data.summary === 'string') {
                        if (summaryContent) summaryContent.textContent = data.summary;
                    }
                } else {
                    alert(data.error || "Could not generate summary.");
                }
            })
            .catch(() => {
                alert("Summarization failed. Please check your connection.");
                resetButtonState();
            });
        });

        function resetButtonState() {
            isProcessing = false;
            summarizeBtn.disabled = false;
            summarizeBtn.style.opacity = '1';
            summarizeBtn.style.cursor = 'pointer';
            summarizeBtn.innerHTML = `${fallbackIcon} <span class="btn-text">Summarize Notes</span>`;
        }
    }

    // --- RECOMMENDATIONS ---
    if (recBtn) {
        let isRecProcessing = false;
        const recIcon = recBtn.querySelector('.btn-icon') ? recBtn.querySelector('.btn-icon').outerHTML : '<span class="btn-icon">&#128366;&#65038;</span>';

        recBtn.addEventListener('click', function (e) {
            e.preventDefault();
            if (isRecProcessing || recBtn.disabled) return;

            isRecProcessing = true;
            recBtn.disabled = true;
            recBtn.innerHTML = `${recIcon} <span class="btn-text">Finding Books...</span>`;

            const poolId = fileInput ? fileInput.dataset.poolId : null;
            const parsedPoolId = poolId && poolId !== '0' ? parseInt(poolId, 10) : null;

            fetch('/api/recommendations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ group_id: parsedPoolId })
            })
            .then(res => res.json())
            .then(data => {
                isRecProcessing = false;
                recBtn.disabled = false;
                recBtn.innerHTML = `${recIcon} <span class="btn-text">Source Search</span>`;

                if (data.success && data.recommendations) {
                    // Save data and redirect to the new recommendations webpage
                    localStorage.setItem('recommendations_data', JSON.stringify(data.recommendations));
                    window.location.href = '/recommendations';
                } else {
                    alert(data.error || "Could not load recommendations.");
                }
            })
            .catch(() => {
                isRecProcessing = false;
                recBtn.disabled = false;
                recBtn.innerHTML = `${recIcon} <span class="btn-text">Get Recommendations</span>`;
                alert("Recommendations request failed. Please try again.");
            });
        });
    }
});

// Dropdown Toggle
window.toggleDropdown = function() {
    const dropdown = document.getElementById("myDropdown");
    if (dropdown) {
        dropdown.style.display = (dropdown.style.display === "none" || dropdown.style.display === "") ? "block" : "none";
    }
};

window.addEventListener('click', function(event) {
    if (!event.target.matches('.menu-trigger') && !event.target.matches('.three-dots')) {
        const dropdown = document.getElementById("myDropdown");
        if (dropdown) {
            dropdown.style.display = "none";
        }
    }
});