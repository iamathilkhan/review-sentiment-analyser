/**
 * emotion_detect.js
 * Handles live NLP emotion detection as the user types a review.
 */

(function () {
    'use strict';

    function initEmotionDetectors() {
        const forms = document.querySelectorAll('.review-form');
        
        forms.forEach(form => {
            const productId = form.dataset.productId;
            const textarea = document.getElementById(`review-content-${productId}`);
            const emotionContainer = document.getElementById(`emotion-suggester-${productId}`);
            const emotionPills = document.getElementById(`emotion-pills-${productId}`);
            const confirmedInput = document.getElementById(`confirmed_emotions-${productId}`);
            const predictUrl = form.dataset.predictUrl || '/dashboard/predict_emotion';

            if (!textarea || !emotionContainer || !emotionPills) return;

            let debounceTimer = null;
            const confirmedEmotions = new Set();

            textarea.addEventListener('input', function () {
                clearTimeout(debounceTimer);
                const text = this.value.trim();

                if (text.length > 8) {
                    debounceTimer = setTimeout(() => predictEmotions(text, productId, predictUrl, emotionContainer, emotionPills, confirmedEmotions), 600);
                } else {
                    if (confirmedEmotions.size === 0) {
                        emotionContainer.classList.add('hidden');
                    }
                }
            });

            async function predictEmotions(text, pId, url, container, pills, confirmedSet) {
                const csrfToken = document.querySelector('input[name="csrf_token"]');
                const headers = { 'Content-Type': 'application/json' };
                if (csrfToken) headers['X-CSRFToken'] = csrfToken.value;

                try {
                    const response = await fetch(url, {
                        method: 'POST',
                        credentials: 'same-origin',
                        headers: headers,
                        body: JSON.stringify({ text: text })
                    });

                    if (!response.ok) {
                        console.warn('Emotion API returned', response.status);
                        return;
                    }

                    const data = await response.json();
                    const emotions = data.emotions;

                    if (Array.isArray(emotions) && emotions.length > 0) {
                        renderEmotions(emotions, pills, confirmedSet, pId);
                        container.classList.remove('hidden');
                    } else if (confirmedSet.size === 0) {
                        container.classList.add('hidden');
                    }
                } catch (err) {
                    console.error('Emotion prediction fetch failed:', err);
                }
            }

            function renderEmotions(emotions, pills, confirmedSet, pId) {
                pills.innerHTML = '';

                const normalised = emotions.map(e =>
                    (typeof e === 'object' && e.label) ? e : { label: String(e), score: null }
                );

                const allLabels = new Set([
                    ...normalised.map(e => e.label),
                    ...Array.from(confirmedSet)
                ]);

                allLabels.forEach(label => {
                    const isConfirmed = confirmedSet.has(label);
                    const obj = normalised.find(e => e.label === label);
                    const pct = (obj && obj.score !== null) ? Math.round(obj.score * 100) : null;

                    const btn = document.createElement('button');
                    btn.type = 'button';
                    btn.dataset.emotion = label;
                    btn.dataset.confirmed = isConfirmed ? 'true' : 'false';

                    if (isConfirmed) {
                        btn.className = 'inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-bold bg-teal-600 text-white shadow-md ring-2 ring-teal-600 ring-offset-2 transition-all duration-200';
                        btn.innerHTML = `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg>${label}${pct !== null ? `<span class="text-teal-200 font-normal text-xs">${pct}%</span>` : ''}`;
                    } else {
                        btn.className = 'inline-flex items-center gap-1 px-4 py-1.5 rounded-full text-sm font-semibold bg-white text-gray-700 border border-gray-200 hover:border-teal-500 hover:text-teal-600 hover:bg-teal-50 transition-all duration-200 shadow-sm';
                        btn.innerHTML = `${label}${pct !== null ? `<span class="text-gray-400 font-normal text-xs">${pct}%</span>` : ''}`;
                    }

                    btn.style.cursor = 'pointer';
                    btn.onclick = () => {
                        toggleEmotion(label, emotions, pills, confirmedSet, pId);
                    };
                    pills.appendChild(btn);
                });
            }

            function toggleEmotion(label, lastEmotions, pills, confirmedSet, pId) {
                if (confirmedSet.has(label)) {
                    confirmedSet.delete(label);
                } else {
                    confirmedSet.add(label);
                    if (window.showToast) {
                        window.showToast('✓ Emotion confirmed — helps train the AI!', 'success');
                    }
                }

                const cInput = document.getElementById(`confirmed_emotions-${pId}`);
                if (cInput) {
                    cInput.value = JSON.stringify(Array.from(confirmedSet));
                }

                renderEmotions(lastEmotions, pills, confirmedSet, pId);
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initEmotionDetectors);
    } else {
        initEmotionDetectors();
    }
})();
