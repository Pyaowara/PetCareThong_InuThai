<script lang="ts">
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { isAuthenticated, user, authService } from '$lib/auth';
    import { userApi } from '$lib/apiServices';

    interface User {
        id: number;
        email: string;
        full_name: string;
        phone_number?: string;
        role: 'client' | 'staff' | 'vet';
        active: boolean;
        created_at: string;
        image_url?: string;
    }

    let users: User[] = [];
    let isLoading = true;
    let error = '';
    let searchQuery = '';
    let roleFilter = '';
    let statusFilter = '';
    let showProfileModal = false;
    let editingUser: User | null = null;

    // Profile form data
    let profileForm = {
        full_name: '',
        email: '',
        phone_number: '',
        role: 'client' as 'client' | 'staff' | 'vet',
        active: true,
        current_password: '',
        password: '',
        image: null as File | null
    };

    $: filteredUsers = users.filter(u => {
        const matchesSearch = !searchQuery || 
            u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
            u.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            (u.phone_number && u.phone_number.toLowerCase().includes(searchQuery.toLowerCase()));
        
        const matchesRole = !roleFilter || u.role === roleFilter;
        const matchesStatus = !statusFilter || 
            (statusFilter === 'active' && u.active) ||
            (statusFilter === 'inactive' && !u.active);
        
        return matchesSearch && matchesRole && matchesStatus;
    });

    onMount(async () => {
        if (!$isAuthenticated) {
            goto('/login');
            return;
        }
        
        // Check if user has permission to view user management
        if ($user?.role === 'client') {
            // Clients can only view their own profile
            await loadOwnProfile();
        } else {
            // Staff and vets can view all users
            await loadUsers();
        }
    });

    async function loadUsers() {
        if ($user?.role === 'client') return;
        
        try {
            isLoading = true;
            users = await userApi.getUsers();
            error = '';
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to load users';
        } finally {
            isLoading = false;
        }
    }

    async function loadOwnProfile() {
        try {
            isLoading = true;
            const profile = await userApi.getProfile();
            users = [profile];
            error = '';
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to load profile';
        } finally {
            isLoading = false;
        }
    }

    async function toggleUserStatus(targetUser: User) {
        if ($user?.role === 'client' || targetUser.id === $user?.id) {
            error = 'You cannot deactivate your own account or change user status as a client';
            return;
        }

        const action = targetUser.active ? 'deactivate' : 'activate';
        if (!confirm(`Are you sure you want to ${action} ${targetUser.full_name}?`)) {
            return;
        }

        try {
            await userApi.updateUserStatus(targetUser.id, !targetUser.active);
            await loadUsers();
        } catch (err) {
            error = err instanceof Error ? err.message : `Failed to ${action} user`;
        }
    }

    function startEditProfile(targetUser: User) {
        editingUser = targetUser;
        profileForm = {
            full_name: targetUser.full_name,
            email: targetUser.email,
            phone_number: targetUser.phone_number || '',
            role: targetUser.role,
            active: targetUser.active,
            current_password: '',
            password: '',
            image: null
        };
        showProfileModal = true;
    }

    function resetForm() {
        profileForm = { 
            full_name: '', 
            email: '', 
            phone_number: '', 
            role: 'client',
            active: true,
            current_password: '', 
            password: '', 
            image: null 
        };
        editingUser = null;
        error = '';
    }

    async function updateProfile() {
        if (!editingUser) return;
        
        try {
            const formData = new FormData();
            formData.append('full_name', profileForm.full_name);
            formData.append('email', profileForm.email);
            if (profileForm.phone_number) formData.append('phone_number', profileForm.phone_number);
            
            // Staff can edit roles and active status for other users
            if ($user?.role === 'staff' && editingUser.id !== $user.id) {
                formData.append('role', profileForm.role);
                formData.append('active', profileForm.active.toString());
            }
            
            // For clients, current password is required
            if ($user?.role === 'client') {
                if (!profileForm.current_password) {
                    error = 'Current password is required to update your profile';
                    return;
                }
                formData.append('current_password', profileForm.current_password);
            }
            
            // If changing password
            if (profileForm.password) {
                formData.append('password', profileForm.password);
            }
            
            // If uploading image
            if (profileForm.image) {
                formData.append('image', profileForm.image);
            }

            await userApi.updateUser(editingUser.id, formData);
            
            // Reload appropriate data based on user role
            if ($user?.role === 'client') {
                await loadOwnProfile();
            } else {
                await loadUsers();
            }
            
            resetForm();
            showProfileModal = false;
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to update profile';
        }
    }

    function handleImageChange(event: Event) {
        const target = event.target as HTMLInputElement;
        if (target.files && target.files[0]) {
            profileForm.image = target.files[0];
        }
    }

    function clearFilters() {
        searchQuery = '';
        roleFilter = '';
        statusFilter = '';
    }

    function canViewAllUsers(): boolean {
        return $user?.role === 'staff' || $user?.role === 'vet';
    }

    function canEditUser(targetUser: User): boolean {
        // Users can always edit their own profile
        if (targetUser.id === $user?.id) return true;
        
        // Staff can edit other users (but not change roles/status)
        return $user?.role === 'staff';
    }

    function canToggleUserStatus(targetUser: User): boolean {
        // Only staff can toggle status, and not their own
        return $user?.role === 'staff' && targetUser.id !== $user?.id;
    }

    function canEditUserRole(targetUser: User): boolean {
        // Only staff can edit roles, and not their own
        return $user?.role === 'staff' && targetUser.id !== $user?.id;
    }

    function getRoleBadgeClass(role: string): string {
        switch (role) {
            case 'vet': return 'role-vet';
            case 'staff': return 'role-staff';
            case 'client': return 'role-client';
            default: return 'role-client';
        }
    }

    function formatDate(dateString: string): string {
        return new Date(dateString).toLocaleDateString();
    }

    function formatDateTime(dateString: string | undefined): string {
        if (!dateString) return 'Never';
        return new Date(dateString).toLocaleString();
    }

    function viewHistory(userId: number) {
        goto(`/history/${userId}`);
    }
</script>

<svelte:head>
    <title>{canViewAllUsers() ? 'User Management' : 'My Profile'} - PetCare</title>
</svelte:head>

<div class="users-container">
    <div class="users-header">
        <h1>{canViewAllUsers() ? 'User Management' : 'My Profile'}</h1>
    </div>

    {#if canViewAllUsers()}
        <!-- Filters (only for staff/vet) -->
        <div class="filters-section">
            <div class="filters-row">
                <div class="filter-group">
                    <label for="searchFilter">Search</label>
                    <input
                        type="text"
                        id="searchFilter"
                        placeholder="Search by name, email, or phone..."
                        bind:value={searchQuery}
                        class="filter-input"
                    />
                </div>
                
                <div class="filter-group">
                    <label for="roleFilter">Role</label>
                    <select id="roleFilter" bind:value={roleFilter} class="filter-select">
                        <option value="">All Roles</option>
                        <option value="client">Client</option>
                        <option value="staff">Staff</option>
                        <option value="vet">Veterinarian</option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <label for="statusFilter">Status</label>
                    <select id="statusFilter" bind:value={statusFilter} class="filter-select">
                        <option value="">All Status</option>
                        <option value="active">Active</option>
                        <option value="inactive">Inactive</option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <button class="clear-filters-btn" on:click={clearFilters}>
                        Clear Filters
                    </button>
                </div>
            </div>
        </div>
    {/if}

    {#if error}
        <div class="error-message">{error}</div>
    {/if}

    {#if isLoading}
        <div class="loading">Loading {canViewAllUsers() ? 'users' : 'profile'}...</div>
    {:else if filteredUsers.length === 0}
        <div class="no-data">
            {searchQuery || roleFilter || statusFilter 
                ? 'No users found matching your filters.' 
                : 'No users available.'}
        </div>
    {:else}
        {#if canViewAllUsers()}
            <!-- Users Table -->
            <div class="users-table-container">
                <table class="users-table">
                    <thead>
                        <tr>
                            <th>User</th>
                            <th>Role</th>
                            <th>Status</th>
                            <th>Joined</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each filteredUsers as u (u.id)}
                            <tr class={!u.active ? 'user-inactive' : ''}>
                                <td>
                                    <div class="user-info">
                                        <div class="user-avatar">
                                            {#if u.image_url}
                                                <img src={u.image_url} alt={u.full_name} class="avatar-image" />
                                            {:else}
                                                <div class="avatar-placeholder">👤</div>
                                            {/if}
                                        </div>
                                        <div class="user-details">
                                            <strong>{u.full_name}</strong>
                                            <br><span class="phone">{u.phone_number || 'No phone'}</span>
                                            <br><span class="email">{u.email}</span>
                                        </div>
                                    </div>
                                </td>
                                <td>
                                    <span class="role-badge {getRoleBadgeClass(u.role)}">
                                        {u.role.charAt(0).toUpperCase() + u.role.slice(1)}
                                    </span>
                                </td>
                                <td>
                                    <span class="status-badge {u.active ? 'status-active' : 'status-inactive'}">
                                        {u.active ? 'Active' : 'Inactive'}
                                    </span>
                                </td>
                                <td>{formatDate(u.created_at)}</td>
                                <td>
                                    <div class="user-actions">
                                        {#if canEditUser(u)}
                                            <button class="edit-btn" on:click={() => startEditProfile(u)}>
                                                Edit Profile
                                            </button>
                                        {/if}
                                        {#if canToggleUserStatus(u)}
                                            <button 
                                                class="toggle-btn {u.active ? 'deactivate-btn' : 'activate-btn'}" 
                                                on:click={() => toggleUserStatus(u)}
                                            >
                                                {u.active ? 'Deactivate' : 'Activate'}
                                            </button>
                                        {/if}
                                        {#if u.role === 'client'}
                                            <button class="view-history-btn" on:click={() => viewHistory(u.id)}>
                                                View History
                                            </button>
                                        {/if}
                                    </div>
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        {:else}
            <!-- Profile Display (for clients) -->
            {#each filteredUsers as u (u.id)}
                <div class="profile-container">
                    <div class="profile-header">
                        <button class="back-btn" on:click={() => goto('/')}>
                            ← Back to Dashboard
                        </button>
                        
                        <div class="header-actions">
                            <button class="edit-btn" on:click={() => startEditProfile(u)}>
                                Edit Profile
                            </button>
                        </div>
                    </div>

                    <div class="profile-content">
                        <div class="profile-main-info">
                            <div class="profile-image-section">
                                {#if u.image_url}
                                    <img src={u.image_url} alt={u.full_name} class="profile-image" />
                                {:else}
                                    <div class="profile-image-placeholder">👤</div>
                                {/if}
                            </div>

                            <div class="profile-info-section">
                                <h1>{u.full_name}</h1>
                                <div class="profile-details">
                                    <div class="detail-item">
                                        <strong>Email:</strong> {u.email}
                                    </div>
                                    <div class="detail-item">
                                        <strong>Phone:</strong> {u.phone_number || 'Not provided'}
                                    </div>
                                    <div class="detail-item">
                                        <strong>Role:</strong> 
                                        <span class="role-badge {getRoleBadgeClass(u.role)}">
                                            {u.role.charAt(0).toUpperCase() + u.role.slice(1)}
                                        </span>
                                    </div>
                                    <div class="detail-item">
                                        <strong>Account Status:</strong>
                                        <span class="status-badge {u.active ? 'status-active' : 'status-inactive'}">
                                            {u.active ? 'Active' : 'Inactive'}
                                        </span>
                                    </div>
                                    <div class="detail-item">
                                        <strong>Member Since:</strong> {formatDate(u.created_at)}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="profile-stats-section">
                            <div class="section-header">
                                <h2>Quick Links</h2>
                            </div>
                            
                            <div class="quick-links">
                                <a href="/pets" class="quick-link-card">
                                    <div class="link-icon">🐾</div>
                                    <div class="link-info">
                                        <h3>My Pets</h3>
                                        <p>View and manage your pets</p>
                                    </div>
                                </a>
                                
                                <a href="/vaccinations" class="quick-link-card">
                                    <div class="link-icon">💉</div>
                                    <div class="link-info">
                                        <h3>Vaccinations</h3>
                                        <p>Track vaccination records</p>
                                    </div>
                                </a>
                                
                                <a href="/vaccines" class="quick-link-card">
                                    <div class="link-icon">🔬</div>
                                    <div class="link-info">
                                        <h3>Available Vaccines</h3>
                                        <p>Browse vaccine information</p>
                                    </div>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            {/each}
        {/if}
    {/if}

    <!-- Edit Profile Modal -->
    {#if showProfileModal && editingUser}
        <div class="modal-overlay" role="dialog" tabindex="-1" on:click={() => { showProfileModal = false; resetForm(); }} on:keydown={(e) => e.key === 'Escape' && (showProfileModal = false, resetForm())}>
            <div class="modal-content" on:click|stopPropagation on:keydown|stopPropagation>
                <h2>Edit Profile - {editingUser.full_name}</h2>
                
                <form on:submit|preventDefault={updateProfile} class="profile-form">
                    <div class="form-group">
                        <label for="fullName">Full Name *</label>
                        <input
                            type="text"
                            id="fullName"
                            bind:value={profileForm.full_name}
                            required
                        />
                    </div>
                    
                    <div class="form-group">
                        <label for="email">Email *</label>
                        <input
                            type="email"
                            id="email"
                            bind:value={profileForm.email}
                            required
                        />
                    </div>
                    
                    <div class="form-group">
                        <label for="phone">Phone Number</label>
                        <input
                            type="tel"
                            id="phone"
                            bind:value={profileForm.phone_number}
                        />
                    </div>

                    {#if $user?.role === 'staff' && editingUser.id !== $user.id}
                        <div class="form-group">
                            <label for="userRole">Role *</label>
                            <select id="userRole" bind:value={profileForm.role} required>
                                <option value="client">Client</option>
                                <option value="staff">Staff</option>
                                <option value="vet">Veterinarian</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label class="checkbox-label">
                                <input
                                    type="checkbox"
                                    bind:checked={profileForm.active}
                                />
                                <span>Account Active</span>
                            </label>
                        </div>
                    {/if}

                    {#if $user?.role === 'client'}
                        <div class="form-group">
                            <label for="currentPassword">Current Password *</label>
                            <input
                                type="password"
                                id="currentPassword"
                                bind:value={profileForm.current_password}
                                placeholder="Required to update profile"
                                required
                            />
                        </div>
                    {/if}
                    
                    <div class="form-group">
                        <label for="newPassword">New Password (optional)</label>
                        <input
                            type="password"
                            id="newPassword"
                            bind:value={profileForm.password}
                            placeholder="Leave blank to keep current password"
                        />
                    </div>
                    
                    <div class="form-group">
                        <label for="profileImage">Profile Image</label>
                        <input
                            type="file"
                            id="profileImage"
                            accept="image/*"
                            on:change={handleImageChange}
                        />
                        {#if editingUser.image_url}
                            <div class="current-image">
                                <img src={editingUser.image_url} alt="Current profile" class="preview-image" />
                                <span class="image-label">Current image</span>
                            </div>
                        {/if}
                    </div>
                    
                    <div class="form-actions">
                        <button type="button" class="cancel-btn" on:click={() => { showProfileModal = false; resetForm(); }}>
                            Cancel
                        </button>
                        <button type="submit" class="submit-btn">
                            Update Profile
                        </button>
                    </div>
                </form>
            </div>
        </div>
    {/if}
</div>

<style>
    .phone, .email {
        color: #666;
        font-size: 0.875rem;
    }

    .user-info {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .user-avatar {
        flex-shrink: 0;
    }

    .avatar-image {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #f3e8a6;
    }

    .avatar-placeholder {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: #f3e8a6;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        color: #b8860b;
    }

    .user-details {
        flex: 1;
    }

    .current-image {
        margin-top: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .preview-image {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #f3e8a6;
    }

    .image-label {
        color: #666;
        font-size: 0.875rem;
        font-style: italic;
    }

    .users-container {
        padding: 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }

    .users-header {
        margin-bottom: 2rem;
    }

    .users-header h1 {
        margin: 0;
        color: #b8860b;
        font-size: 2rem;
    }

    .filters-section {
        background: white;
        border-radius: 12px;
        border: 1px solid #f3e8a6;
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 2px 4px rgba(184, 134, 11, 0.1);
    }

    .filters-row {
        display: grid;
        grid-template-columns: 2fr 1fr 1fr auto;
        gap: 1rem;
        align-items: end;
    }

    .filter-group {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .filter-group label {
        font-weight: 600;
        color: #333;
        font-size: 0.9rem;
    }

    .filter-input,
    .filter-select {
        padding: 0.65rem;
        border: 2px solid #f3e8a6;
        border-radius: 6px;
        font-size: 0.9rem;
        background: white;
    }

    .filter-input:focus,
    .filter-select:focus {
        outline: none;
        border-color: #daa520;
    }

    .clear-filters-btn {
        background: #6c757d;
        color: white;
        border: none;
        padding: 0.65rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.9rem;
        white-space: nowrap;
    }

    .users-table-container {
        background: white;
        border-radius: 12px;
        border: 1px solid #f3e8a6;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(184, 134, 11, 0.1);
    }

    .users-table {
        width: 100%;
        border-collapse: collapse;
    }

    .users-table th {
        background: #f8f6f0;
        color: #b8860b;
        font-weight: 700;
        padding: 1rem;
        text-align: left;
        border-bottom: 2px solid #f3e8a6;
    }

    .users-table td {
        padding: 1rem;
        border-bottom: 1px solid #f3e8a6;
        vertical-align: top;
    }

    .users-table tr:hover {
        background: #fffdf5;
    }

    .user-inactive {
        opacity: 0.6;
    }

    .user-info {
        line-height: 1.4;
    }

    .username {
        color: #666;
        font-size: 0.9rem;
    }

    .email {
        color: #888;
        font-size: 0.85rem;
    }

    .role-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .role-vet {
        background: #e8f5e8;
        color: #2d7d2d;
    }

    .role-staff {
        background: #e3f2fd;
        color: #1976d2;
    }

    .role-client {
        background: #fff3e0;
        color: #f57c00;
    }

    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .status-active {
        background: #e8f5e8;
        color: #2d7d2d;
    }

    .status-inactive {
        background: #ffebee;
        color: #d32f2f;
    }

    .user-actions {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }

    .edit-btn {
        background: #daa520;
        color: white;
        border: none;
        padding: 0.4rem 0.8rem;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.85rem;
    }
    .view-history-btn {
        background: #193ee5;
        color: white;
        border: none;
        padding: 0.4rem 0.8rem;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.85rem;
    }

    .toggle-btn {
        border: none;
        padding: 0.4rem 0.8rem;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.85rem;
    }

    .deactivate-btn {
        background: #dc3545;
        color: white;
    }

    .activate-btn {
        background: #28a745;
        color: white;
    }

    .profile-container {
        padding: 0;
        max-width: 1200px;
        margin: 0 auto;
    }

    .profile-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
    }

    .back-btn {
        background: none;
        border: 2px solid #f3e8a6;
        color: #b8860b;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        text-decoration: none;
    }

    .back-btn:hover {
        background: #f3e8a6;
    }

    .header-actions {
        display: flex;
        gap: 0.5rem;
    }

    .profile-content {
        background: white;
        border-radius: 12px;
        border: 1px solid #f3e8a6;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(184, 134, 11, 0.1);
    }

    .profile-main-info {
        display: grid;
        grid-template-columns: 300px 1fr;
        gap: 2rem;
        padding: 2rem;
    }

    .profile-image-section {
        display: flex;
        justify-content: center;
        align-items: flex-start;
    }

    .profile-image {
        width: 250px;
        height: 250px;
        object-fit: cover;
        border-radius: 50%;
        border: 4px solid #f3e8a6;
        box-shadow: 0 4px 8px rgba(184, 134, 11, 0.2);
    }

    .profile-image-placeholder {
        width: 250px;
        height: 250px;
        background: linear-gradient(135deg, #f8f6f0 0%, #f3e8a6 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 6rem;
        border-radius: 50%;
        border: 4px solid #f3e8a6;
        box-shadow: 0 4px 8px rgba(184, 134, 11, 0.2);
    }

    .profile-info-section h1 {
        margin: 0 0 1.5rem 0;
        color: #b8860b;
        font-size: 2.5rem;
        font-weight: 700;
    }

    .profile-details {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
    }

    .detail-item {
        background: #fff8e1;
        padding: 1.25rem;
        border-radius: 8px;
        border-left: 4px solid #daa520;
    }

    .detail-item strong {
        color: #b8860b;
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }

    .profile-stats-section {
        padding: 2rem;
        border-top: 1px solid #f3e8a6;
        background: #fffdf5;
    }

    .section-header {
        margin-bottom: 1.5rem;
    }

    .section-header h2 {
        margin: 0;
        color: #b8860b;
        font-size: 1.5rem;
    }

    .quick-links {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1.5rem;
    }

    .quick-link-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        border: 2px solid #f3e8a6;
        text-decoration: none;
        color: inherit;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 1rem;
        box-shadow: 0 2px 4px rgba(184, 134, 11, 0.1);
    }

    .quick-link-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(218, 165, 32, 0.15);
        border-color: #daa520;
    }

    .link-icon {
        font-size: 2.5rem;
        width: 60px;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #f8f6f0;
        border-radius: 50%;
        flex-shrink: 0;
    }

    .link-info h3 {
        margin: 0 0 0.5rem 0;
        color: #b8860b;
        font-size: 1.1rem;
        font-weight: 600;
    }

    .link-info p {
        margin: 0;
        color: #666;
        font-size: 0.9rem;
    }

    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        padding: 2rem;
    }

    .modal-content {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        width: 100%;
        max-width: 500px;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
    }

    .modal-content h2 {
        margin: 0 0 1.5rem 0;
        color: #b8860b;
        font-size: 1.5rem;
    }

    .profile-form {
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
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

    .form-group label {
        font-weight: 600;
        color: #333;
    }

    .form-group input,
    .form-group select {
        padding: 0.75rem;
        border: 2px solid #f3e8a6;
        border-radius: 8px;
        font-size: 0.95rem;
        background: white;
        font-family: inherit;
    }

    .form-group input:focus,
    .form-group select:focus {
        outline: none;
        border-color: #daa520;
    }

    .checkbox-label {
        display: flex !important;
        flex-direction: row !important;
        align-items: center;
        gap: 0.5rem;
        cursor: pointer;
        font-weight: 600;
        color: #333;
    }

    .checkbox-label input[type="checkbox"] {
        width: auto;
        padding: 0;
        margin: 0;
        transform: scale(1.2);
    }

    .form-actions {
        display: flex;
        gap: 1rem;
        justify-content: flex-end;
        margin-top: 1rem;
    }

    .cancel-btn {
        background: #6c757d;
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        cursor: pointer;
    }

    .submit-btn {
        background: linear-gradient(135deg, #daa520 0%, #b8860b 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
    }

    .error-message {
        background: #fee;
        color: #c33;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        border: 1px solid #fcc;
    }

    .loading,
    .no-data {
        text-align: center;
        padding: 3rem;
        color: #666;
        font-size: 1.1rem;
        background: white;
        border-radius: 12px;
        border: 1px solid #f3e8a6;
    }

    @media (max-width: 1024px) {
        .filters-row {
            grid-template-columns: 1fr 1fr;
        }

        .users-table-container {
            overflow-x: auto;
        }

        .users-table {
            min-width: 900px;
        }

        .profile-main-info {
            grid-template-columns: 1fr;
            text-align: center;
        }

        .profile-details {
            grid-template-columns: 1fr;
        }

        .quick-links {
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        }
    }

    @media (max-width: 768px) {
        .filters-row {
            grid-template-columns: 1fr;
        }

        .form-row {
            grid-template-columns: 1fr;
        }

        .user-actions {
            flex-direction: column;
        }

        .profile-header {
            flex-direction: column;
            gap: 1rem;
            align-items: stretch;
        }

        .profile-image,
        .profile-image-placeholder {
            width: 200px;
            height: 200px;
            font-size: 4rem;
        }

        .profile-info-section h1 {
            font-size: 2rem;
        }

        .quick-links {
            grid-template-columns: 1fr;
        }

        .quick-link-card {
            flex-direction: column;
            text-align: center;
            gap: 1rem;
        }

        .link-icon {
            width: 50px;
            height: 50px;
            font-size: 2rem;
        }
    }
</style>