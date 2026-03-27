/**
 * review_submit.js
 * Handles synchronous review submission and dynamic UI updates.
 */

document.addEventListener('DOMContentLoaded', () => {
    const reviewForms = document.querySelectorAll('.review-form');

    reviewForms.forEach(form => {
        const productId = form.dataset.productId;
        const textarea = document.getElementById(`review-content-${productId}`);
        const submitBtn = form.querySelector('#submit-review-btn');
        const currentCharCount = document.getElementById(`current-count-${productId}`);
        const container = document.getElementById(`review-container-${productId}`);
        const loadingOverlay = container.querySelector('#review-loading');
        const resultContainer = container.querySelector('#review-result');

        if (!textarea || !submitBtn || !currentCharCount) return;

        // Character counter and button state
        textarea.addEventListener('input', () => {
            const length = textarea.value.length;
            currentCharCount.textContent = length;

            if (length >= 20 && length <= 2000) {
                submitBtn.disabled = false;
                textarea.classList.remove('border-red-400');
            } else {
                submitBtn.disabled = true;
            }
        });

        // Form submission
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const content = textarea.value;
            submitBtn.disabled = true;

            // Show loading overlay
            loadingOverlay.classList.remove('hidden');

            try {
                const confirmedEmotionsInput = document.getElementById(`confirmed_emotions-${productId}`);
                const confirmedEmotions = confirmedEmotionsInput
                    ? JSON.parse(confirmedEmotionsInput.value || '[]')
                    : [];

                const response = await fetch('/reviews/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': form.querySelector('[name=csrf_token]').value
                    },
                    body: JSON.stringify({
                        product_id: productId,
                        content: content,
                        confirmed_emotions: confirmedEmotions
                    })
                });

                loadingOverlay.classList.add('hidden');

                if (response.status === 201 || response.status === 202) {
                    const data = await response.json();
                    showSuccessCard(data, confirmedEmotions);
                    showToast('✅ Review submitted and analysed!', 'success');
                } else if (response.status === 429) {
                    showToast("You've submitted too many reviews. Try again later.", 'warning');
                    submitBtn.disabled = false;
                } else {
                    const error = await response.json().catch(() => ({}));
                    showToast(error.error || 'Failed to submit review', 'error');
                    submitBtn.disabled = false;
                }
            } catch (err) {
                console.error('Submission error:', err);
                loadingOverlay.classList.add('hidden');
                showToast('Network error. Please check your connection.', 'error');
                submitBtn.disabled = false;
            }
        });

        function showSuccessCard(data, confirmedEmotions) {
            const sentimentColors = { positive: 'teal', negative: 'red', neutral: 'gray' };
            const sentiment = data.overall_sentiment || 'neutral';
            const color = sentimentColors[sentiment] || 'gray';

            const emotionBadges = Array.isArray(confirmedEmotions) && confirmedEmotions.length > 0
                ? confirmedEmotions.map(e => {
                    const label = typeof e === 'object' && e.label ? e.label : String(e);
                    return `<span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-teal-100 text-teal-700">${label}</span>`;
                }).join('')
                : '<span class="text-gray-400 text-sm italic">No emotions confirmed</span>';

            resultContainer.innerHTML = `
                <div class="flex items-start gap-4 p-6 bg-gradient-to-br from-${color}-50 to-white rounded-2xl border-2 border-${color}-100 shadow-sm">
                    <div class="flex-shrink-0 w-12 h-12 rounded-xl bg-${color}-100 flex items-center justify-center">
                        <svg class="w-6 h-6 text-${color}-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    </div>
                    <div class="flex-1">
                        <h4 class="font-bold text-gray-900 text-lg mb-1">Review Analysed Successfully!</h4>
                        <p class="text-sm text-gray-500 mb-4">Your review has been saved and our AI has analysed its sentiment.</p>
                        <div class="flex flex-wrap gap-3 mb-4">
                            <span class="inline-flex items-center px-4 py-1.5 rounded-full text-sm font-bold bg-${color}-600 text-white shadow-sm capitalize">
                                ${sentiment} Sentiment
                            </span>
                        </div>
                        <div class="mt-3">
                            <p class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Your Confirmed Emotions</p>
                            <div class="flex flex-wrap gap-2">${emotionBadges}</div>
                        </div>
                        <p class="text-xs text-gray-400 mt-4">Thank you! Your confirmed emotions help train our AI model. Refreshing in 3 seconds...</p>
                    </div>
                </div>
            `;
            resultContainer.classList.remove('hidden');
            form.classList.add('opacity-50', 'pointer-events-none');

            // Auto-reload to show new review in the list
            setTimeout(() => { window.location.reload(); }, 3000);
        }
    });

    // Global toast notification (non-blocking)
    window.showToast = function (message, type = 'info') {
        const colors = {
            success: 'bg-teal-600',
            error: 'bg-red-500',
            warning: 'bg-amber-500',
            info: 'bg-blue-500'
        };
        const toast = document.createElement('div');
        toast.className = `fixed bottom-6 right-6 z-50 px-6 py-4 rounded-2xl text-white font-semibold shadow-2xl text-sm transition-all duration-300 ${colors[type] || colors.info}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(1rem)';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    };
});
