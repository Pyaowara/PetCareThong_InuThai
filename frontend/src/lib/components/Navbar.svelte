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
            <a href="/appointment" class="nav-link">Appointment</a>
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
        background: linear-gradient(135deg, #daa520 0%, #b8860b 100%);
        color: white;
        padding: 1rem 0;
        box-shadow: 0 2px 10px rgba(184, 134, 11, 0.2);
        position: sticky;
        top: 0;
        z-index: 100;
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
        color: white;
        text-decoration: none;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
    }

    .brand-link:hover {
        color: rgba(255, 255, 255, 0.8);
    }

    .nav-links {
        display: flex;
        gap: 2rem;
        align-items: center;
    }

    .nav-link {
        color: white;
        text-decoration: none;
        font-weight: 500;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        transition: all 0.2s ease;
        font-size: 0.95rem;
    }

    .nav-link:hover {
        background: rgba(255, 255, 255, 0.1);
        color: rgba(255, 255, 255, 0.9);
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
        border: 2px solid rgba(255, 255, 255, 0.3);
    }

    .avatar-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .avatar-initials {
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.2);
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
    }

    .user-role {
        font-size: 0.75rem;
        opacity: 0.8;
        text-transform: capitalize;
    }

    .logout-btn {
        background: rgba(255, 255, 255, 0.1);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 0.5rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.85rem;
        transition: all 0.2s ease;
    }

    .logout-btn:hover {
        background: rgba(255, 255, 255, 0.2);
        border-color: rgba(255, 255, 255, 0.5);
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