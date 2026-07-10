document.addEventListener('DOMContentLoaded', function () {
    const uploadBtn = document.getElementById('upload-btn');
    const fileInput = document.getElementById('file-input');
    const summarizeBtn = document.getElementById('summarize-btn');
    const notesContent = document.getElementById('notes-content');
    const summaryContent = document.getElementById('summary-content');

    if (uploadBtn) {
        uploadBtn.addEventListener('click', function () {
            fileInput.click();
        });

        fileInput.addEventListener('change', function () {
            const file = fileInput.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);
            const poolId = fileInput.dataset.poolId;
            if (poolId) {
                formData.append('group_id', poolId);
            }

            uploadBtn.disabled = true;
            uploadBtn.querySelector('.btn-text').textContent = 'Uploading...';

            fetch('/upload', { method: 'POST', body: formData })
                .then(res => res.json())
                .then(data => {
                    window.location.reload()
                    // notesContent.innerHTML = `<p class="placeholder-text">Uploaded: <strong>${file.name}</strong></p>`;
                })
                .catch(() => {
                    notesContent.innerHTML = `<p class="placeholder-text">Upload failed. Please try again.</p>`;
                })
                .finally(() => {
                    uploadBtn.disabled = false;
                    uploadBtn.querySelector('.btn-text').textContent = 'Upload Doc';
                    fileInput.value = '';
                });
        });
    }

   if (summarizeBtn) {
        summarizeBtn.addEventListener('click', function () {
            summarizeBtn.disabled = true;
            summarizeBtn.querySelector('.btn-text').textContent = 'Summarizing...';

            fetch('/api/summarize', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    summaryContent.style.display = 'block';
                    if (data.success) {
                        const items = data.summary.map(item => `
                            <div>
                                <strong>${item.note_name}</strong>
                                <p>${item.summary}</p>
                            </div>
                        `).join('<hr>');
                        summaryContent.innerHTML = `<h3>Summary</h3>${items}`;
                    } else {
                        summaryContent.innerHTML = `<p class="placeholder-text" style="color: #dc2626;">Error: ${data.error || 'Could not generate summary.'}</p>`;
                    }
                })
                .catch(() => {
                    summaryContent.style.display = 'block';
                    summaryContent.innerHTML = `<p class="placeholder-text">Summarization failed. Please try again.</p>`;
                })
                .finally(() => {
                    summarizeBtn.disabled = false;
                    summarizeBtn.querySelector('.btn-text').textContent = 'Summarize Notes';
                });
        });
    }
});

function navigateTo(viewId) {
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    document.getElementById(viewId + '-view').classList.add('active');
    document.getElementById('myDropdown').classList.remove('show');
}

function toggleDropdown() {
    document.getElementById('myDropdown').classList.toggle('show');
}

window.onclick = function (event) {
    if (!event.target.matches('.menu-trigger') && !event.target.matches('.three-dots')) {
        document.querySelectorAll('.dropdown-content').forEach(dropdown => {
            dropdown.classList.remove('show');
        });
    }
};
