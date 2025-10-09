import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import { apiJson, apiFormData } from './api';

// User interface
export interface User {
    id: number;
    email: string;
    full_name: string;
    first_name?: string;
    last_name?: string;
    phone_number?: string;
    role: string;
    active?: boolean;
    created_at?: string;
    image_url?: string;
}

// Auth store
export const isAuthenticated = writable<boolean>(false);
export const user = writable<User | null>(null);

// Initialize auth state from sessionStorage on page load
if (browser) {
    const savedUser = sessionStorage.getItem('user');
    if (savedUser) {
        try {
            const userData = JSON.parse(savedUser);
            user.set(userData);
            isAuthenticated.set(true);
        } catch (e) {
            console.error('Failed to parse saved user data');
            sessionStorage.removeItem('user');
        }
    }
}

// Auth functions
export const authService = {
    async login(email: string, password: string) {
        try {
            console.log('Attempting login for:', email);

            const data = await apiJson('/auth/login/', {
                method: 'POST',
                body: JSON.stringify({ email, password })
            });

            const userData = data.user;
            user.set(userData);
            isAuthenticated.set(true);

            // Save to sessionStorage
            if (browser) {
                sessionStorage.setItem('user', JSON.stringify(userData));
            }

            return { success: true, user: userData };
        } catch (error) {
            console.error('Login error:', error);
            let friendlyError = error;
            if (error instanceof TypeError && error.message === 'Failed to fetch') {
                friendlyError = 'Cannot connect to server. Please try again later.';
            }
            return { success: false, error: friendlyError };
        }
    },

    async register(userData: { email: string; password: string; full_name: string; phone_number?: string; role?: string }) {
        try {
            const formData = new FormData();
            formData.append('email', userData.email);
            formData.append('password', userData.password);
            formData.append('full_name', userData.full_name);
            if (userData.phone_number) {
                formData.append('phone_number', userData.phone_number);
            }
            if (userData.role) {
                formData.append('role', userData.role);
            }

            const data = await apiFormData('/auth/register/', formData);
            return { success: true, user: data.user };
        } catch (error) {
            let friendlyError = error;
            if (error instanceof TypeError && error.message === 'Failed to fetch') {
                friendlyError = 'Cannot connect to server. Please try again later.';
            }
            return { success: false, error: friendlyError };
        }
    },

    async logout() {
        try {
            await apiJson('/auth/logout/', {
                method: 'POST',
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Clear state regardless of API response
            user.set(null);
            isAuthenticated.set(false);

            if (browser) {
                sessionStorage.removeItem('user');
            }
        }
    },

    async getProfile() {
        try {
            console.log('Fetching user profile...');

            const userData = await apiJson('/auth/profile/');

            console.log('Profile response:', userData);

            user.set(userData);
            isAuthenticated.set(true);

            if (browser) {
                sessionStorage.setItem('user', JSON.stringify(userData));
            }

            return userData;
        } catch (error) {
            console.error('Profile fetch error:', error);
            // Clear state without making logout API call if we're not authenticated
            user.set(null);
            isAuthenticated.set(false);

            if (browser) {
                sessionStorage.removeItem('user');
            }

            return null;
        }
    }
};