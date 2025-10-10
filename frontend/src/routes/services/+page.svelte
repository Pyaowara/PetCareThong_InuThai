<script lang="ts">
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { isAuthenticated, user, authService } from '$lib/auth';
    import { serviceApi } from '$lib/apiServices';

    interface Service {
        id: number;
        title: string;
        description?: string;
    }

    let services: Service[] = [];
    let isLoading = true;
    let error = '';
    let searchQuery = '';
    let showCreateModal = false;
    let editingService: Service | null = null;

    // Form data
    let serviceForm = {
        title: '',
        description: ''
    };

    $: filteredService= services.filter(service =>
        service.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (service.description && service.description.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    onMount(async () => {
        if (!$isAuthenticated) {
            goto('/login');
            return;
        }
        
        await loadServices();
    });

    async function loadServices() {
        try {
            isLoading = true;
            services = await serviceApi.getServices();
            error = '';
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to load services';
        } finally {
            isLoading = false;
        }
    }

    async function createService() {
        if (!serviceForm.title.trim()) {
            error = 'Service title is required';
            return;
        }

        try {
            await serviceApi.createService(serviceForm);
            await loadServices();
            resetForm();
            showCreateModal = false;
        } catch (err) {
            error = err instanceof Error ? `Failed to create service: ${err.message}` : `Failed to create service: ${JSON.stringify(err)}`;
        }
    }

    async function updateService() {
        if (!editingService || !serviceForm.title.trim()) {
            error = 'Vaccine name is required';
            return;
        }

        try {
            await serviceApi.updateService(editingService.id, serviceForm);
            await loadServices();
            resetForm();
            editingService = null;
        } catch (err) {
            error = err instanceof Error ? `Failed to update service: ${err.message}` : `Failed to update service: ${JSON.stringify(err)}`;
        }
    }

    async function deleteService(service: Service) {
        if (!confirm(`Are you sure you want to delete "${service.title}"? This action cannot be undone.`)) {
            return;
        }

        try {
            await serviceApi.deleteService(service.id);
            await loadServices();
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to delete vaccine';
        }
    }

    function startEdit(service: Service) {
        editingService = service;
        serviceForm = {
            title: service.title,
            description: service.description || ''
        };
    }

    function resetForm() {
        serviceForm = { title: '', description: '' };
        editingService = null;
        error = '';
    }

    function canManageServices(): boolean {
        return $user?.role === 'staff';
    }

    // function formatDate(dateString: string): string {
    //     return new Date(dateString).toLocaleDateString();
    // }
</script>

<svelte:head>
    <title>Service Management - PetCare</title>
</svelte:head>

<div class="services-container">
    <div class="services-header">
        <h1>Service Management</h1>
        
        <div class="header-actions">
            <div class="search-container">
                <input
                    type="text"
                    placeholder="Search service..."
                    bind:value={searchQuery}
                    class="search-input"
                />
            </div>
            
            {#if canManageServices()}
                <button class="create-btn" on:click={() => showCreateModal = true}>
                    Add New Service
                </button>
            {/if}
        </div>
    </div>

    {#if error && !showCreateModal && !editingService}
        <div class="error-message">{error}</div>
    {/if}

    {#if isLoading}
        <div class="loading">Loading services...</div>
    {:else if filteredService.length === 0}
        <div class="no-data">
            {searchQuery ? 'No services found matching your search.' : 'No services available yet.'}
        </div>
    {:else}
        <div class="services-grid">
            {#each filteredService as service (service.id)}
                <div class="service-card">
                    <div class="service-info">
                        <h3>{service.title}</h3>
                        {#if service.description}
                            <p class="service-description">{service.description}</p>
                        {/if}
                    </div>
                    
                    {#if canManageServices() && !['getVaccine', 'Others', 'Neutering/Spaying'].includes(service.title)}
                        <div class="service-actions">
                            <button class="edit-btn" on:click={() => startEdit(service)}>
                                Edit
                            </button>
                            <button class="delete-btn" on:click={() => deleteService(service)}>
                                Delete
                            </button>
                        </div>

                    {/if}
                </div>
            {/each}
        </div>
    {/if}

    <!-- Create/Edit service Modal -->
    {#if showCreateModal || editingService}
        <div class="modal-overlay" role="dialog" tabindex="-1" on:click={() => { showCreateModal = false; resetForm(); }} on:keydown={(e) => e.key === 'Escape' && (showCreateModal = false, resetForm())}>
            <div class="modal-content" on:click|stopPropagation on:keydown|stopPropagation>
                <h2>{editingService ? 'Edit service' : 'Add New service'}</h2>
                
                <form on:submit|preventDefault={editingService ? updateService : createService} class="service-form">
                    <div class="form-group">
                        <label for="serviceName">Service Name *</label>
                        <input
                            type="text"
                            id="serviceName"
                            bind:value={serviceForm.title}
                            placeholder="Input service name..."
                            required
                        />
                    </div>
                    
                    <div class="form-group">
                        <label for="serviceDescription">Description</label>
                        <textarea
                            id="serviceDescription"
                            bind:value={serviceForm.description}
                            placeholder="Optional description of the service..."
                            rows="4"
                        ></textarea>
                    </div>
                    {#if error}
                        <div class="error-message">{error}</div>
                    {/if}
                    <div class="form-actions">
                        <button type="button" class="cancel-btn" on:click={resetForm}>
                            Cancel
                        </button>
                        <button type="submit" class="submit-btn">
                            {editingService ? 'Update service' : 'Add service'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    {/if}
</div>

<style>
    .services-container {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }

    .services-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        gap: 2rem;
    }

    .services-header h1 {
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

    .services-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
        gap: 1.5rem;
    }

    .service-card {
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

    .service-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(184, 134, 11, 0.2);
    }

    .service-info h3 {
        margin: 0 0 0.75rem 0;
        color: #b8860b;
        font-size: 1.25rem;
        font-weight: 700;
    }

    .service-description {
        margin: 0 0 1rem 0;
        color: #666;
        line-height: 1.5;
    }

    

    .service-actions {
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

    .service-form {
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
        .services-header {
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

        .services-grid {
            grid-template-columns: 1fr;
        }

        .service-actions {
            justify-content: center;
        }
    }
</style>