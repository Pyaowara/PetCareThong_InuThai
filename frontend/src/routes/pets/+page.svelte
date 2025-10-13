<script lang="ts">
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { isAuthenticated, user, authService } from '$lib/auth';
    import { petApi } from '$lib/apiServices';

    interface Pet {
        id: number;
        name: string;
        breed: string;
        gender?: string;
        age?: number;
        image_url?: string;
        owner_name: string;
    }

    let pets: Pet[] = [];
    let isLoading = true;
    let error = '';
    let showCreateForm = false;
    let searchTerm = '';

    // Form data for creating new pet
    let newPet = {
        name: '',
        breed: '',
        birth_date: '',
        color: '',
        gender: 'Male',
        allergic: '',
        marks: '',
        chronic_conditions: '',
        neutered_status: false,
        owner_id: null as number | null,
        image: null as File | null
    };
    
    let users: any[] = []; // For staff to select pet owner

    onMount(async () => {
        if (!$isAuthenticated) {
            goto('/login');
            return;
        }
        
        await loadPets();
        
        // Load users if staff (for owner selection)
        if ($user?.role === 'staff') {
            await loadUsers();
        }
    });

    async function loadUsers() {
        try {
            const { userApi } = await import('$lib/apiServices');
            users = await userApi.getUsersByRole('client');
        } catch (err) {
            console.error('Failed to load users:', err);
        }
    }

    function getTodayDate(): string {
        return new Date().toISOString().split("T")[0];
    }

    async function loadPets() {
        try {
            isLoading = true;
            const data = await petApi.getPets();
            pets = data;
            error = '';
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to load pets';
        } finally {
            isLoading = false;
        }
    }

    async function createPet() {
        try {
            const formData = new FormData();
            formData.append('name', newPet.name);
            formData.append('breed', newPet.breed);
            formData.append('birth_date', newPet.birth_date);
            formData.append('color', newPet.color);
            formData.append('gender', newPet.gender);
            formData.append('neutered_status', newPet.neutered_status.toString());
            if (newPet.allergic) formData.append('allergic', newPet.allergic);
            if (newPet.marks) formData.append('marks', newPet.marks);
            if (newPet.chronic_conditions) formData.append('chronic_conditions', newPet.chronic_conditions);
            if (newPet.owner_id) formData.append('owner_id', newPet.owner_id.toString());
            if (newPet.image) formData.append('image', newPet.image);

            await petApi.createPet(formData);
            
            // Reset form
            newPet = { 
                name: '', 
                breed: '', 
                birth_date: '', 
                color: '', 
                gender: 'Male', 
                allergic: '', 
                marks: '', 
                chronic_conditions: '', 
                neutered_status: false, 
                owner_id: null,
                image: null 
            };
            showCreateForm = false;
            
            // Reload pets
            await loadPets();
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to create pet';
        }
    }

    async function deletePet(petId: number) {
        if (!confirm('Are you sure you want to delete this pet?')) return;
        
        try {
            await petApi.deletePet(petId);
            await loadPets();
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to delete pet';
        }
    }

    function handleImageChange(event: Event) {
        const target = event.target as HTMLInputElement;
        if (target.files && target.files[0]) {
            newPet.image = target.files[0];
        }
    }

    function canEditPet(pet: Pet): boolean {
        if (!$user) return false;
        return $user.role === 'staff';
    }

    $: filteredPets = pets.filter(pet => 
        pet.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        pet.breed.toLowerCase().includes(searchTerm.toLowerCase()) ||
        pet.owner_name.toLowerCase().includes(searchTerm.toLowerCase())
    );
</script>

<svelte:head>
    <title>Pet Management - PetCare</title>
</svelte:head>

<div class="pets-container">
    <div class="pets-header">
        <h1>Pet Management</h1>
        <div class="header-actions">
            <input 
                type="text" 
                placeholder="Search pets..." 
                bind:value={searchTerm}
                class="search-input"
            />
            {#if $user?.role !== 'vet'}
            <button class="create-btn" on:click={() => showCreateForm = true}>
                Add New Pet
            </button>
            {/if}
        </div>
    </div>

    {#if error}
        <div class="error-message">{error}</div>
    {/if}

    {#if showCreateForm}
        <div class="modal-overlay" role="dialog" on:click={() => showCreateForm = false} on:keydown={(e) => e.key === 'Escape' && (showCreateForm = false)}>
            <div class="modal-content" role="document" on:click|stopPropagation on:keydown|stopPropagation>
                <h2>Add New Pet</h2>
                <form on:submit|preventDefault={createPet} class="pet-form">
                    <div class="form-group">
                        <label for="name">Pet Name *</label>
                        <input type="text" id="name" bind:value={newPet.name} required />
                    </div>
                    
                    {#if $user?.role === 'staff'}
                        <div class="form-group">
                            <label for="owner">Pet Owner *</label>
                            <select id="owner" bind:value={newPet.owner_id} required>
                                <option value={null}>Select pet owner</option>
                                {#each users as user (user.id)}
                                    <option value={user.id}>{user.full_name} ({user.email})</option>
                                {/each}
                            </select>
                        </div>
                    {/if}
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="breed">Breed *</label>
                            <input type="text" id="breed" bind:value={newPet.breed} required placeholder="e.g., Golden Retriever, Persian Cat" />
                        </div>
                        <div class="form-group">
                            <label for="gender">Gender</label>
                            <select id="gender" bind:value={newPet.gender}>
                                <option value="Male">Male</option>
                                <option value="Female">Female</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="birth_date">Birth Date *</label>
                            <input type="date" id="birth_date" bind:value={newPet.birth_date} max={getTodayDate()} required />
                        </div>
                        <div class="form-group">
                            <label for="color">Color *</label>
                            <input type="text" id="color" bind:value={newPet.color} required placeholder="e.g., Brown, Black, White" />
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="allergic">Allergies (optional)</label>
                        <textarea id="allergic" bind:value={newPet.allergic} placeholder="Any known allergies"></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="marks">Distinctive Marks (optional)</label>
                        <textarea id="marks" bind:value={newPet.marks} placeholder="Unique physical characteristics"></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="chronic_conditions">Chronic Conditions (optional)</label>
                        <textarea id="chronic_conditions" bind:value={newPet.chronic_conditions} placeholder="Any chronic health conditions"></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" bind:checked={newPet.neutered_status} />
                            Neutered/Spayed
                        </label>
                    </div>
                    
                    <div class="form-group">
                        <label for="image">Pet Photo</label>
                        <input type="file" id="image" accept="image/*" on:change={handleImageChange} />
                    </div>
                    
                    <div class="form-actions">
                        <button type="button" class="cancel-btn" on:click={() => showCreateForm = false}>
                            Cancel
                        </button>
                        <button type="submit" class="submit-btn">Create Pet</button>
                    </div>
                </form>
            </div>
        </div>
    {/if}

    {#if isLoading}
        <div class="loading">Loading pets...</div>
    {:else if filteredPets.length === 0}
        <div class="no-data">
            {searchTerm ? 'No pets found matching your search.' : 'No pets registered yet.'}
        </div>
    {:else}
        <div class="pets-grid">
            {#each filteredPets as pet (pet.id)}
                <div class="pet-card">
                    {#if pet.image_url}
                        <img src={pet.image_url} alt={pet.name} class="pet-image" />
                    {:else}
                        <div class="pet-image-placeholder">🐾</div>
                    {/if}
                    
                    <div class="pet-info">
                        <h3>{pet.name}</h3>
                        <p class="pet-breed">{pet.breed}</p>
                        
                        <div class="pet-details">
                            {#if pet.gender}<span>Gender: {pet.gender}</span>{/if}
                            {#if pet.age}<span>Age: {pet.age} years old</span>{/if}
                        </div>
                        
                        <p class="pet-owner">Owner: {pet.owner_name}</p>
                        
                        <div class="pet-actions">
                            <button class="view-btn" on:click={() => goto(`/pets/${pet.id}`)}>
                                View Details
                            </button>
                            
                            {#if canEditPet(pet)}
                                <button class="delete-btn" on:click={() => deletePet(pet.id)}>
                                    Delete
                                </button>
                            {/if}
                        </div>
                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div>

<style>
    .pets-container {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }

    .pets-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        flex-wrap: wrap;
        gap: 1rem;
    }

    .pets-header h1 {
        margin: 0;
        color: #b8860b;
        font-size: 2rem;
        font-weight: 700;
    }

    .header-actions {
        display: flex;
        gap: 1rem;
        align-items: center;
    }

    .search-input {
        padding: 0.5rem 1rem;
        border: 2px solid #f3e8a6;
        border-radius: 8px;
        font-size: 0.95rem;
        min-width: 200px;
    }

    .search-input:focus {
        outline: none;
        border-color: #daa520;
    }

    .create-btn {
        background: linear-gradient(135deg, #daa520 0%, #b8860b 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: transform 0.2s ease;
    }

    .create-btn:hover {
        transform: translateY(-1px);
    }

    .pets-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 1.5rem;
    }

    .pet-card {
        background: white;
        border-radius: 12px;
        border: 1px solid #f3e8a6;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(184, 134, 11, 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .pet-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(218, 165, 32, 0.15);
    }

    .pet-image {
        width: 100%;
        height: 200px;
        object-fit: cover;
    }

    .pet-image-placeholder {
        width: 100%;
        height: 200px;
        background: #f8f6f0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 3rem;
    }

    .pet-info {
        padding: 1.5rem;
    }

    .pet-info h3 {
        margin: 0 0 0.5rem 0;
        color: #333;
        font-size: 1.25rem;
    }

    .pet-breed {
        margin: 0 0 1rem 0;
        color: #666;
        font-weight: 500;
    }

    .pet-details {
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }

    .pet-details span {
        background: #fff8e1;
        color: #b8860b;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.875rem;
    }

    .pet-owner {
        margin: 0 0 1rem 0;
        color: #666;
        font-size: 0.9rem;
    }

    .pet-actions {
        display: flex;
        gap: 0.5rem;
    }

    .view-btn {
        flex: 1;
        background: #daa520;
        color: white;
        border: none;
        padding: 0.5rem;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.875rem;
    }

    .delete-btn {
        background: #dc3545;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.875rem;
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
    }

    .pet-form {
        display: flex;
        flex-direction: column;
        gap: 1rem;
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
    .form-group select,
    .form-group textarea {
        padding: 0.75rem;
        border: 2px solid #f3e8a6;
        border-radius: 8px;
        font-size: 0.95rem;
        background: white;
        font-family: inherit;
    }

    .form-group textarea {
        min-height: 80px;
        resize: vertical;
    }

    .form-group input:focus,
    .form-group select:focus,
    .form-group textarea:focus {
        outline: none;
        border-color: #daa520;
    }

    .checkbox-label {
        display: flex !important;
        flex-direction: row !important;
        align-items: center;
        gap: 0.5rem;
        cursor: pointer;
    }

    .checkbox-label input[type="checkbox"] {
        width: auto;
        padding: 0;
        margin: 0;
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
    }

    .error-message {
        background: #fee;
        color: #c33;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #fcc;
    }

    .loading, .no-data {
        text-align: center;
        padding: 3rem;
        color: #666;
        font-size: 1.1rem;
    }

    @media (max-width: 768px) {
        .pets-header {
            flex-direction: column;
            align-items: stretch;
        }

        .header-actions {
            flex-direction: column;
        }

        .pets-grid {
            grid-template-columns: 1fr;
        }

        .form-row {
            grid-template-columns: 1fr;
        }
    }
</style>