<script lang="ts">
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { isAuthenticated, user, authService } from '$lib/auth';
    import { petApi, vaccinationApi } from '$lib/apiServices';

    interface DashboardStats {
        totalPets: number;
        totalVaccinations: number;
        recentVaccinations: {
            id: number;
            pet_name: string;
            vaccine_name: string;
            date: string;
        }[];
        upcomingReminders?: any[]; // For future implementation
    }

    let stats: DashboardStats = {
        totalPets: 0,
        totalVaccinations: 0,
        recentVaccinations: []
    };
    let isLoading = true;
    let error = '';

    onMount(async () => {
        if (!$isAuthenticated) {
            goto('/login');
            return;
        }
        
        await loadDashboardData();
    });

    async function loadDashboardData() {
        try {
            isLoading = true;
            
            // Load pets and vaccinations
            const [pets, vaccinations] = await Promise.all([
                petApi.getPets(),
                vaccinationApi.getVaccinations()
            ]);

            // Filter data based on user role
            let userPets = pets;
            let userVaccinations = vaccinations;
            
            if ($user?.role === 'client') {
                userPets = pets.filter(pet => pet.user_id === $user?.id);
                userVaccinations = vaccinations.filter(vaccination => {
                    const pet = pets.find(p => p.id === vaccination.pet);
                    return pet?.user_id === $user?.id;
                });
            }

            // Sort vaccinations by date (most recent first)
            userVaccinations.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

            stats = {
                totalPets: userPets.length,
                totalVaccinations: userVaccinations.length,
                recentVaccinations: userVaccinations.slice(0, 5) // Show last 5
            };
            
            error = '';
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to load dashboard data';
        } finally {
            isLoading = false;
        }
    }

    function formatDate(dateString: string): string {
        return new Date(dateString).toLocaleDateString();
    }

    function getWelcomeMessage(): string {
        if (!$user) return 'Welcome to PetCare';
        
        const hour = new Date().getHours();
        let greeting = 'Good morning';
        if (hour >= 12 && hour < 17) greeting = 'Good afternoon';
        else if (hour >= 17) greeting = 'Good evening';
        
        const name = $user.first_name || $user.full_name.split(' ')[0] || $user.full_name;
        return `${greeting}, ${name}!`;
    }
</script>

<svelte:head>
    <title>Dashboard - PetCare</title>
</svelte:head>

<div class="dashboard-container">
    {#if error}
        <div class="error-message">{error}</div>
    {/if}

    {#if isLoading}
        <div class="loading">Loading dashboard...</div>
    {:else}
        <!-- Welcome Section -->
        <div class="welcome-section">
            <h1>{getWelcomeMessage()}</h1>
            <p class="welcome-subtitle">
                {#if $user?.role === 'client'}
                    Manage your pets and track their health records
                {:else if $user?.role === 'staff'}
                    Staff dashboard - Manage pets, users, and vaccination records
                {:else if $user?.role === 'vet'}
                    Veterinarian dashboard - Access all pet health information
                {/if}
            </p>
        </div>

        <!-- Stats Cards -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">🐾</div>
                <div class="stat-content">
                    <h3>{stats.totalPets}</h3>
                    <p>{$user?.role === 'client' ? 'My Pets' : 'Total Pets'}</p>
                </div>
                <a href="/pets" class="stat-link">View All</a>
            </div>

            <div class="stat-card">
                <div class="stat-icon">💉</div>
                <div class="stat-content">
                    <h3>{stats.totalVaccinations}</h3>
                    <p>Vaccination Records</p>
                </div>
                <a href="/vaccinations" class="stat-link">View All</a>
            </div>

            {#if $user?.role === 'staff' || $user?.role === 'vet'}
                <div class="stat-card">
                    <div class="stat-icon">🏥</div>
                    <div class="stat-content">
                        <h3>Active</h3>
                        <p>System Status</p>
                    </div>
                    <a href="/vaccines" class="stat-link">Manage</a>
                </div>
            {/if}

            {#if $user?.role === 'staff'}
                <div class="stat-card">
                    <div class="stat-icon">👥</div>
                    <div class="stat-content">
                        <h3>Users</h3>
                        <p>User Management</p>
                    </div>
                    <a href="/users" class="stat-link">Manage</a>
                </div>
            {/if}
        </div>

        <!-- Quick Actions -->
        <div class="quick-actions">
            <h2>Quick Actions</h2>
            <div class="actions-grid">
                <a href="/pets" class="action-card">
                    <div class="action-icon">🐕</div>
                    <h4>Manage Pets</h4>
                    <p>{$user?.role === 'client' ? 'Add or update pet information' : 'View and manage all pets'}</p>
                </a>

                {#if $user?.role === 'staff' || $user?.role === 'vet'}
                    <a href="/vaccinations" class="action-card">
                        <div class="action-icon">�</div>
                        <h4>Record Vaccination</h4>
                        <p>Add new vaccination records</p>
                    </a>

                    <a href="/vaccines" class="action-card">
                        <div class="action-icon">�</div>
                        <h4>Manage Vaccines</h4>
                        <p>Add or update vaccine information</p>
                    </a>
                {:else}
                    <a href="/vaccinations" class="action-card">
                        <div class="action-icon">�</div>
                        <h4>View Vaccinations</h4>
                        <p>Check your pets' vaccination history</p>
                    </a>

                    <a href="/users" class="action-card">
                        <div class="action-icon">�</div>
                        <h4>My Profile</h4>
                        <p>Update your account information</p>
                    </a>
                {/if}
            </div>
        </div>

        <!-- Recent Activity -->
        {#if stats.recentVaccinations.length > 0}
            <div class="recent-activity">
                <h2>Recent Vaccinations</h2>
                <div class="activity-list">
                    {#each stats.recentVaccinations as vaccination (vaccination.id)}
                        <div class="activity-item">
                            <div class="activity-icon">�</div>
                            <div class="activity-content">
                                <p><strong>{vaccination.pet_name}</strong> received <strong>{vaccination.vaccine_name}</strong></p>
                                <span class="activity-date">{formatDate(vaccination.date)}</span>
                            </div>
                        </div>
                    {/each}
                </div>
                <div class="activity-footer">
                    <a href="/vaccinations" class="view-all-link">View All Vaccinations →</a>
                </div>
            </div>
        {/if}
    {/if}
</div>

<style>
    .dashboard-container {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }

    .welcome-section {
        text-align: center;
        margin-bottom: 3rem;
    }

    .welcome-section h1 {
        margin: 0 0 0.5rem 0;
        color: #b8860b;
        font-size: 2.5rem;
        font-weight: 700;
    }

    .welcome-subtitle {
        margin: 0;
        color: #666;
        font-size: 1.1rem;
        opacity: 0.8;
    }

    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin-bottom: 3rem;
    }

    .stat-card {
        background: white;
        border-radius: 12px;
        border: 1px solid #f3e8a6;
        padding: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        box-shadow: 0 2px 4px rgba(184, 134, 11, 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        position: relative;
        overflow: hidden;
    }

    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(184, 134, 11, 0.2);
    }

    .stat-icon {
        font-size: 2rem;
        background: #fff8e1;
        padding: 0.75rem;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 60px;
        height: 60px;
    }

    .stat-content {
        flex: 1;
    }

    .stat-content h3 {
        margin: 0 0 0.25rem 0;
        color: #b8860b;
        font-size: 1.75rem;
        font-weight: 700;
    }

    .stat-content p {
        margin: 0;
        color: #666;
        font-size: 0.9rem;
    }

    .stat-link {
        color: #daa520;
        text-decoration: none;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 0.5rem 0.75rem;
        border: 1px solid #f3e8a6;
        border-radius: 6px;
        transition: all 0.2s ease;
    }

    .stat-link:hover {
        background: #f3e8a6;
        color: #b8860b;
    }

    .quick-actions {
        margin-bottom: 3rem;
    }

    .quick-actions h2 {
        margin: 0 0 1.5rem 0;
        color: #b8860b;
        font-size: 1.75rem;
    }

    .actions-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1.5rem;
    }

    .action-card {
        background: white;
        border-radius: 12px;
        border: 1px solid #f3e8a6;
        padding: 2rem;
        text-decoration: none;
        color: inherit;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        box-shadow: 0 2px 4px rgba(184, 134, 11, 0.1);
        display: block;
    }

    .action-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(184, 134, 11, 0.2);
        color: inherit;
    }

    .action-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }

    .action-card h4 {
        margin: 0 0 0.75rem 0;
        color: #b8860b;
        font-size: 1.25rem;
        font-weight: 600;
    }

    .action-card p {
        margin: 0;
        color: #666;
        line-height: 1.4;
    }

    .recent-activity {
        background: white;
        border-radius: 12px;
        border: 1px solid #f3e8a6;
        padding: 2rem;
        box-shadow: 0 2px 4px rgba(184, 134, 11, 0.1);
    }

    .recent-activity h2 {
        margin: 0 0 1.5rem 0;
        color: #b8860b;
        font-size: 1.5rem;
    }

    .activity-list {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .activity-item {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        background: #fff8e1;
        border-radius: 8px;
    }

    .activity-icon {
        font-size: 1.25rem;
        background: white;
        padding: 0.5rem;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 40px;
        height: 40px;
        border: 1px solid #f3e8a6;
    }

    .activity-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }

    .activity-content p {
        margin: 0;
        color: #333;
        font-size: 0.95rem;
    }

    .activity-date {
        color: #666;
        font-size: 0.85rem;
    }

    .activity-footer {
        margin-top: 1.5rem;
        text-align: center;
    }

    .view-all-link {
        color: #daa520;
        text-decoration: none;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        border: 1px solid #f3e8a6;
        border-radius: 8px;
        display: inline-block;
        transition: all 0.2s ease;
    }

    .view-all-link:hover {
        background: #f3e8a6;
        color: #b8860b;
    }

    .error-message {
        background: #fee;
        color: #c33;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        border: 1px solid #fcc;
    }

    .loading {
        text-align: center;
        padding: 3rem;
        color: #666;
        font-size: 1.1rem;
    }

    @media (max-width: 768px) {
        .dashboard-container {
            padding: 1rem;
        }

        .welcome-section h1 {
            font-size: 2rem;
        }

        .stats-grid {
            grid-template-columns: 1fr;
        }

        .actions-grid {
            grid-template-columns: 1fr;
        }

        .stat-card, .action-card {
            padding: 1.25rem;
        }

        .activity-item {
            flex-direction: column;
            text-align: center;
        }
    }
</style>
