/**
 * PDF Receipt Extractor - Frontend Logic
 * Handles drag-and-drop, file upload, and table management
 */

document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const tableBody = document.getElementById('tableBody');
    const resultsTable = document.getElementById('resultsTable');
    const emptyState = document.getElementById('emptyState');
    const clearBtn = document.getElementById('clearBtn');
    const copyAllBtn = document.getElementById('copyAllBtn');
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');

    // Drag and Drop handlers
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');

        const files = Array.from(e.dataTransfer.files).filter(
            file => file.type === 'application/pdf'
        );

        if (files.length === 0) {
            showToast('Please drop PDF files only', 'error');
            return;
        }

        processFiles(files);
    });

    // Click to upload
    dropZone.addEventListener('click', () => {
        if (!dropZone.classList.contains('processing')) {
            fileInput.click();
        }
    });

    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        if (files.length > 0) {
            processFiles(files);
        }
        fileInput.value = ''; // Reset for re-upload
    });

    // Clear all results
    clearBtn.addEventListener('click', () => {
        tableBody.innerHTML = '';
        updateTableVisibility();
        showToast('All results cleared', 'success');
    });

    // Copy all rows
    copyAllBtn.addEventListener('click', async () => {
        const rows = tableBody.querySelectorAll('tr');
        if (rows.length === 0) {
            showToast('No data to copy', 'error');
            return;
        }

        let text = 'Date\tDocument Name\tAmount\n';
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length >= 3) {
                text += `${cells[0].textContent}\t${cells[1].textContent}\t${cells[2].textContent}\n`;
            }
        });

        try {
            await navigator.clipboard.writeText(text.trim());
            showToast(`Copied ${rows.length} row(s) to clipboard!`, 'success');
        } catch (error) {
            const textarea = document.createElement('textarea');
            textarea.value = text.trim();
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            showToast(`Copied ${rows.length} row(s) to clipboard!`, 'success');
        }
    });

    /**
     * Process multiple PDF files
     */
    async function processFiles(files) {
        dropZone.classList.add('processing');

        for (const file of files) {
            try {
                await uploadAndExtract(file);
            } catch (error) {
                console.error('Error processing file:', error);
                showToast(`Error processing ${file.name}`, 'error');
            }
        }

        dropZone.classList.remove('processing');
    }

    /**
     * Upload single file and extract data
     */
    async function uploadAndExtract(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success && result.data) {
                addRowToTable(result.data);
                showToast(`Extracted data from ${file.name}`, 'success');
            } else {
                showToast(result.error || 'Extraction failed', 'error');
            }
        } catch (error) {
            throw new Error(`Upload failed: ${error.message}`);
        }
    }

    /**
     * Add a row to the results table
     */
    function addRowToTable(data) {
        const row = document.createElement('tr');

        row.innerHTML = `
            <td>${escapeHtml(data.date)}</td>
            <td title="${escapeHtml(data.docname)}">${escapeHtml(data.docname)}</td>
            <td>${escapeHtml(data.amount)}</td>
            <td>
                <button class="copy-btn" data-row='${JSON.stringify(data)}'>
                    📋 Copy Row
                </button>
            </td>
        `;

        // Add copy functionality
        const copyBtn = row.querySelector('.copy-btn');
        copyBtn.addEventListener('click', () => copyRow(copyBtn, data));

        tableBody.appendChild(row);
        updateTableVisibility();
    }

    /**
     * Copy row data to clipboard
     */
    async function copyRow(btn, data) {
        const text = `${data.date}\t${data.docname}\t${data.amount}`;

        try {
            await navigator.clipboard.writeText(text);

            // Visual feedback
            const originalText = btn.innerHTML;
            btn.innerHTML = '✓ Copied!';
            btn.classList.add('copied');

            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.classList.remove('copied');
            }, 2000);

            showToast('Row copied to clipboard!', 'success');
        } catch (error) {
            // Fallback for older browsers
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);

            showToast('Row copied to clipboard!', 'success');
        }
    }

    /**
     * Update table/empty state visibility
     */
    function updateTableVisibility() {
        const hasData = tableBody.children.length > 0;

        resultsTable.classList.toggle('has-data', hasData);
        emptyState.classList.toggle('hidden', hasData);
    }

    /**
     * Show toast notification
     */
    function showToast(message, type = 'success') {
        toastMessage.textContent = message;
        toast.className = 'toast';
        toast.classList.add('show', type);

        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(str) {
        if (!str) return 'N/A';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // Initialize
    updateTableVisibility();
});
