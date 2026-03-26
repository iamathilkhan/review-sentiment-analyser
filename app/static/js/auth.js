/**
 * Authentication Service for ReviewAI
 * Handles AJAX calls to the auth blueprint
 */

const authService = {
    async _fetch(url, options = {}) {
        const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        };

        const finalOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, finalOptions);
            const data = await response.json();

            if (!response.ok) {
                // Handle Rate Limiting
                if (response.status === 429) {
                    this._showToast('Too many requests — please wait before trying again', 'error');
                    throw new Error('Rate limit exceeded');
                }

                // Handle Token Expiry
                if (response.status === 401 && !url.includes('/login')) {
                    this._showToast('Your session has expired. Please sign in again.', 'info');
                    setTimeout(() => {
                        window.location.href = '/auth/login?expired=1';
                    }, 1500);
                    throw new Error('Unauthorized');
                }

                throw data;
            }

            return data;
        } catch (error) {
            console.error('Auth Request Error:', error);
            throw error;
        }
    },

    async login(credentials) {
        return this._fetch('/auth/login', {
            method: 'POST',
            body: JSON.stringify(credentials)
        }).then(data => {
            // Role-based redirection logic
            const role = data.user.role;
            let redirect = '/';
            if (role === 'admin') redirect = '/admin';
            else if (role === 'seller') redirect = '/seller';
            
            return { ...data, redirect };
        });
    },

    async register(userData) {
        return this._fetch('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    },

    async logout() {
        return this._fetch('/auth/logout', {
            method: 'POST'
        }).then(() => {
            window.location.href = '/auth/login';
        });
    },

    _showToast(message, type = 'info') {
        // Simple toast implementation using Alpine.js or native alert
        // In a real app, this would trigger a nice UI component
        const toast = document.createElement('div');
        toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-2xl text-white font-medium z-50 transition-all duration-500 transform translate-y-20
            ${type === 'error' ? 'bg-red-600' : 'bg-teal-600'}`;
        toast.innerText = message;
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => toast.classList.remove('translate-y-20'), 100);
        
        // Animate out
        setTimeout(() => {
            toast.classList.add('opacity-0', 'translate-y-2');
            setTimeout(() => toast.remove(), 500);
        }, 3000);
    }
};
