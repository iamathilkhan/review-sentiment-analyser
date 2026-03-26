/**
 * review_submit.js
 * Handles asynchronous review submission, SSE tracking, and dynamic UI updates.
 */

document.addEventListener('DOMContentLoaded', () => {
    const reviewForms = document.querySelectorAll('.review-form');
    
    reviewForms.forEach(form => {
        const productId = form.dataset.productId;
        const textarea = form.querySelector('textarea');
        const submitBtn = form.querySelector('#submit-review-btn');
        const currentCharCount = form.querySelector('#current-count');
        const container = document.getElementById(`review-container-${productId}`);
        const loadingOverlay = container.querySelector('#review-loading');
        const resultContainer = container.querySelector('#review-result');
        const statusText = container.querySelector('#processing-status-text');

        // Character counter and button state
        textarea.addEventListener('input', () => {
            const length = textarea.value.length;
            currentCharCount.textContent = length;
            
            if (length >= 20 && length <= 2000) {
                submitBtn.disabled = false;
                textarea.classList.remove('is-invalid');
            } else {
                submitBtn.disabled = true;
            }
        });

        // Form submission
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const content = textarea.value;
            submitBtn.disabled = true;
            
            try {
                const confirmedEmotionsInput = form.querySelector('#confirmed_emotions');
                const confirmedEmotions = confirmedEmotionsInput ? JSON.parse(confirmedEmotionsInput.value) : [];

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

                if (response.status === 202) {
                    const data = await response.json();
                    startTracking(data.review_id);
                } else if (response.status === 429) {
                    showToast("You've submitted too many reviews. Try again later.", "warning");
                    submitBtn.disabled = false;
                } else {
                    const error = await response.json();
                    showToast(error.error || "Failed to submit review", "danger");
                    submitBtn.disabled = false;
                }
            } catch (err) {
                console.error("Submission error:", err);
                showToast("Network error. Please check your connection.", "danger");
                submitBtn.disabled = false;
            }
        });

        /**
         * Real-time tracking via SSE
         */
        function startTracking(reviewId) {
            // UI Transition
            form.classList.add('d-none');
            loadingOverlay.classList.remove('d-none');
            
            // Get token from cookie or local state if available
            // For this implementation, we assume the token is in the 'access_token' cookie
            const token = getCookie('access_token');
            const sseUrl = `/sse/review/${reviewId}?token=${token}`;
            
            const eventSource = new EventSource(sseUrl);
            let pollingInterval = null;

            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateUIState(data);
                
                if (data.status === 'done') {
                    eventSource.close();
                    renderFinalResult(reviewId, data);
                } else if (data.status === 'failed' || data.status === 'timeout') {
                    eventSource.close();
                    handleFailure(data.error || "Analysis failed");
                }
            };

            eventSource.onerror = (err) => {
                console.warn("SSE connection failed, falling back to polling...", err);
                eventSource.close();
                startPolling(reviewId);
            };

            // EventSource 'close' event (custom)
            eventSource.addEventListener('close', () => {
                eventSource.close();
            });
        }

        /**
         * Fallback Polling
         */
        function startPolling(reviewId) {
            const poll = async () => {
                try {
                    const response = await fetch(`/reviews/${reviewId}/status`);
                    if (response.ok) {
                        const data = await response.json();
                        updateUIState(data);
                        if (data.status === 'done') {
                            clearInterval(pollingInterval);
                            renderFinalResult(reviewId, data);
                        } else if (data.status === 'failed') {
                            clearInterval(pollingInterval);
                            handleFailure(data.error);
                        }
                    }
                } catch (err) {
                    console.error("Polling error:", err);
                }
            };
            pollingInterval = setInterval(poll, 2000);
            poll();
        }

        function updateUIState(data) {
            if (data.status === 'processing') {
                statusText.textContent = "Processing aspects...";
            } else if (data.status === 'done') {
                statusText.textContent = "Analysis complete!";
            }
        }

        async function renderFinalResult(reviewId, data) {
            loadingOverlay.classList.add('d-none');
            resultContainer.classList.remove('d-none');
            
            // Fetch partial HTML for the result card
            try {
                const response = await fetch(`/reviews/${reviewId}/result-partial`);
                if (response.ok) {
                    const html = await response.text();
                    resultContainer.innerHTML = html;
                } else {
                    // Manual fallback if partial route doesn't exist yet
                    resultContainer.innerHTML = `
                        <div class="alert alert-success">
                            <h4>Review Processed</h4>
                            <p>Overall Sentiment: <strong>${data.overall_sentiment}</strong></p>
                            <ul>
                                ${data.aspects.map(a => `<li>${a.aspect_category}: ${a.polarity} (${Math.round(a.confidence * 100)}%)</li>`).join('')}
                            </ul>
                        </div>
                    `;
                }
            } catch (err) {
                console.error("Error fetching result partial:", err);
            }
        }

        function handleFailure(errorMsg) {
            loadingOverlay.classList.add('d-none');
            form.classList.remove('d-none');
            submitBtn.disabled = false;
            showToast(errorMsg || "Analysis encountered an error.", "danger");
        }
    });

    // Helper functions
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    function showToast(message, type) {
        // Simple toast implementation or alert
        alert(message); 
    }
});
