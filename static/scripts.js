        /* ══════════════════════════════════════════════════════════
           PRESENTATION CONTROLLER
           ══════════════════════════════════════════════════════════ */
        const PPT = (() => {
            const TOTAL = 8;
            let current = 0;

            const wrapper    = document.getElementById('pptWrapper');
            const stage      = document.getElementById('pptStage');
            const slides     = document.getElementById('pptSlides');
            const dotsBox    = document.getElementById('pptDots');
            const counter    = document.getElementById('pptCounter');
            const prevBtn    = document.getElementById('prevSlide');
            const nextBtn    = document.getElementById('nextSlide');
            const fsBtn      = document.getElementById('toggleFullscreen');
            const minBtn     = document.getElementById('minimizePpt');

            // Build dot indicators
            for (let i = 0; i < TOTAL; i++) {
                const dot = document.createElement('button');
                dot.className = 'ppt-dot' + (i === 0 ? ' active' : '');
                dot.setAttribute('aria-label', `Go to slide ${i + 1}`);
                dot.addEventListener('click', () => goTo(i));
                dotsBox.appendChild(dot);
            }

            function goTo(idx) {
                if (idx < 0 || idx >= TOTAL) return;
                current = idx;
                requestAnimationFrame(() => {
                    slides.style.transform = `translateX(-${current * 100}%)`;
                    counter.textContent = `${current + 1} / ${TOTAL}`;
                    prevBtn.disabled = current === 0;
                    nextBtn.disabled = current === TOTAL - 1;
                    dotsBox.querySelectorAll('.ppt-dot').forEach((d, i) => {
                        d.classList.toggle('active', i === current);
                    });
                });
            }

            prevBtn.addEventListener('click', () => goTo(current - 1));
            nextBtn.addEventListener('click', () => goTo(current + 1));

            // Keyboard navigation
            document.addEventListener('keydown', e => {
                if (e.key === 'ArrowLeft')  goTo(current - 1);
                if (e.key === 'ArrowRight') goTo(current + 1);
                if (e.key === 'Escape' && wrapper.classList.contains('fullscreen')) toggleFS();
            });

            // Fullscreen
            function toggleFS() {
                wrapper.classList.toggle('fullscreen');
                fsBtn.textContent = wrapper.classList.contains('fullscreen') ? '✕' : '⛶';
                document.body.style.overflow = wrapper.classList.contains('fullscreen') ? 'hidden' : '';
            }
            fsBtn.addEventListener('click', toggleFS);

            // Minimize / restore
            let minimized = false;
            minBtn.addEventListener('click', () => {
                minimized = !minimized;
                stage.style.display = minimized ? 'none' : '';
                document.getElementById('pptNav').style.display = minimized ? 'none' : '';
                minBtn.textContent = minimized ? '+' : '−';
            });

            // Init
            goTo(0);

            return { goTo };
        })();

        function closePpt() {
            const stage = document.getElementById('pptStage');
            const nav   = document.getElementById('pptNav');
            const min   = document.getElementById('minimizePpt');
            stage.style.display = 'none';
            nav.style.display   = 'none';
            min.textContent     = '+';
        }

        /* ══════════════════════════════════════════════════════════
           DOCUMENT UPLOAD & PROCESSING
           ══════════════════════════════════════════════════════════ */
        let lastResults = null;

        /* ── DOM refs ─────────────────────────────────────────── */
        const uploadArea = document.getElementById('uploadArea');
        const fileInput  = document.getElementById('fileInput');
        const fileName   = document.getElementById('fileName');

        /* ── Drag & Drop ──────────────────────────────────────── */
        uploadArea.addEventListener('dragover', e => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });
        uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('drag-over'));
        uploadArea.addEventListener('drop', e => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            fileInput.files = e.dataTransfer.files;
            showFileName(fileInput.files[0]);
        });
        uploadArea.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', () => {
            if (fileInput.files[0]) showFileName(fileInput.files[0]);
        });

        function showFileName(file) {
            if (!file) return;
            fileName.textContent = `📎 ${file.name}  (${(file.size / 1024).toFixed(1)} KB)`;
            fileName.classList.add('show');
        }

        /* ── Form submit ──────────────────────────────────────── */
        document.getElementById('uploadForm').addEventListener('submit', async e => {
            e.preventDefault();
            const file = fileInput.files[0];
            if (!file) { showError('Please select a file first.'); return; }

            const formData = new FormData();
            formData.append('file', file);

            setLoading(true);
            hideError();
            document.getElementById('results').classList.remove('show');

            try {
                const res = await fetch('/upload', { method: 'POST', body: formData });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Processing failed');
                displayResults(data);
                lastResults = data;
            } catch (err) {
                showError('Error: ' + err.message);
            } finally {
                setLoading(false);
            }
        });

        /* ── Display helpers (optimized: batched DOM) ─────────── */
        function displayResults(data) {
            const tbody = document.getElementById('resultsBody');
            const labels = { name: 'Name', amount: 'Amount', date: 'Date', invoice_id: 'Invoice / Doc ID' };

            // Build all rows as fragment to batch DOM write
            const frag = document.createDocumentFragment();
            for (const [field, value] of Object.entries(data.data)) {
                const status = data.validation[field] || 'invalid';
                const badgeClass = status === 'valid' ? 'badge-valid'
                                 : status === 'warning' ? 'badge-warning'
                                 : 'badge-invalid';
                const icon = status === 'valid' ? '✓' : status === 'warning' ? '⚠' : '✗';

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${labels[field] || field}</td>
                    <td>${value}</td>
                    <td><span class="badge ${badgeClass}">${icon} ${status}</span></td>`;
                frag.appendChild(tr);
            }
            tbody.innerHTML = '';
            tbody.appendChild(frag);

            document.getElementById('metaInfo').textContent =
                `Processed in ${data.processing_time || '—'}`;

            if (data.raw_text) {
                document.getElementById('rawText').textContent = data.raw_text;
            }

            document.getElementById('results').classList.add('show');
        }

        function setLoading(on) { document.getElementById('loading').classList.toggle('show', on); }
        function showError(msg) {
            const el = document.getElementById('errorMsg');
            el.textContent = msg; el.classList.add('show');
        }
        function hideError() { document.getElementById('errorMsg').classList.remove('show'); }

        function clearForm() {
            fileInput.value = '';
            fileName.classList.remove('show');
            document.getElementById('results').classList.remove('show');
            hideError();
        }

        function toggleRaw() {
            const raw = document.getElementById('rawText');
            const toggle = document.getElementById('rawToggle');
            const open = raw.classList.toggle('show');
            toggle.textContent = open ? '▾ Hide raw OCR text' : '▸ Show raw OCR text';
        }

        function downloadJSON() {
            if (!lastResults) return;
            const blob = new Blob([JSON.stringify(lastResults, null, 2)], { type: 'application/json' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'extraction_result.json';
            a.click();
            URL.revokeObjectURL(a.href);
        }
