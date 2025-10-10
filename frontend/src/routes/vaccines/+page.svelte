<script lang="ts">
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { isAuthenticated, user, authService } from '$lib/auth';
    import { vaccineApi } from '$lib/apiServices';

    interface Vaccine {
        id: number;
        name: string;
        description?: string;
        created_at: string;
    }

    let vaccines: Vaccine[] = [];
    let isLoading = true;
    let error = '';
    let searchQuery = '';
    let showCreateModal = false;
    let editingVaccine: Vaccine | null = null;

    // Form data
    let vaccineForm = {
        name: '',
        description: ''
    };

    $: filteredVaccines = vaccines.filter(vaccine =>
        vaccine.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (vaccine.description && vaccine.description.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    onMount(async () => {
        if (!$isAuthenticated) {
            goto('/login');
            return;
        }
        
        await loadVaccines();
    });

    async function loadVaccines() {
        try {
            isLoading = true;
            vaccines = await vaccineApi.getVaccines();
            error = '';
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to load vaccines';
        } finally {
            isLoading = false;
        }
    }

    async function createVaccine() {
        if (!vaccineForm.name.trim()) {
            error = 'Vaccine name is required';
            return;
        }

        try {
            await vaccineApi.createVaccine(vaccineForm);
            await loadVaccines();
            resetForm();
            showCreateModal = false;
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to create vaccine';
        }
    }

    async function updateVaccine() {
        if (!editingVaccine || !vaccineForm.name.trim()) {
            error = 'Vaccine name is required';
            return;
        }

        try {
            await vaccineApi.updateVaccine(editingVaccine.id, vaccineForm);
            await loadVaccines();
            resetForm();
            editingVaccine = null;
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to update vaccine';
        }
    }

    async function deleteVaccine(vaccine: Vaccine) {
        if (!confirm(`Are you sure you want to delete "${vaccine.name}"? This action cannot be undone.`)) {
            return;
        }

        try {
            await vaccineApi.deleteVaccine(vaccine.id);
            await loadVaccines();
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to delete vaccine';
        }
    }

    function startEdit(vaccine: Vaccine) {
        editingVaccine = vaccine;
        vaccineForm = {
            name: vaccine.name,
            description: vaccine.description || ''
        };
    }

    function resetForm() {
        vaccineForm = { name: '', description: '' };
        editingVaccine = null;
        error = '';
    }

    function canManageVaccines(): boolean {
        return $user?.role === 'staff';
    }

    function formatDate(dateString: string): string {
        return new Date(dateString).toLocaleDateString();
    }
</script>

<svelte:head>
    <title>Vaccines Management - PetCare</title>
</svelte:head>

<div class="vaccines-container">
    <div class="vaccines-header">
        <h1>Vaccines available</h1>
        
        <div class="header-actions">
            <div class="search-container">
                <input
                    type="text"
                    placeholder="Search vaccines..."
                    bind:value={searchQuery}
                    class="search-input"
                />
            </div>
            
            {#if canManageVaccines()}
                <button class="create-btn" on:click={() => showCreateModal = true}>
                    Add New Vaccine
                </button>
            {/if}
        </div>
    </div>

    {#if error}
        <div class="error-message">{error}</div>
    {/if}

    {#if isLoading}
        <div class="loading">Loading vaccines...</div>
    {:else if filteredVaccines.length === 0}
        <div class="no-data">
            {searchQuery ? 'No vaccines found matching your search.' : 'No vaccines available yet.'}
        </div>
    {:else}
        <div class="vaccines-grid">
            {#each filteredVaccines as vaccine (vaccine.id)}
                <div class="vaccine-card">
                    <div class="vaccine-info">
                        <h3>{vaccine.name}</h3>
                        {#if vaccine.description}
                            <p class="vaccine-description">{vaccine.description}</p>
                        {/if}
                    </div>
                    
                    {#if canManageVaccines()}
                        <div class="vaccine-actions">
                            <button class="edit-btn" on:click={() => startEdit(vaccine)}>
                                Edit
                            </button>
                            <button class="delete-btn" on:click={() => deleteVaccine(vaccine)}>
                                Delete
                            </button>
                        </div>
                    {/if}
                </div>
            {/each}
        </div>
    {/if}

    <!-- Create/Edit Vaccine Modal -->
    {#if showCreateModal || editingVaccine}
        <div class="modal-overlay" role="dialog" tabindex="-1" on:click={() => { showCreateModal = false; resetForm(); }} on:keydown={(e) => e.key === 'Escape' && (showCreateModal = false, resetForm())}>
            <div class="modal-content" on:click|stopPropagation on:keydown|stopPropagation>
                <h2>{editingVaccine ? 'Edit Vaccine' : 'Add New Vaccine'}</h2>
                
                <form on:submit|preventDefault={editingVaccine ? updateVaccine : createVaccine} class="vaccine-form">
                    <div class="form-group">
                        <label for="vaccineName">Vaccine Name *</label>
                        <input
                            type="text"
                            id="vaccineName"
                            bind:value={vaccineForm.name}
                            placeholder="e.g., Rabies, Distemper, Parvovirus"
                            required
                        />
                    </div>
                    
                    <div class="form-group">
                        <label for="vaccineDescription">Description</label>
                        <textarea
                            id="vaccineDescription"
                            bind:value={vaccineForm.description}
                            placeholder="Optional description of the vaccine..."
                            rows="4"
                        ></textarea>
                    </div>
                    
                    <div class="form-actions">
                        <button type="button" class="cancel-btn" on:click={resetForm}>
                            Cancel
                        </button>
                        <button type="submit" class="submit-btn">
                            {editingVaccine ? 'Update Vaccine' : 'Add Vaccine'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    {/if}
</div>

<style>
    .vaccines-container {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }

    .vaccines-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        gap: 2rem;
    }

    .vaccines-header h1 {
        margin: 0;
        color: #b8860b;
        font-size: 2rem;
    }

    .header-actions {
        display: flex;
        gap: 1rem;
        align-items: center;
    }

    .search-container {
        position: relative;
    }

    .search-input {
        padding: 0.75rem 1rem;
        border: 2px solid #f3e8a6;
        border-radius: 8px;
        font-size: 0.95rem;
        min-width: 300px;
        background: white;
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
        cursor: pointer;
        font-weight: 600;
        white-space: nowrap;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .create-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(184, 134, 11, 0.3);
    }

    .vaccines-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
        gap: 1.5rem;
    }

    .vaccine-card {
        background: white;
        border-radius: 12px;
        border: 1px solid #f3e8a6;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(184, 134, 11, 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .vaccine-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(184, 134, 11, 0.2);
    }

    .vaccine-info h3 {
        margin: 0 0 0.75rem 0;
        color: #b8860b;
        font-size: 1.25rem;
        font-weight: 700;
    }

    .vaccine-description {
        margin: 0 0 1rem 0;
        color: #666;
        line-height: 1.5;
    }

    .vaccine-date {
        margin: 0 0 1rem 0;
        color: #888;
        font-size: 0.9rem;
    }

    .vaccine-actions {
        display: flex;
        gap: 0.5rem;
        justify-content: flex-end;
        margin-top: auto;
        padding-top: 1rem;
    }

    .edit-btn {
        background: #daa520;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.9rem;
        transition: background 0.2s ease;
    }

    .edit-btn:hover {
        background: #b8860b;
    }

    .delete-btn {
        background: #dc3545;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.9rem;
        transition: background 0.2s ease;
    }

    .delete-btn:hover {
        background: #c82333;
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

    .vaccine-form {
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
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
    .form-group textarea {
        padding: 0.75rem;
        border: 2px solid #f3e8a6;
        border-radius: 8px;
        font-size: 0.95rem;
        font-family: inherit;
    }

    .form-group input:focus,
    .form-group textarea:focus {
        outline: none;
        border-color: #daa520;
    }

    .form-group textarea {
        resize: vertical;
        min-height: 100px;
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
        transition: background 0.2s ease;
    }

    .cancel-btn:hover {
        background: #5a6268;
    }

    .submit-btn {
        background: linear-gradient(135deg, #daa520 0%, #b8860b 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .submit-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(184, 134, 11, 0.3);
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

    @media (max-width: 768px) {
        .vaccines-header {
            flex-direction: column;
            gap: 1rem;
        }

        .header-actions {
            width: 100%;
            flex-direction: column;
        }

        .search-input {
            min-width: 100%;
        }

        .vaccines-grid {
            grid-template-columns: 1fr;
        }

        .vaccine-actions {
            justify-content: center;
        }
    }
</style>