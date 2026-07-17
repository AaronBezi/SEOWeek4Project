document.addEventListener('DOMContentLoaded', function () {
    const uploadBtn = document.getElementById('upload-btn');
    const fileInput = document.getElementById('file-input');
    const summarizeBtn = document.getElementById('summarize-btn');
    const notesContent = document.getElementById('notes-content');
    const summaryContent = document.getElementById('summary-content');

    // WIRE FRAMED FUNCTIONS IN RECOMMENDATIONS.HTML DELETE THIS COMMENT ONCE DONE
    const bookFeed = document.getElementById('book-feed');

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
            <strong>${book.subject}</strong>
            <p>${book.summary}</p>
            <div class="book-tags">
                ${book.topics.map(t => `<span class="tag">${t}</span>`).join('')}
            </div>
        </div>
    `).join('');
}

function runLiveSearch() {
    const query = document.getElementById('search-input').value.toLowerCase();
    const filtered = allRecommendations.filter(book =>
        book.subject.toLowerCase().includes(query) ||
        book.summary.toLowerCase().includes(query) ||
        book.topics.some(t => t.toLowerCase().includes(query)) ||
        book.keywords.some(k => k.toLowerCase().includes(query))
    );
    renderBooks(filtered);
}

function toggleLayoutMode() {
    const bookFeed = document.getElementById('book-feed');
    bookFeed.classList.toggle('book-list');
    bookFeed.classList.toggle('book-grid');
}
