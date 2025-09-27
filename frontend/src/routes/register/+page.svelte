<script lang="ts">
    import { authService, isAuthenticated, user } from '$lib/auth';
    import { goto } from '$app/navigation';
    import { onMount } from 'svelte';

    let email = '';
    let fullName = '';
    let phoneNumber = '';
    let password = '';
    let confirmPassword = '';
    let isLoading = false;
    let error = '';
    let success = '';

    onMount(() => {
        // Clear any existing auth state when visiting register (no API call)
        user.set(null);
        isAuthenticated.set(false);
        
        if (typeof sessionStorage !== 'undefined') {
            sessionStorage.removeItem('user');
        }
    });

    async function handleRegister() {
        // Validation
        if (!email || !fullName || !password || !confirmPassword) {
            error = 'Please fill in all required fields';
            return;
        }

        if (password !== confirmPassword) {
            error = 'Passwords do not match';
            return;
        }

        if (password.length < 8) {
            error = 'Password must be at least 8 characters long';
            return;
        }

        isLoading = true;
        error = '';
        success = '';

        const result = await authService.register({
            email,
            full_name: fullName,
            password,
            phone_number: phoneNumber || undefined,
        });

        if (result.success) {
            success = 'Registration successful! Please sign in.';
            // Clear form
            email = fullName = phoneNumber = password = confirmPassword = '';
            // Redirect to login after a brief delay
            setTimeout(() => goto('/login'), 2000);
        } else {
            error = result.error || 'Registration failed';
        }

        isLoading = false;
    }

    function goToLogin() {
        goto('/login');
    }
</script>

<svelte:head>
    <title>Register - PetCare</title>
</svelte:head>

<div class="register-container">
    <div class="register-card">
        <div class="register-header">
            <div class="logo">🐾</div>
            <h1>Join PetCare</h1>
            <p>Create your account to get started</p>
        </div>

        <form on:submit|preventDefault={handleRegister} class="register-form">
            {#if error}
                <div class="error-message">
                    {error}
                </div>
            {/if}

            {#if success}
                <div class="success-message">
                    {success}
                </div>
            {/if}

            <div class="form-group">
                <label for="fullName">Full Name</label>
                <input
                    type="text"
                    id="fullName"
                    bind:value={fullName}
                    placeholder="Enter your full name"
                    required
                    disabled={isLoading}
                />
            </div>

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
                <label for="phoneNumber">Phone Number (optional)</label>
                <input
                    type="tel"
                    id="phoneNumber"
                    bind:value={phoneNumber}
                    placeholder="Enter your phone number"
                    disabled={isLoading}
                />
            </div>



            <div class="form-row">
                <div class="form-group">
                    <label for="password">Password</label>
                    <input
                        type="password"
                        id="password"
                        bind:value={password}
                        placeholder="Create a password"
                        required
                        disabled={isLoading}
                    />
                </div>

                <div class="form-group">
                    <label for="confirmPassword">Confirm Password</label>
                    <input
                        type="password"
                        id="confirmPassword"
                        bind:value={confirmPassword}
                        placeholder="Confirm your password"
                        required
                        disabled={isLoading}
                    />
                </div>
            </div>

            <button type="submit" class="register-btn" disabled={isLoading}>
                {#if isLoading}
                    <div class="spinner"></div>
                    Creating Account...
                {:else}
                    Create Account
                {/if}
            </button>
        </form>

        <div class="register-footer">
            <p>Already have an account? 
                <button type="button" class="link-btn" on:click={goToLogin}>
                    Sign in here
                </button>
            </p>
        </div>
    </div>
</div>

<style>
    .register-container {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #f8f6f0 0%, #fff8e1 100%);
        padding: 2rem 1rem;
    }

    .register-card {
        background: white;
        border-radius: 12px;
        padding: 2.5rem;
        box-shadow: 0 20px 40px rgba(184, 134, 11, 0.1);
        border: 1px solid #f3e8a6;
        width: 100%;
        max-width: 500px;
    }

    .register-header {
        text-align: center;
        margin-bottom: 2rem;
    }

    .logo {
        font-size: 3rem;
        margin-bottom: 1rem;
    }

    .register-header h1 {
        margin: 0 0 0.5rem 0;
        font-size: 1.75rem;
        font-weight: 700;
        color: #b8860b;
    }

    .register-header p {
        margin: 0;
        color: #666;
        font-size: 0.95rem;
    }

    .register-form {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }

    .form-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
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

    .register-btn {
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
        margin-top: 1rem;
    }

    .register-btn:hover:not(:disabled) {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(218, 165, 32, 0.4);
    }

    .register-btn:disabled {
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

    .success-message {
        background: #efe;
        color: #363;
        padding: 0.75rem;
        border-radius: 6px;
        border: 1px solid #cfc;
        font-size: 0.9rem;
        text-align: center;
    }

    .register-footer {
        text-align: center;
        margin-top: 2rem;
        padding-top: 1.5rem;
        border-top: 1px solid #f3e8a6;
    }

    .register-footer p {
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

    @media (max-width: 600px) {
        .form-row {
            grid-template-columns: 1fr;
        }
        
        .register-card {
            padding: 2rem 1.5rem;
        }
    }
</style>