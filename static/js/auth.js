document.addEventListener('DOMContentLoaded', function () {
    const uploadBtn = document.getElementById('upload-btn');
    const fileInput = document.getElementById('file-input');
    const summarizeBtn = document.getElementById('summarize-btn');
    const notesContent = document.getElementById('notes-content');
    const summaryContent = document.getElementById('summary-content');

    const bookFeed = document.getElementById('book-feed');

    if (bookFeed) {
        fetch('/api/recommendations', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    allRecommendations = data.recommendations;
                    renderBooks(allRecommendations);
                } else {
                    bookFeed.innerHTML = `<p class="placeholder-text" style="color: #dc2626;">Error: ${data.error || 'Could not load recommendations.'}</p>`;
                }
            })
            .catch(() => {
                bookFeed.innerHTML = '<p class="placeholder-text">Could not load recommendations. Please try again.</p>';
            });
    }

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
    // A simple flag to absolutely lock out secondary threads
    let isProcessing = false;

    summarizeBtn.addEventListener('click', function (e) {
        e.preventDefault();

        // If it's already running, drop the click immediately!
        if (isProcessing || summarizeBtn.disabled) return;

        // Lock it down instantly
        isProcessing = true;
        summarizeBtn.disabled = true;
        summarizeBtn.innerHTML = '<span class="btn-icon">☰</span> <span class="btn-text">Summarizing...</span>';

        const poolId = fileInput ? fileInput.dataset.poolId : null;

        fetch('/api/summarize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ group_id: poolId ? parseInt(poolId) : null })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            } else {
                alert(data.error || "Could not generate summary.");
                resetButtonState();
            }
        })
        .catch(() => {
            alert("Summarization failed.");
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
/*
   if (summarizeBtn) {
        summarizeBtn.addEventListener('click', function () {
            summarizeBtn.disabled = true;
            summarizeBtn.innerHTML = '<span class="btn-icon">☰</span><span class="btn-text">Summarizing...</span>';

            const poolId = fileInput ? fileInput.dataset.poolId : null;

            fetch('/api/summarize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body:JSON.stringify({group_id: poolId})
                })
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
*/

// Global drop down visibility controller function pinned directly to the root window object context
window.toggleDropdown = function() {
    const dropdown = document.getElementById("myDropdown");
    if (dropdown) {
        if (dropdown.style.display === "none" || dropdown.style.display === "") {
            dropdown.style.display = "block";
        } else {
            dropdown.style.display = "none";
        }
    }
};

// Global tap intercept listener setup to collapse the dropdown box if users click away
window.addEventListener('click', function(event) {
    if (!event.target.matches('.menu-trigger') && !event.target.matches('.three-dots')) {
        const dropdown = document.getElementById("myDropdown");
        if (dropdown) {
            dropdown.style.display = "none";
        }
    }
});

let allRecommendations = [];

function renderBooks(books) {
    const bookFeed = document.getElementById('book-feed');
    if (!bookFeed) return;
    if (!books || books.length === 0) {
        bookFeed.innerHTML = '<p class="placeholder-text">No recommendations found.</p>';
        return;
    }
    bookFeed.innerHTML = books.map(book => `
        <div class="book-card">
            <strong>${book.title}</strong>
            <p class="book-authors">${book.authors.join(', ')}</p>
            <p>${book.description || 'No description available.'}</p>
            ${book.preview_link ? `<a href="${book.preview_link}" target="_blank" class="preview-link">Preview</a>` : ''}
        </div>
    `).join('');
}

function runLiveSearch() {
    const query = document.getElementById('search-input').value.toLowerCase();
    const filtered = allRecommendations.filter(book =>
        book.title.toLowerCase().includes(query) ||
        (book.description && book.description.toLowerCase().includes(query)) ||
        book.authors.some(a => a.toLowerCase().includes(query))
    );
    renderBooks(filtered);
}

function toggleLayoutMode() {
    const bookFeed = document.getElementById('book-feed');
    bookFeed.classList.toggle('book-list');
    bookFeed.classList.toggle('book-grid');
}