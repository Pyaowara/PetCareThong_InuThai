<script lang="ts">
    import { onMount } from "svelte";
    import { goto } from "$app/navigation";
    import { isAuthenticated, user, authService } from "$lib/auth";
    import { appointmentApi, vaccineApi, petApi, userApi } from "$lib/apiServices";

    interface Appointment {
        id: number;
        pet_name: string;
        owner_name: string;
        owner_email: string;
        assigned_vet: string;
        purpose?: string;
        status: string;
        date: string;
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


    let appointments: Appointment[] = [];
    let pets: Pet[] = [];
    let users: User[] = [];
    let isLoading = true;
    let error = "";
    let searchQuery = "";
    let dateFilter = "";
    let petFilter = "";
    let statusFilter = "";
    let showCreateModal = false;
    // Form data
    let appointmentForm = {
        user: null as number | null,
        pet: null as number | null,
        date: "",
        remarks: "",
        purpose: "",
    };

    $: filteredAppointments = appointments.filter((appointment) => {
        const matchesSearch =
            !searchQuery ||
            appointment.pet_name
                .toLowerCase()
                .includes(searchQuery.toLowerCase()) ||
            appointment.owner_name
                .toLowerCase()
                .includes(searchQuery.toLowerCase()) ||
            (appointment.purpose &&
                appointment.purpose
                    .toLowerCase()
                    .includes(searchQuery.toLowerCase()));
        console.log(formatDate(appointment.date))
        console.log(dateFilter)
        const matchesDate = !dateFilter || formatDate(appointment.date) === dateFilter;
        const matchesPet =
            !petFilter || appointment.pet_name === petFilter;
        const matchesStatus =
            !statusFilter || appointment.status === statusFilter;

        return matchesSearch && matchesDate && matchesPet && matchesStatus;
    });
    
    $: availablePets = pets;
    $: availableUsers = user;
    onMount(async () => {
        if (!$isAuthenticated) {
            goto("/login");
            return;
        }

        await Promise.all([loadAppointments(), loadPets(), loadUsers()]);
    });

    async function loadAppointments() {
        try {
            isLoading = true;
            appointments = await appointmentApi.getAppointment();

            error = "";
        } catch (err) {
            error =
                err instanceof Error
                    ? err.message
                    : "Failed to load appointment records";
        } finally {
            isLoading = false;
        }
    }

    async function loadPets() {
        try {
            pets = await petApi.getPets();
        } catch (err) {
            console.error("Failed to load pets:", err);
        }
    }

    async function loadUsers() {
        try {
            users = await userApi.getClients();
        } catch (err) {
            console.error("Failed to load user:", err);
        }
    }


    async function createAppointment() {
        if (
            !appointmentForm.pet ||
            !appointmentForm.purpose ||
            !appointmentForm.date
        ) {
            error = "Pet, Purpose, and date are required";
            return;
        }

        try {
            await appointmentApi.bookAppointment(appointmentForm);
            await loadAppointments();
            resetForm();
            showCreateModal = false;
        } catch (err) {
            error =
                err instanceof Error
                    ? err.message
                    : "Failed to create appointment record";
        }
    }

    // async function deleteAppointment(appointment: Appointment) {
    //     if (
    //         !confirm(
    //             `Are you sure you want to delete this appointment record for ${appointment.pet_name}?`,
    //         )
    //     ) {
    //         return;
    //     }

    //     try {
    //         await appointmentApi.deleteAppointment(appointment.id);
    //         await loadAppointments();
    //     } catch (err) {
    //         error =
    //             err instanceof Error
    //                 ? err.message
    //                 : "Failed to delete appointment record";
    //     }
    // }

    function resetForm() {
        appointmentForm = { pet: null, user: null, purpose: "", date: "", remarks: "" };
        error = "";
    }

    function clearFilters() {
        searchQuery = "";
        dateFilter = "";
        petFilter = "";
        statusFilter = "";
    }

    function cancreateAppointments(): boolean {
        return $user?.role === "staff" || $user?.role === "client";
    }

    // function candeleteAppointment(): boolean {
    //     return $user?.role === "staff";
    // }

    function formatDate(dateString: string): string {
        const d = new Date(dateString);

        const day = d.getDate();
        const month = (d.getMonth() + 1).toString().padStart(2, "0");;
        const year = d.getFullYear().toString().padStart(2, "0");;

        return `${year}-${month}-${day}`;
        
    }
    function formatDatetime(dateString: string): string {
        
        return new Date(dateString).toISOString().replace("T", " ").split("Z")[0].slice(0, -7);

    }
    function getTodayDate(): string {
        return new Date().toISOString().split("T")[0];
    }

    // Set default date to today when modal opens
    $: if (showCreateModal && !appointmentForm.date) {
        appointmentForm.date = getTodayDate();
    }
</script>

<svelte:head>
    <title>Appointment Records - PetCare</title>
</svelte:head>

<div class="appointments-container">
    <div class="appointments-header">
        <h1>Appointment Records</h1>

        <div class="header-actions">
            {#if cancreateAppointments()}
                <button
                    class="create-btn"
                    on:click={() => (showCreateModal = true)}
                >
                    Add Appointment Record
                </button>
            {/if}
        </div>
    </div>

    <!-- Filters -->
    <div class="filters-section">
        <div class="filters-row">
            <div class="filter-group">
                <label for="searchFilter">Search</label>
                <input
                    type="text"
                    id="searchFilter"
                    placeholder="Search by purpose, pet name, status......."
                    bind:value={searchQuery}
                    class="filter-input"
                />
            </div>

            <div class="filter-group">
                <label for="petFilter">Pet</label>
                <select
                    id="petFilter"
                    bind:value={petFilter}
                    class="filter-select"
                >
                    <option value="">All Pets</option>
                    {#each availablePets as pet (pet.id)}
                        <option value={pet.name}
                            >{pet.name} ({pet.owner_name})</option
                        >
                    {/each}
                </select>
            </div>

            <div class="filter-group">
                <label for="statusFilter">All Status</label>
                <select
                    id="statusFilter"
                    bind:value={statusFilter}
                    class="filter-select"
                >
                    <option value="">All Status</option>
                        <option value='booked'>Booked</option>
                        <option value='confirmed'>Confirmed</option>
                        <option value='completed'>Completed</option>
                        <option value='rejected'>Rejected</option>
                        <option value='cancelled'>Cancelled</option>
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
        <div class="loading">Loading Appointement records...</div>
    {:else if filteredAppointments.length === 0}
        <div class="no-data">
            {searchQuery || dateFilter || petFilter || statusFilter
                ? "No Appointement records found matching your filters."
                : "No Appointement records available yet."}
        </div>
    {:else}
        <div class="appointments-table-container">
            <table class="appointments-table">
                <thead>
                    <tr>
                        <th>User</th>
                        <th>Purpose</th>
                        <th>Pet</th>
                        <th>Date</th>
                        <th>Status</th>
                        <th>Assigned Vet</th>
                        <th>Actions</th>
                        
                    </tr>
                </thead>
                <tbody>
                    {#each filteredAppointments as appointment (appointment.id)}
                        <tr>
                            <td>
                                <strong>{appointment.owner_name}</strong> ({appointment.owner_email})
                            </td>
                            <td>{appointment.purpose}</td>
                            <td>{appointment.pet_name}</td>
                            <td>{formatDatetime(appointment.date)}</td>
                            <td><span class="status-badge status-{appointment.status}">{appointment.status}</span></td>
                            <td>{appointment.assigned_vet || "Not Assigned now"}</td>
                                    

                            
                                <td>
                                    <!-- {#if candeleteAppointment()}
                                    <button
                                    class="delete-btn"
                                    on:click={() =>
                                            deleteAppointment(appointment)}
                                    >
                                    Delete
                                    </button>
                                    {/if} -->
                                <button
                                    class="detail-btn"
                                    on:click={() => goto(`/appointments/${appointment.id}`)}
                                >
                                    View
                                </button>
                                </td>
                            
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    {/if}

    <!-- Create Appointment Modal -->
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
                <h2>Add Appointment Record</h2>

                <form
                    on:submit|preventDefault={createAppointment}
                    class="appointment-form"
                >   
                    <div class="form-group">
                        <label for="formPurpose">Purpose</label>
                            <input type="text" id="formPurpose" bind:value={appointmentForm.purpose} required placeholder="Purpose about your appointment" />
                    </div>
                    {#if $user?.role === 'staff'}
                    <div class="form-group">
                        <label for="formOwner">Owner *</label>
                        <select
                            id="formOwner"
                            bind:value={appointmentForm.user}
                            required
                        >
                            <option value={null}>Select a user</option>
                            {#each users as user (user.id)}
                                <option value={user.id}
                                    >{user.full_name}</option
                                >
                            {/each}
                        </select>
                    </div>
                    {/if}
                    <div class="form-group">
                        <label for="formPet">Pet *</label>
                        <select
                            id="formPet"
                            bind:value={appointmentForm.pet}
                            required
                        >
                            <option value={null}>Select a pet</option>
                            {#each availablePets as pet (pet.id)}
                                <option value={pet.id}>
                                    {pet.name} {pet.owner_name}
                                </option>
                            {/each}
                        </select>
                    </div>


                    <div class="form-group">
                        <label for="formDate">Appointment Date *</label>
                        <input
                            type="datetime-local"
                            id="formDate"
                            bind:value={appointmentForm.date}
                            max={getTodayDate()}
                            required
                        />
                    </div>

                    <div class="form-group">
                        <label for="formRemarks">Remarks</label>
                        <textarea
                            id="formRemarks"
                            bind:value={appointmentForm.remarks}
                            placeholder="Optional remarks about the appointment..."
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
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .status-completed {
        background: #e8f5e8;
        color: #2d7d2d;
    }

    .status-confirmed {
        background: #e3f2fd;
        color: #1976d2;
    }

    .status-cancelled {
        background: #fff3e0;
        color: #e66909;
    }

    .status-booked {
        background: #fff3e0;
        color: #ebd126;
    }

    .status-rejected {
        background: #ffebee;
        color: #d32f2f;
    }
    .appointments-container {
        padding: 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }

    .appointments-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
    }

    .appointments-header h1 {
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
        grid-template-columns: 2fr 1.5fr 1.5fr 1fr auto;
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

    .appointments-table-container {
        background: white;
        border-radius: 12px;
        border: 1px solid #f3e8a6;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(184, 134, 11, 0.1);
    }

    .appointments-table {
        width: 100%;
        border-collapse: collapse;
    }

    .appointments-table th {
        background: #f8f6f0;
        color: #b8860b;
        font-weight: 700;
        padding: 1rem;
        text-align: left;
        border-bottom: 2px solid #f3e8a6;
    }

    .appointments-table td {
        padding: 1rem;
        border-bottom: 1px solid #f3e8a6;
        vertical-align: top;
    }

    .appointments-table tr:hover {
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
    .detail-btn {
        background: #1e3bce;
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

    .appointment-form {
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

        .appointments-table-container {
            overflow-x: auto;
        }

        .appointments-table {
            min-width: 800px;
        }
    }

    @media (max-width: 768px) {
        .appointments-header {
            flex-direction: column;
            gap: 1rem;
        }

        .filters-row {
            grid-template-columns: 1fr;
        }
    }
</style>
