<script lang="ts">
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { isAuthenticated, user, authService } from '$lib/auth';
    import { petApi, vaccinationApi, appointmentApi } from '$lib/apiServices';
    import backgroundImage from '$lib/assets/main_background.png';

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

    interface Appointment {
        id: number;
        date: string; // This is actually a datetime field in the model
        pet_name: string;
        pet_image_url?: string;
        pet_breed: string;
        pet_gender: string;
        pet_age: number | null;
        owner_name: string;
        owner_email: string;
        status: string;
        purpose: string; // This is the actual field name in the model
        assigned_vet?: string;
    }

    let stats: DashboardStats = {
        totalPets: 0,
        totalVaccinations: 0,
        recentVaccinations: []
    };
    let appointments: Appointment[] = [];
    let isLoading = true;
    let error = '';

    onMount(async () => {
        if (!$isAuthenticated) {
            goto('/login');
            return;
        }

        if ($user?.role !== 'client' && $user?.role !== 'staff' && $user?.role !== 'vet') {
            goto('/unauthorized');
            return;
        }

        await loadDashboardData();
    });

    async function loadDashboardData() {
        try {
            isLoading = true;
            
            // Load pets, vaccinations, and appointments
            const [pets, vaccinations, allAppointments] = await Promise.all([
                petApi.getPets(),
                vaccinationApi.getVaccinations(),
                appointmentApi.getAppointment()
            ]);

            // For clients, the backend already filters data by user
            // No need to filter on frontend since API handles role-based access
            let userPets = pets;
            let userVaccinations = vaccinations;

            // Sort vaccinations by date (most recent first)
            userVaccinations.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

            // Filter appointments based on user role
            const today = new Date().toISOString().split('T')[0];
            
            if ($user?.role === 'staff') {
                // Staff: Display all appointments with status 'booked'
                appointments = allAppointments.filter(apt => apt.status === 'booked');
            } else if ($user?.role === 'vet') {
                // Vet: Display appointments with status 'confirmed' and assigned to them
                appointments = allAppointments.filter(apt => 
                    apt.status === 'confirmed' && 
                    apt.assigned_vet === $user?.full_name
                );
            } else if ($user?.role === 'client') {
                // Client: Display upcoming appointments with status 'booked' or 'confirmed'
                // Order by closest to today and must not be less than today
                appointments = allAppointments
                    .filter(apt => {
                        const appointmentDate = new Date(apt.date).toISOString().split('T')[0];
                        return (apt.status === 'booked' || apt.status === 'confirmed') &&
                               appointmentDate >= today;
                    })
                    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
            }

            stats = {
                totalPets: userPets.length,
                totalVaccinations: userVaccinations.length,
                recentVaccinations: userVaccinations.slice(0, 5) // Show last 5
            };
            
            error = '';
        } catch (err) {
            if (err instanceof Error) {
                error = err.message;
            } else if (typeof err === 'object' && err !== null) {
                if ('non_field_errors' in err && Array.isArray((err as any).non_field_errors)) {
                    error = (err as any).non_field_errors.join(', ');
                } else if ('detail' in err) {
                    error = (err as any).detail;
                } else {
                    error = JSON.stringify(err);
                }
            } else {
                error = typeof err === 'string' ? err : 'Failed to load dashboard data';
            }
        } finally {
            isLoading = false;
        }
    }

    function formatDate(dateString: string): string {
        return new Date(dateString).toLocaleDateString();
    }

    function formatDateTime(dateString: string): string {
        const date = new Date(dateString);
        return `${date.toLocaleDateString()} at ${date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
    }

    function getStatusColor(status: string): string {
        switch (status) {
            case 'booked': return '#ffc107';
            case 'confirmed': return '#28a745';
            case 'completed': return '#6c757d';
            case 'cancelled': return '#dc3545';
            case 'rejected': return '#dc3545';
            default: return '#6c757d';
        }
    }

    function getAppointmentSectionTitle(): string {
        if ($user?.role === 'staff') {
            return 'Pending Appointments (Booked)';
        } else if ($user?.role === 'vet') {
            return 'My Confirmed Appointments';
        } else if ($user?.role === 'client') {
            return 'Upcoming Appointments';
        }
        return 'Appointments';
    }

    function getWelcomeMessage(): string {
        if (!$user) return 'Welcome to PetCare';
        
        const hour = new Date().getHours();
        let greeting = 'Good morning';
        if (hour >= 12 && hour < 17) greeting = 'Good afternoon';
        else if (hour >= 17) greeting = 'Good evening';
        
        const name = $user.full_name.split(' ')[0] || $user.full_name;
        return `${greeting}, ${name}!`;
    }
</script>

<svelte:head>
    <title>PetCare</title>
</svelte:head>

<div class="dashboard-container">
    {#if error}
        <div class="error-message">{error}</div>
    {/if}

    {#if isLoading}
        <div class="loading">Loading dashboard...</div>
    {:else}
        <div class="hero-section" style="background-image: url({backgroundImage});">
            <div class="hero-overlay"></div>
            <div class="hero-content">
                <h1>{getWelcomeMessage()}</h1>
                <p class="hero-subtitle">
                    {#if $user?.role === 'client'}
                        Manage your pets and track their health records
                    {:else if $user?.role === 'staff'}
                        Staff dashboard - Manage pets, users, and vaccination records
                    {:else if $user?.role === 'vet'}
                        Veterinarian dashboard - Access all pet health information
                    {/if}
                </p>
                <a href="/appointments" class="hero-button">
                    📅 View Appointments
                </a>
            </div>
        </div>

        <!-- Main Content -->
        <div class="main-content">
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
            {#if $user?.role === 'client'}
                <div class="stat-card">
                    <div class="stat-icon">💉</div>
                    <div class="stat-content">
                        <h3>{stats.totalVaccinations}</h3>
                        <p>My Vaccination Records</p>
                    </div>
                    <a href="/vaccinations" class="stat-link">View All</a>
                </div>
            {/if}

            <div class="stat-card">
                <div class="stat-icon">🏥</div>
                <div class="stat-content">
                    <h3>Vaccines</h3>
                    <p>{($user?.role === 'staff' || $user?.role === 'vet') ? 'Vaccines Available' : 'Available Vaccines'}</p>
                </div>
                <a href="/vaccines" class="stat-link">{($user?.role === 'staff' || $user?.role === 'vet') ? 'Manage' : 'View'}</a>
            </div>

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

        <!-- Appointments Section -->
        <div class="appointments-section">
            <h2>{getAppointmentSectionTitle()}</h2>
            {#if appointments.length === 0}
                <div class="no-appointments">
                    <div class="no-appointments-icon">�</div>
                    <p>
                        {#if $user?.role === 'staff'}
                            No pending appointments to review
                        {:else if $user?.role === 'vet'}
                            No confirmed appointments assigned to you
                        {:else if $user?.role === 'client'}
                            No upcoming appointments scheduled
                        {/if}
                    </p>
                    <a href="/appointments" class="book-appointment-btn">
                        {$user?.role === 'client' ? 'Book Appointment' : 'View All Appointments'}
                    </a>
                </div>
            {:else}
                <div class="appointments-list">
                    {#each appointments as appointment (appointment.id)}
                        <div class="appointment-card">
                            <div class="appointment-left-section">
                                <div class="appointment-pet-section">
                                    <div class="appointment-pet-image">
                                        {#if appointment.pet_image_url}
                                            <img src={appointment.pet_image_url} alt={appointment.pet_name} class="pet-image" />
                                        {:else}
                                            <div class="pet-image-placeholder">🐾</div>
                                        {/if}
                                    </div>
                                    <div class="pet-info">
                                        <div class="pet-name">{appointment.pet_name}</div>
                                        <div class="pet-breed">{appointment.pet_breed}</div>
                                    </div>
                                </div>
                                <div class="pet-details-section">
                                    <div class="pet-stats">
                                        <div class="pet-stat">
                                            <span class="stat-icon">🎂</span>
                                            <span class="stat-text">{appointment.pet_age || 'N/A'} {appointment.pet_age === 1 ? 'year' : 'years'}</span>
                                        </div>
                                        <div class="pet-stat">
                                            <span class="stat-icon">{appointment.pet_gender === 'Male' ? '♂️' : '♀️'}</span>
                                            <span class="stat-text">{appointment.pet_gender}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="appointment-main-content">
                                <div class="appointment-header">
                                    <div class="appointment-title">
                                        {#if $user?.role === 'client'}
                                            <h4>Appointment Details</h4>
                                        {:else}
                                            <h4><span class="owner-label">Owner:</span> {appointment.owner_name}</h4>
                                        {/if}
                                        <div class="appointment-meta">
                                            <div class="appointment-date">
                                                <span class="date-icon">📅</span>
                                                {formatDateTime(appointment.date)}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="appointment-body">
                                    <div class="purpose-section">
                                        <div class="purpose-label">
                                            <span class="purpose-icon">🎯</span>
                                            <strong>Purpose</strong>
                                        </div>
                                        <p class="purpose-text">{appointment.purpose}</p>
                                    </div>
                                    
                                    {#if $user?.role === 'staff' && appointment.assigned_vet}
                                        <div class="vet-section">
                                            <div class="vet-label">
                                                <span class="vet-icon">👨‍⚕️</span>
                                                <strong>Assigned Vet</strong>
                                            </div>
                                            <p class="vet-text">{appointment.assigned_vet}</p>
                                        </div>
                                    {/if}
                                </div>
                            </div>
                            
                            <div class="appointment-right-section">
                                <div class="appointment-status" style="background-color: {getStatusColor(appointment.status)}">
                                    <span class="status-icon">
                                        {#if appointment.status === 'booked'}
                                            ⏰
                                        {:else if appointment.status === 'confirmed'}
                                            ✅
                                        {:else if appointment.status === 'completed'}
                                            🏁
                                        {:else if appointment.status === 'cancelled' || appointment.status === 'rejected'}
                                            ❌
                                        {:else}
                                            📋
                                        {/if}
                                    </span>
                                    <span class="status-text">{appointment.status.toUpperCase()}</span>
                                </div>
                                <a href="/appointments/{appointment.id}" class="view-appointment-btn">
                                    <span class="btn-icon">👁️</span>
                                    View Details
                                </a>
                            </div>
                        </div>
                    {/each}
                </div>
                <div class="appointments-footer">
                    <a href="/appointments" class="view-all-appointments-link">
                        View All Appointments →
                    </a>
                </div>
            {/if}
        </div>

        <!-- Recent Activity -->
        {#if stats.recentVaccinations.length > 0}
            <div class="recent-activity">
                <h2>Recent Vaccinations</h2>
                <div class="activity-list">
                    {#each stats.recentVaccinations as vaccination (vaccination.id)}
                        <div class="activity-item">
                            <div class="activity-icon">💉</div>
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
    </div>
    {/if}
</div>

<style>
    .dashboard-container {
        min-height: 100vh;
        background-color: #faf8f3;
    }

    .hero-section {
        position: relative;
        height: 500px;
        background-size: cover;
        background-position: center;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 3rem;
        overflow: hidden;
    }

    .hero-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(100, 79, 20, 0.3);
        z-index: 1;
    }

    .hero-content {
        position: relative;
        z-index: 2;
        text-align: center;
        color: white;
        padding: 2rem;
        max-width: 800px;
    }

    .hero-content h1 {
        margin: 0 0 1rem 0;
        font-size: 3.5rem;
        font-weight: 700;
        text-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        line-height: 1.2;
    }

    .hero-subtitle {
        margin: 0 0 2rem 0;
        font-size: 1.3rem;
        font-weight: 400;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        opacity: 0.95;
    }

    .hero-button {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: white;
        color: #b8860b;
        text-decoration: none;
        font-weight: 700;
        font-size: 1.1rem;
        padding: 1rem 2.5rem;
        border-radius: 50px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }

    .hero-button:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.3);
        background: #fff8e1;
    }

    .main-content {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 2rem 2rem 2rem;
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
        box-shadow: 0 2px 8px rgba(184, 134, 11, 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        position: relative;
        overflow: hidden;
    }

    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(184, 134, 11, 0.15);
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

    .appointments-section {
        margin-bottom: 3rem;
        background: white;
        border-radius: 12px;
        border: 1px solid #f3e8a6;
        padding: 2rem;
        box-shadow: 0 2px 8px rgba(184, 134, 11, 0.1);
    }

    .appointments-section h2 {
        margin: 0 0 1.5rem 0;
        color: #b8860b;
        font-size: 1.75rem;
    }

    .no-appointments {
        text-align: center;
        padding: 3rem 1rem;
        color: #666;
    }

    .no-appointments-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }

    .no-appointments p {
        margin: 0 0 2rem 0;
        font-size: 1.1rem;
    }

    .book-appointment-btn {
        display: inline-block;
        background: linear-gradient(135deg, #daa520 0%, #b8860b 100%);
        color: white;
        text-decoration: none;
        font-weight: 600;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .book-appointment-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(184, 134, 11, 0.3);
    }

    .appointments-list {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .appointment-card {
        background: white;
        border-radius: 16px;
        border: 2px solid #f3e8a6;
        padding: 1.5rem;
        display: flex;
        align-items: stretch;
        gap: 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(184, 134, 11, 0.08);
        position: relative;
        overflow: hidden;
    }

    .appointment-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(184, 134, 11, 0.15);
        border-color: #daa520;
    }

    .appointment-left-section {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        min-width: 200px;
    }

    .appointment-pet-section {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        background: linear-gradient(135deg, #fff8e1, #f8f6f0);
        border-radius: 12px;
        border: 1px solid #f3e8a6;
    }

    .appointment-pet-image {
        position: relative;
        width: 70px;
        height: 70px;
        border-radius: 50%;
        overflow: hidden;
        flex-shrink: 0;
        border: 3px solid #daa520;
        background: white;
        box-shadow: 0 3px 10px rgba(184, 134, 11, 0.2);
    }

    .pet-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .pet-image-placeholder {
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        background: #f8f6f0;
        color: #b8860b;
    }

    .pet-info {
        flex: 1;
    }

    .pet-name {
        font-size: 1.1rem;
        font-weight: 700;
        color: #b8860b;
        margin-bottom: 0.3rem;
        line-height: 1.2;
    }

    .pet-breed {
        font-size: 0.9rem;
        color: #666;
        font-weight: 500;
    }

    .pet-details-section {
        flex: 1;
    }

    .pet-stats {
        display: flex;
        gap: 1rem;
    }

    .pet-stat {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background: white;
        border: 1px solid #f3e8a6;
        border-radius: 20px;
        font-size: 0.85rem;
    }

    .stat-icon {
        font-size: 1rem;
    }

    .stat-text {
        font-weight: 600;
        color: #333;
    }

    .appointment-main-content {
        flex: 2;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .appointment-header {
        border-bottom: 2px solid #f3e8a6;
        padding-bottom: 1rem;
    }

    .appointment-title h4 {
        margin: 0 0 0.5rem 0;
        color: #b8860b;
        font-size: 1.3rem;
        font-weight: 700;
    }

    .appointment-meta {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .appointment-date {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #666;
        font-weight: 600;
        font-size: 0.95rem;
        padding: 0.4rem 0.8rem;
        background: #f8f6f0;
        border-radius: 8px;
    }

    .date-icon {
        font-size: 1rem;
    }

    .appointment-body {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        flex: 1;
    }

    .purpose-section, .vet-section {
        padding: 1rem;
        background: #fff8e1;
        border-radius: 10px;
        border-left: 4px solid #daa520;
    }

    .purpose-label, .vet-label {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
        color: #b8860b;
        font-size: 0.9rem;
    }

    .purpose-icon, .vet-icon {
        font-size: 1.1rem;
    }

    .purpose-text, .vet-text {
        margin: 0;
        color: #333;
        font-size: 0.95rem;
        line-height: 1.4;
        font-weight: 500;
    }

    .appointment-right-section {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
        min-width: 140px;
        justify-content: center;
    }

    .appointment-status {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.3rem;
        color: white;
        font-weight: 700;
        font-size: 0.75rem;
        padding: 1rem 0.8rem;
        border-radius: 12px;
        text-align: center;
        min-width: 100px;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
    }

    .status-icon {
        font-size: 1.5rem;
    }

    .status-text {
        letter-spacing: 0.5px;
    }

    .view-appointment-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        background: linear-gradient(135deg, #daa520, #b8860b);
        color: white;
        text-decoration: none;
        font-weight: 600;
        font-size: 0.9rem;
        padding: 0.8rem 1.2rem;
        border-radius: 10px;
        text-align: center;
        transition: all 0.2s ease;
        min-width: 100px;
        box-shadow: 0 3px 8px rgba(184, 134, 11, 0.3);
    }

    .view-appointment-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 12px rgba(184, 134, 11, 0.4);
    }

    .btn-icon {
        font-size: 1rem;
    }

    .owner-label {
        color: #666;
        font-weight: 500;
        font-size: 1.1rem;
    }

    .appointments-footer {
        margin-top: 1.5rem;
        text-align: center;
    }

    .view-all-appointments-link {
        color: #daa520;
        text-decoration: none;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        border: 1px solid #f3e8a6;
        border-radius: 8px;
        display: inline-block;
        transition: all 0.2s ease;
    }

    .view-all-appointments-link:hover {
        background: #f3e8a6;
        color: #b8860b;
    }

    .recent-activity {
        background: white;
        border-radius: 12px;
        border: 1px solid #f3e8a6;
        padding: 2rem;
        box-shadow: 0 2px 8px rgba(184, 134, 11, 0.1);
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
        margin: 0 2rem 1.5rem 2rem;
        max-width: 1200px;
        margin-left: auto;
        margin-right: auto;
        border: 1px solid #fcc;
    }

    .loading {
        text-align: center;
        padding: 3rem;
        color: #666;
        font-size: 1.1rem;
        max-width: 1200px;
        margin: 0 auto;
    }

    @media (max-width: 768px) {
        .dashboard-container {
            padding: 1rem;
        }

        .hero-content h1 {
            font-size: 2rem;
        }

        .stats-grid {
            grid-template-columns: 1fr;
        }

        .appointment-card {
            flex-direction: column;
            gap: 1rem;
        }

        .appointment-left-section {
            min-width: auto;
        }

        .appointment-pet-section {
            justify-content: center;
        }

        .pet-stats {
            justify-content: center;
        }

        .appointment-main-content {
            flex: none;
        }

        .appointment-header {
            text-align: center;
        }

        .appointment-title h4 {
            font-size: 1.1rem;
        }

        .appointment-right-section {
            flex-direction: row;
            justify-content: center;
            min-width: auto;
        }

        .appointment-status {
            flex-direction: row;
            gap: 0.5rem;
            padding: 0.8rem 1rem;
            min-width: auto;
        }

        .status-icon {
            font-size: 1.2rem;
        }

        .appointment-details {
            order: 1;
        }

        .stat-card, .appointments-section {
            padding: 1.25rem;
        }

        .activity-item {
            flex-direction: column;
            text-align: center;
        }
    }
</style>
