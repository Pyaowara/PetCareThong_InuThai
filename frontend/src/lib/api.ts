import { browser } from '$app/environment';

// API configuration and utilities
export const API_CONFIG = {
    BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
    TIMEOUT: 10000,
};

// CSRF token management
let csrfToken: string | null = null;

export const getCsrfToken = async (): Promise<string | null> => {
    if (!browser) return null;
    
    // Try to get CSRF token from cookies first
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            csrfToken = decodeURIComponent(value);
            return csrfToken;
        }
    }
    
    // If no token in cookies, make a simple GET request to any API endpoint to get cookies set
    try {
        const response = await fetch(`${API_CONFIG.BASE_URL}/auth/profile/`, {
            method: 'GET',
            credentials: 'include',
        });
        
        // Check cookies again after the request
        const newCookies = document.cookie.split(';');
        for (let cookie of newCookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                csrfToken = decodeURIComponent(value);
                return csrfToken;
            }
        }
    } catch (error) {
        console.error('Failed to fetch CSRF token:', error);
    }
    
    return null;
};

// Common API headers
export const getApiHeaders = async (includeAuth = true) => {
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
    };
    
    // Skip CSRF for now since we disabled it for debugging
    // TODO: Re-enable CSRF token handling after debugging
    
    return headers;
};

// API fetch wrapper with proper error handling
export const apiRequest = async (
    endpoint: string, 
    options: RequestInit = {}
): Promise<Response> => {
    const url = `${API_CONFIG.BASE_URL}${endpoint}`;
    
    // Get headers asynchronously
    const defaultHeaders = await getApiHeaders();
    
    const config: RequestInit = {
        credentials: 'include', // Important for session-based auth
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers,
        },
    };

    try {
        const response = await fetch(url, config);
        return response;
    } catch (error) {
        console.error(`API request failed for ${url}:`, error);
        throw error;
    }
};

// Helper for JSON API requests
export const apiJson = async (endpoint: string, options: RequestInit = {}) => {
    const response = await apiRequest(endpoint, options);
    
    if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorData}`);
    }
    
    return response.json();
};

// Helper for FormData API requests (file uploads)
export const apiFormData = async (endpoint: string, formData: FormData, options: RequestInit = {}) => {
    const url = `${API_CONFIG.BASE_URL}${endpoint}`;
    
    // Skip CSRF for now since we disabled it for debugging
    const headers: Record<string, string> = {
        ...options.headers as Record<string, string>,
    };
    
    // Don't add Content-Type for FormData, let browser set it with boundary
    const config: RequestInit = {
        method: 'POST',
        credentials: 'include',
        body: formData,
        ...options,
        headers,
    };
    
    try {
        const response = await fetch(url, config);
        
        if (!response.ok) {
            const errorData = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorData}`);
        }
        
        return response.json();
    } catch (error) {
        console.error(`API FormData request failed for ${url}:`, error);
        throw error;
    }
};

export default {
    API_CONFIG,
    apiRequest,
    apiJson,
    apiFormData,
};