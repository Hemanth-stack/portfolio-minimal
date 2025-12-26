/**
 * Inline Section Editor
 * Enables pencil-icon editing for sections when admin is logged in
 */

class InlineEditor {
    constructor() {
        this.activeEditor = null;
        this.originalContent = null;
        this.init();
    }

    init() {
        // Add click handlers to all edit buttons
        document.querySelectorAll('.edit-section-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.openEditor(e));
        });

        // Close editor on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.activeEditor) {
                this.closeEditor(false);
            }
        });
    }

    openEditor(e) {
        const btn = e.currentTarget;
        const section = btn.closest('.editable-section');
        const sectionId = section.dataset.sectionId;
        const page = section.dataset.page;
        const sectionKey = section.dataset.sectionKey;
        const contentDiv = section.querySelector('.section-content');

        // Close any existing editor
        if (this.activeEditor) {
            this.closeEditor(false);
        }

        // Store original content
        this.originalContent = contentDiv.innerHTML;
        this.activeEditor = section;

        // Get raw markdown from server
        fetch(`/api/section/${page}/${sectionKey}`)
            .then(res => res.json())
            .then(data => {
                this.showEditorUI(section, contentDiv, data.content, data.title);
            })
            .catch(err => {
                console.error('Failed to load section:', err);
                alert('Failed to load section content');
            });
    }

    showEditorUI(section, contentDiv, markdown, title) {
        const page = section.dataset.page;
        const sectionKey = section.dataset.sectionKey;

        // Create editor UI
        const editorHTML = `
            <div class="inline-editor">
                <div class="editor-header">
                    <input type="text" class="editor-title" value="${this.escapeHtml(title)}" placeholder="Section title">
                    <div class="editor-actions">
                        <button type="button" class="btn btn-save">Save</button>
                        <button type="button" class="btn btn-secondary btn-cancel">Cancel</button>
                    </div>
                </div>
                <textarea class="editor-content">${this.escapeHtml(markdown)}</textarea>
                <div class="editor-preview">
                    <div class="preview-label">Preview</div>
                    <div class="preview-content"></div>
                </div>
            </div>
        `;

        contentDiv.innerHTML = editorHTML;

        const textarea = contentDiv.querySelector('.editor-content');
        const preview = contentDiv.querySelector('.preview-content');
        const titleInput = contentDiv.querySelector('.editor-title');
        const saveBtn = contentDiv.querySelector('.btn-save');
        const cancelBtn = contentDiv.querySelector('.btn-cancel');

        // Update preview on input
        const updatePreview = () => {
            fetch('/api/markdown', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: textarea.value })
            })
            .then(res => res.json())
            .then(data => {
                preview.innerHTML = data.html;
            });
        };

        textarea.addEventListener('input', this.debounce(updatePreview, 300));
        updatePreview();

        // Auto-resize textarea
        textarea.style.height = 'auto';
        textarea.style.height = Math.max(200, textarea.scrollHeight) + 'px';
        textarea.addEventListener('input', () => {
            textarea.style.height = 'auto';
            textarea.style.height = textarea.scrollHeight + 'px';
        });

        // Save handler
        saveBtn.addEventListener('click', () => {
            this.saveSection(page, sectionKey, textarea.value, titleInput.value);
        });

        // Cancel handler
        cancelBtn.addEventListener('click', () => {
            this.closeEditor(false);
        });

        // Focus textarea
        textarea.focus();

        // Hide edit button while editing
        section.querySelector('.edit-section-btn').style.display = 'none';
    }

    async saveSection(page, sectionKey, content, title) {
        try {
            const response = await fetch(`/api/section/${page}/${sectionKey}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content, title })
            });

            if (response.ok) {
                const data = await response.json();
                this.closeEditor(true, data.html);
            } else {
                const error = await response.json();
                alert('Failed to save: ' + (error.detail || 'Unknown error'));
            }
        } catch (err) {
            console.error('Save failed:', err);
            alert('Failed to save section');
        }
    }

    closeEditor(saved, newContent = null) {
        if (!this.activeEditor) return;

        const section = this.activeEditor;
        const contentDiv = section.querySelector('.section-content');

        if (saved && newContent) {
            contentDiv.innerHTML = newContent;
        } else {
            contentDiv.innerHTML = this.originalContent;
        }

        // Show edit button again
        section.querySelector('.edit-section-btn').style.display = '';

        this.activeEditor = null;
        this.originalContent = null;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.editable-section')) {
        new InlineEditor();
    }
});
