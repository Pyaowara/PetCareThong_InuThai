<script lang="ts">
    import { onMount } from "svelte";
    import { goto } from "$app/navigation";
    import { isAuthenticated, user, authService } from "$lib/auth";
    import { vaccinationApi, vaccineApi, petApi, userApi } from "$lib/apiServices";

    interface Vaccination {
        id: number;
        pet: number;
        pet_name: string;
        pet_breed: string;
        vaccine: number;
        vaccine_name: string;
        date: string;
        remarks?: string;
        owner_name: string;
    }

    interface Pet {
        id: number;
        name: string;
        breed: string;
        gender?: string;
        age?: number;
        image_url?: string;
        owner_name: string;
    }

    interface Vaccine {
        id: number;
        name: string;
        description?: string;
    }

    interface User {
        id: number;
        email: string;
        full_name: string;
        role: string;
    }

    let vaccinations: Vaccination[] = [];
    let pets: Pet[] = [];
    let allPets: Pet[] = []; // Store all pets for filtering
    let vaccines: Vaccine[] = [];
    let users: User[] = [];
    let isLoading = true;
    let error = "";
    let dateFilter = "";
    let petFilter = "";
    let vaccineFilter = "";
    let userFilter = "";
    let showCreateModal = false;

    // Form data
    let vaccinationForm = {
        pet: null as number | null,
        vaccine: null as number | null,
        date: "",
        remarks: "",
    };

    // Reactive statement to filter pets based on selected user
    $: {
        if (userFilter && allPets.length > 0) {
            const selectedUser = users.find(u => u.full_name === userFilter);
            if (selectedUser) {
                pets = allPets.filter(pet => pet.owner_name === selectedUser.full_name);
                // Reset pet filter when user changes
                petFilter = "";
            }
        } else {
            pets = allPets;
        }
    }

    // Reactive statement to reload data when filters change
    $: {
        if (allPets.length > 0 && vaccines.length > 0) {
            loadVaccinations();
        }
    }

    // Watch for changes in filter values and automatically reload data
    $: dateFilter, petFilter, vaccineFilter, userFilter, handleFilterChange();

    function handleFilterChange() {
        // Debounce the filtering to avoid too many API calls
        if (allPets.length > 0 && vaccines.length > 0) {
            clearTimeout(filterTimeout);
            filterTimeout = setTimeout(() => {
                loadVaccinations();
            }, 300);
        }
    }

    let filterTimeout: ReturnType<typeof setTimeout>;

    onMount(async () => {
        if (!$isAuthenticated) {
            goto("/login");
            return;
        }

        const loadTasks = [loadPets(), loadVaccines()];
        
        // Only load users if user is staff or vet
        if ($user?.role === "staff" || $user?.role === "vet") {
            loadTasks.push(loadUsers());
        }

        await Promise.all(loadTasks);
        await loadVaccinations();
    });

    async function loadVaccinations() {
        try {
            isLoading = true;
            
            // Build filters object
            const filters: any = {};
            
            // Convert user name filter to user ID (for owner_id filter)
            if (userFilter) {
                const selectedUser = users.find(user => user.full_name === userFilter);
                if (selectedUser) {
                    filters.owner_id = selectedUser.id;
                }
            }
            
            // Convert pet name filter to pet ID
            if (petFilter) {
                const selectedPet = pets.find(pet => pet.name === petFilter);
                if (selectedPet) {
                    filters.pet_id = selectedPet.id;
                }
            }
            
            // Convert vaccine name filter to vaccine ID
            if (vaccineFilter) {
                const selectedVaccine = vaccines.find(vaccine => vaccine.name === vaccineFilter);
                if (selectedVaccine) {
                    filters.vaccine_id = selectedVaccine.id;
                }
            }
            
            if (dateFilter) {
                filters.date = dateFilter;
            }
            
            // Get vaccinations with full backend filtering
            vaccinations = await vaccinationApi.getVaccinations(filters);

            error = "";
        } catch (err) {
            error =
                err instanceof Error
                    ? err.message
                    : "Failed to load vaccination records";
        } finally {
            isLoading = false;
        }
    }

    async function loadPets() {
        try {
            allPets = await petApi.getPets();
            pets = allPets; // Initially show all pets
        } catch (err) {
            console.error("Failed to load pets:", err);
        }
    }

    async function loadVaccines() {
        try {
            vaccines = await vaccineApi.getVaccines();
        } catch (err) {
            console.error("Failed to load vaccines:", err);
        }
    }

    async function loadUsers() {
        try {
            users = await userApi.getUsersByRole("client");
        } catch (err) {
            console.error("Failed to load users:", err);
        }
    }

    async function createVaccination() {
        if (
            !vaccinationForm.pet ||
            !vaccinationForm.vaccine ||
            !vaccinationForm.date
        ) {
            error = "Pet, vaccine, and date are required";
            return;
        }

        try {
            await vaccinationApi.createVaccination(vaccinationForm);
            await loadVaccinations();
            resetForm();
            showCreateModal = false;
        } catch (err) {
            error =
                err instanceof Error
                    ? err.message
                    : "Failed to create vaccination record";
        }
    }

    async function deleteVaccination(vaccination: Vaccination) {
        if (
            !confirm(
                `Are you sure you want to delete this vaccination record for ${vaccination.pet_name}?`,
            )
        ) {
            return;
        }

        try {
            await vaccinationApi.deleteVaccination(vaccination.id);
            await loadVaccinations();
        } catch (err) {
            error =
                err instanceof Error
                    ? err.message
                    : "Failed to delete vaccination record";
        }
    }

    function resetForm() {
        vaccinationForm = { pet: null, vaccine: null, date: "", remarks: "" };
        error = "";
    }

    function clearFilters() {
        clearTimeout(filterTimeout);
        dateFilter = "";
        petFilter = "";
        vaccineFilter = "";
        userFilter = "";
        loadVaccinations(); // Reload data without filters
    }

    function canCreateVaccinations(): boolean {
        return $user?.role === "staff" || $user?.role === "vet";
    }

    function canDeleteVaccination(): boolean {
        return $user?.role === "staff" || $user?.role === "vet";
    }

    function formatDate(dateString: string): string {
        return new Date(dateString).toLocaleDateString();
    }

    function getTodayDate(): string {
        return new Date().toISOString().split("T")[0];
    }

    // Set default date to today when modal opens
    $: if (showCreateModal && !vaccinationForm.date) {
        vaccinationForm.date = getTodayDate();
    }
</script>

<svelte:head>
    <title>Vaccination Records - PetCare</title>
</svelte:head>

<div class="vaccinations-container">
    <div class="vaccinations-header">
        <h1>Vaccination Records</h1>

        <div class="header-actions">
            {#if canCreateVaccinations()}
                <button
                    class="create-btn"
                    on:click={() => (showCreateModal = true)}
                >
                    Add Vaccination Record
                </button>
            {/if}
        </div>
    </div>

    <!-- Filters -->
    <div class="filters-section">
        <div class="filters-row">

            {#if $user?.role === "staff" || $user?.role === "vet"}
                <div class="filter-group">
                    <label for="userFilter">Owner</label>
                    <select
                        id="userFilter"
                        bind:value={userFilter}
                        class="filter-select"
                    >
                        <option value="">All Owners</option>
                        {#each users as user (user.id)}
                            <option value={user.full_name}>{user.full_name}</option>
                        {/each}
                    </select>
                </div>
            {/if}

            <div class="filter-group">
                <label for="petFilter">Pet</label>
                <select
                    id="petFilter"
                    bind:value={petFilter}
                    class="filter-select"
                >
                    <option value="">All Pets</option>
                    {#each pets as pet (pet.id)}
                        <option value={pet.name}
                            >{pet.name}</option
                        >
                    {/each}
                </select>
            </div>

            <div class="filter-group">
                <label for="vaccineFilter">Vaccine</label>
                <select
                    id="vaccineFilter"
                    bind:value={vaccineFilter}
                    class="filter-select"
                >
                    <option value="">All Vaccines</option>
                    {#each vaccines as vaccine (vaccine.id)}
                        <option value={vaccine.name}>{vaccine.name}</option>
                    {/each}
                </select>
            </div>

            <div class="filter-group">
                <label for="dateFilter">Date</label>
                <input
                    type="date"
                    id="dateFilter"
                    bind:value={dateFilter}
                    class="filter-input"
                />
            </div>

            <div class="filter-group">
                <button class="clear-filters-btn" on:click={clearFilters}>
                    Clear Filters
                </button>
            </div>
        </div>
    </div>

    {#if error}
        <div class="error-message">{error}</div>
    {/if}

    {#if isLoading}
        <div class="loading">Loading vaccination records...</div>
    {:else if vaccinations.length === 0}
        <div class="no-data">
            {dateFilter || petFilter || vaccineFilter
                ? "No vaccination records found matching your filters."
                : "No vaccination records available yet."}
        </div>
    {:else}
        <div class="vaccinations-table-container">
            <table class="vaccinations-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Breed</th>
                        <th>Vaccine</th>
                        <th>Date</th>
                        <th>Remarks</th>
                        <th>Owner</th>
                        {#if canDeleteVaccination()}
                            <th>Actions</th>
                        {/if}
                    </tr>
                </thead>
                <tbody>
                    {#each vaccinations as vaccination (vaccination.id)}
                        <tr>
                            <td>
                                <strong>{vaccination.pet_name}</strong>
                            </td>
                            <td>{vaccination.pet_breed}</td>
                            <td>{vaccination.vaccine_name}</td>
                            <td>{formatDate(vaccination.date)}</td>
                            <td>{vaccination.remarks || "-"}</td>
                            <td>{vaccination.owner_name || "Unknown"}</td>
                            {#if canDeleteVaccination()}
                                <td>
                                    <button
                                        class="delete-btn"
                                        on:click={() =>
                                            deleteVaccination(vaccination)}
                                    >
                                        Delete
                                    </button>
                                </td>
                            {/if}
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    {/if}

    <!-- Create Vaccination Modal -->
    {#if showCreateModal}
        <div
            class="modal-overlay"
            role="dialog"
            tabindex="-1"
            on:click={() => {
                showCreateModal = false;
                resetForm();
            }}
            on:keydown={(e) =>
                e.key === "Escape" && ((showCreateModal = false), resetForm())}
        >
            <div
                class="modal-content"
                on:click|stopPropagation
                on:keydown|stopPropagation
            >
                <h2>Add Vaccination Record</h2>

                <form
                    on:submit|preventDefault={createVaccination}
                    class="vaccination-form"
                >
                    <div class="form-group">
                        <label for="formPet">Pet *</label>
                        <select
                            id="formPet"
                            bind:value={vaccinationForm.pet}
                            required
                        >
                            <option value={null}>Select a pet</option>
                            {#each pets as pet (pet.id)}
                                <option value={pet.id}>
                                    {pet.name} ({pet.breed}) - {pet.owner_name}
                                </option>
                            {/each}
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="formVaccine">Vaccine *</label>
                        <select
                            id="formVaccine"
                            bind:value={vaccinationForm.vaccine}
                            required
                        >
                            <option value={null}>Select a vaccine</option>
                            {#each vaccines as vaccine (vaccine.id)}
                                <option value={vaccine.id}
                                    >{vaccine.name}</option
                                >
                            {/each}
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="formDate">Vaccination Date *</label>
                        <input
                            type="date"
                            id="formDate"
                            bind:value={vaccinationForm.date}
                            max={getTodayDate()}
                            required
                        />
                    </div>

                    <div class="form-group">
                        <label for="formRemarks">Remarks</label>
                        <textarea
                            id="formRemarks"
                            bind:value={vaccinationForm.remarks}
                            placeholder="Optional remarks about the vaccination..."
                            rows="3"
                        ></textarea>
                    </div>

                    <div class="form-actions">
                        <button
                            type="button"
                            class="cancel-btn"
                            on:click={() => {
                                showCreateModal = false;
                                resetForm();
                            }}
                        >
                            Cancel
                        </button>
                        <button type="submit" class="submit-btn">
                            Add Record
                        </button>
                    </div>
                </form>
            </div>
        </div>
    {/if}
</div>

<style>
    .vaccinations-container {
        padding: 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }

    .vaccinations-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
    }

    .vaccinations-header h1 {
        margin: 0;
        color: #b8860b;
        font-size: 2rem;
    }

    .create-btn {
        background: linear-gradient(135deg, #daa520 0%, #b8860b 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        transition:
            transform 0.2s ease,
            box-shadow 0.2s ease;
    }

    .create-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(184, 134, 11, 0.3);
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
        grid-template-columns: 2fr 1.5fr 1.5fr 1.5fr 1fr auto;
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

    .vaccinations-table-container {
        background: white;
        border-radius: 12px;
        border: 1px solid #f3e8a6;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(184, 134, 11, 0.1);
    }

    .vaccinations-table {
        width: 100%;
        border-collapse: collapse;
    }

    .vaccinations-table th {
        background: #f8f6f0;
        color: #b8860b;
        font-weight: 700;
        padding: 1rem;
        text-align: left;
        border-bottom: 2px solid #f3e8a6;
    }

    .vaccinations-table td {
        padding: 1rem;
        border-bottom: 1px solid #f3e8a6;
        vertical-align: top;
    }

    .vaccinations-table tr:hover {
        background: #fffdf5;
    }

    .pet-species {
        color: #666;
        font-size: 0.9rem;
        font-style: italic;
    }

    .delete-btn {
        background: #dc3545;
        color: white;
        border: none;
        padding: 0.4rem 0.8rem;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.85rem;
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
        max-width: 600px;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
    }

    .modal-content h2 {
        margin: 0 0 1.5rem 0;
        color: #b8860b;
        font-size: 1.5rem;
    }

    .vaccination-form {
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
    .form-group select,
    .form-group textarea {
        padding: 0.75rem;
        border: 2px solid #f3e8a6;
        border-radius: 8px;
        font-size: 0.95rem;
        font-family: inherit;
    }

    .form-group input:focus,
    .form-group select:focus,
    .form-group textarea:focus {
        outline: none;
        border-color: #daa520;
    }

    .form-group textarea {
        resize: vertical;
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
            gap: 1rem;
        }

        .vaccinations-table-container {
            overflow-x: auto;
        }

        .vaccinations-table {
            min-width: 800px;
        }
    }

    @media (max-width: 768px) {
        .vaccinations-header {
            flex-direction: column;
            gap: 1rem;
        }

        .filters-row {
            grid-template-columns: 1fr;
        }
    }
</style>
