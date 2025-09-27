<script lang="ts">
    import { authService, isAuthenticated, user } from '$lib/auth';
    import { goto } from '$app/navigation';
    import { onMount } from 'svelte';

    let email = '';
    let password = '';
    let isLoading = false;
    let error = '';

    onMount(() => {
        // Clear any existing auth state when visiting login (no API call)
        user.set(null);
        isAuthenticated.set(false);
        
        if (typeof sessionStorage !== 'undefined') {
            sessionStorage.removeItem('user');
        }
    });

    async function handleLogin() {
        if (!email || !password) {
            error = 'Please fill in all fields';
            return;
        }

        isLoading = true;
        error = '';

        const result = await authService.login(email, password);

        if (result.success) {
            goto('/');
        } else {
            error = result.error || 'Login failed';
        }

        isLoading = false;
    }

    function goToRegister() {
        goto('/register');
    }
</script>

<svelte:head>
    <title>Login - PetCare</title>
</svelte:head>

<div class="login-container">
    <div class="login-card">
        <div class="login-header">
            <div class="logo">🐾</div>
            <h1>Welcome to PetCare</h1>
            <p>Sign in to your account</p>
        </div>

        <form on:submit|preventDefault={handleLogin} class="login-form">
            {#if error}
                <div class="error-message">
                    {error}
                </div>
            {/if}

            <div class="form-group">
                <label for="email">Email</label>
                <input
                    type="email"
                    id="email"
                    bind:value={email}
                    placeholder="Enter your email"
                    required
                    disabled={isLoading}
                />
            </div>

            <div class="form-group">
                <label for="password">Password</label>
                <input
                    type="password"
                    id="password"
                    bind:value={password}
                    placeholder="Enter your password"
                    required
                    disabled={isLoading}
                />
            </div>

            <button type="submit" class="login-btn" disabled={isLoading}>
                {#if isLoading}
                    <div class="spinner"></div>
                    Signing in...
                {:else}
                    Sign In
                {/if}
            </button>
        </form>

        <div class="login-footer">
            <p>Don't have an account? 
                <button type="button" class="link-btn" on:click={goToRegister}>
                    Register here
                </button>
            </p>
        </div>
    </div>
</div>

<style>
    .login-container {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #f8f6f0 0%, #fff8e1 100%);
        padding: 2rem 1rem;
    }

    .login-card {
        background: white;
        border-radius: 12px;
        padding: 2.5rem;
        box-shadow: 0 20px 40px rgba(184, 134, 11, 0.1);
        border: 1px solid #f3e8a6;
        width: 100%;
        max-width: 400px;
    }

    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }

    .logo {
        font-size: 3rem;
        margin-bottom: 1rem;
    }

    .login-header h1 {
        margin: 0 0 0.5rem 0;
        font-size: 1.75rem;
        font-weight: 700;
        color: #b8860b;
    }

    .login-header p {
        margin: 0;
        color: #666;
        font-size: 0.95rem;
    }

    .login-form {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }

    .form-group {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    label {
        font-weight: 600;
        color: #333;
        font-size: 0.9rem;
    }

    input {
        padding: 0.75rem;
        border: 2px solid #f3e8a6;
        border-radius: 8px;
        font-size: 0.95rem;
        transition: border-color 0.2s ease;
    }

    input:focus {
        outline: none;
        border-color: #daa520;
        box-shadow: 0 0 0 3px rgba(218, 165, 32, 0.1);
    }

    input:disabled {
        background: #faf8f3;
        cursor: not-allowed;
    }

    .login-btn {
        background: linear-gradient(135deg, #daa520 0%, #b8860b 100%);
        color: white;
        border: none;
        padding: 0.875rem;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }

    .login-btn:hover:not(:disabled) {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(218, 165, 32, 0.4);
    }

    .login-btn:disabled {
        opacity: 0.7;
        cursor: not-allowed;
        transform: none;
    }

    .spinner {
        width: 16px;
        height: 16px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        border-top-color: white;
        animation: spin 1s ease-in-out infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    .error-message {
        background: #fee;
        color: #c33;
        padding: 0.75rem;
        border-radius: 6px;
        border: 1px solid #fcc;
        font-size: 0.9rem;
        text-align: center;
    }

    .login-footer {
        text-align: center;
        margin-top: 2rem;
        padding-top: 1.5rem;
        border-top: 1px solid #f3e8a6;
    }

    .login-footer p {
        margin: 0;
        color: #666;
        font-size: 0.9rem;
    }

    .link-btn {
        background: none;
        border: none;
        color: #daa520;
        text-decoration: underline;
        cursor: pointer;
        font-size: inherit;
        padding: 0;
    }

    .link-btn:hover {
        color: #b8860b;
    }
</style>