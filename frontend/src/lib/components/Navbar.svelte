<script lang="ts">
    import { user, isAuthenticated, authService } from '$lib/auth';
    import { goto } from '$app/navigation';

    async function handleLogout() {
        await authService.logout();
        goto('/login');
    }

    function getInitials(name: string): string {
        return name
            .split(' ')
            .map(word => word.charAt(0).toUpperCase())
            .join('')
            .substring(0, 2);
    }
</script>

{#if $isAuthenticated && $user}
<nav class="navbar">
    <div class="nav-container">
        <div class="nav-brand">
            <a href="/" class="brand-link">🐾 PetCare</a>
        </div>
        
        <div class="nav-links">
            <a href="/appointments" class="nav-link">Appointment</a>
            <a href="/pets" class="nav-link">Pets</a>
            
            {#if $user?.role === 'staff' || $user?.role === 'vet'}
                <a href="/vaccines" class="nav-link">Vaccines</a>
            {/if}
            
            <a href="/vaccinations" class="nav-link">Vaccinations</a>
            
            {#if $user?.role === 'staff'}
                <a href="/services" class="nav-link">Services</a>
                <a href="/users" class="nav-link">Users</a>
            {:else}
                <a href="/users" class="nav-link">Profile</a>
            {/if}
        </div>
        
        <div class="nav-user">
            <div class="user-info">
                <div class="user-avatar">
                    {#if $user.image_url}
                        <img src={$user.image_url} alt="Profile" class="avatar-image" />
                    {:else}
                        <div class="avatar-initials">
                            {getInitials($user.full_name)}
                        </div>
                    {/if}
                </div>
                <div class="user-details">
                    <span class="user-name">{$user.full_name}</span>
                    <span class="user-role">{$user.role}</span>
                </div>
            </div>
            
            <button class="logout-btn" on:click={handleLogout}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                    <polyline points="16,17 21,12 16,7"/>
                    <line x1="21" y1="12" x2="9" y2="12"/>
                </svg>
                Logout
            </button>
        </div>
    </div>
</nav>
{/if}

<style>
    .navbar {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        color: #333;
        padding: 1rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        position: sticky;
        top: 0;
        z-index: 100;
        border-bottom: 1px solid rgba(218, 165, 32, 0.2);
    }

    .nav-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .brand-link {
        background: linear-gradient(135deg, #daa520 0%, #b8860b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-decoration: none;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
        transition: all 0.3s ease;
    }

    .brand-link:hover {
        opacity: 0.8;
        transform: scale(1.05);
    }

    .nav-links {
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }

    .nav-link {
        color: #555;
        text-decoration: none;
        font-weight: 500;
        padding: 0.6rem 1.2rem;
        border-radius: 8px;
        transition: all 0.2s ease;
        font-size: 0.95rem;
        position: relative;
    }

    .nav-link:hover {
        background: linear-gradient(135deg, #daa520 0%, #b8860b 100%);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(218, 165, 32, 0.3);
    }

    .nav-user {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .user-info {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .user-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        overflow: hidden;
        border: 2px solid #daa520;
        box-shadow: 0 2px 8px rgba(218, 165, 32, 0.3);
    }

    .avatar-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .avatar-initials {
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, #daa520 0%, #b8860b 100%);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.9rem;
    }

    .user-details {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
    }

    .user-name {
        font-weight: 600;
        font-size: 0.9rem;
        color: #333;
    }

    .user-role {
        font-size: 0.75rem;
        color: #888;
        text-transform: capitalize;
    }

    .logout-btn {
        background: white;
        color: #b8860b;
        border: 2px solid #daa520;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.85rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .logout-btn:hover {
        background: linear-gradient(135deg, #daa520 0%, #b8860b 100%);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(218, 165, 32, 0.3);
    }

    @media (max-width: 768px) {
        .nav-container {
            padding: 0 1rem;
        }
        
        .nav-links {
            gap: 1rem;
        }
        
        .nav-link {
            padding: 0.4rem 0.6rem;
            font-size: 0.85rem;
        }
        
        .user-details {
            display: none;
        }
        
        .logout-btn {
            padding: 0.5rem;
        }
    }
</style>