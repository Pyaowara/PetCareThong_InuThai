<script lang="ts">
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import { isAuthenticated, user, authService } from '$lib/auth';
    import { petApi, vaccinationApi, vaccineApi, appointmentApi } from '$lib/apiServices';

    interface Pet {
        id: number;
        user: number;
        name: string;
        gender: string;
        breed: string;
        color: string;
        allergic?: string;
        marks?: string;
        chronic_conditions?: string;
        neutered_status: boolean;
        birth_date: string;
        image_url?: string;
        age: number;
        vaccinations?: Vaccination[];
        total_vaccinations?: number;
        appointments?: Appointment[];
        total_appointments?: number;
    }

    interface Vaccination {
        id: number;
        vaccine_name: string;
        vaccine_id: number;
        date: string;
        remarks?: string;
    }

    interface Appointment {
        id: number;
        date: string;
        purpose: string;
        status: string;
        pet_name: string;
        owner_name: string;
        owner_email: string;
        assigned_vet?: string;
        pet_image_url?: string;
        pet_breed: string;
        pet_gender: string;
        pet_age?: number;
    }

    interface Vaccine {
        id: number;
        name: string;
        description?: string;
    }

    let pet: Pet | null = null;
    let vaccines: Vaccine[] = [];
    let isLoading = true;
    let error = '';
    let showAddVaccination = false;
    let isEditing = false;

    // Edit form data
    let editData = {
        name: '',
        breed: '',
        color: '',
        gender: 'Male',
        birth_date: '',
        allergic: '',
        marks: '',
        chronic_conditions: '',
        neutered_status: false,
        image: null as File | null
    };

    // Vaccination form data
    let newVaccination = {
        vaccine_id: null as number | null,
        date: '',
        remarks: ''
    };

    $: petId = parseInt($page.params.id || '0');

    onMount(async () => {
        if (!$isAuthenticated) {
            goto('/login');
            return;
        }
        
        await loadPetDetails();
        await loadVaccines();
    });

    async function loadPetDetails() {
        try {
            isLoading = true;
            pet = await petApi.getPetDetail(petId);
            
            // Initialize edit form with current data
            if (pet) {
                editData = {
                    name: pet.name,
                    breed: pet.breed,
                    color: pet.color,
                    gender: pet.gender,
                    birth_date: pet.birth_date,
                    allergic: pet.allergic || '',
                    marks: pet.marks || '',
                    chronic_conditions: pet.chronic_conditions || '',
                    neutered_status: pet.neutered_status,
                    image: null
                };
            }
            
            error = '';
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to load pet details';
        } finally {
            isLoading = false;
        }
    }

    async function loadVaccines() {
        try {
            vaccines = await vaccineApi.getVaccines();
        } catch (err) {
            console.error('Failed to load vaccines:', err);
        }
    }

    async function updatePet() {
        if (!pet) return;
        
        try {
            const formData = new FormData();
            formData.append('name', editData.name);
            formData.append('breed', editData.breed);
            formData.append('color', editData.color);
            formData.append('gender', editData.gender);
            formData.append('birth_date', editData.birth_date);
            formData.append('neutered_status', editData.neutered_status.toString());
            if (editData.allergic) formData.append('allergic', editData.allergic);
            if (editData.marks) formData.append('marks', editData.marks);
            if (editData.chronic_conditions) formData.append('chronic_conditions', editData.chronic_conditions);
            if (editData.image) formData.append('image', editData.image);

            await petApi.updatePet(pet.id, formData);
            await loadPetDetails();
            isEditing = false;
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to update pet';
        }
    }

    async function addVaccination() {
        if (!pet || !newVaccination.vaccine_id || !newVaccination.date) return;
        
        try {
            await vaccinationApi.createVaccination({
                pet: pet.id,
                vaccine: newVaccination.vaccine_id,
                date: newVaccination.date,
                remarks: newVaccination.remarks
            });
            
            // Reset form
            newVaccination = { vaccine_id: null, date: '', remarks: '' };
            showAddVaccination = false;
            
            // Reload pet details to get updated vaccinations
            await loadPetDetails();
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to add vaccination';
        }
    }

    async function deletePet() {
        if (!pet || !confirm('Are you sure you want to delete this pet? This action cannot be undone.')) return;
        
        try {
            await petApi.deletePet(pet.id);
            goto('/pets');
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to delete pet';
        }
    }

    function handleImageChange(event: Event) {
        const target = event.target as HTMLInputElement;
        if (target.files && target.files[0]) {
            editData.image = target.files[0];
        }
    }

    function canEdit(): boolean {
        if (!$user || !pet) return false;
        return $user.role === 'staff' || pet.user === $user.id;
    }

    function canAddVaccination(): boolean {
        return $user?.role === 'staff' || $user?.role === 'vet';
    }

    function formatDate(dateString: string): string {
        return new Date(dateString).toLocaleDateString();
    }

    function formatDateTime(dateString: string): string {
        return new Date(dateString).toLocaleString();
    }

    function getStatusColor(status: string): string {
        switch (status) {
            case 'booked': return '#ffc107';
            case 'confirmed': return '#17a2b8';
            case 'completed': return '#28a745';
            case 'rejected': return '#dc3545';
            case 'cancelled': return '#6c757d';
            default: return '#6c757d';
        }
    }

    function getStatusText(status: string): string {
        return status.charAt(0).toUpperCase() + status.slice(1);
    }

    function viewAppointment(appointmentId: number) {
        goto(`/appointments/${appointmentId}`);
    }
    function getTodayDate(): string {
        return new Date().toISOString().split("T")[0];
    }
</script>

<svelte:head>
    <title>{pet ? `${pet.name} - Pet Details` : 'Pet Details'} - PetCare</title>
</svelte:head>

<div class="pet-detail-container">
    {#if error && !showAddVaccination && !isEditing}
        <div class="error-message">{error}</div>
    {/if}

    {#if isLoading}
        <div class="loading">Loading pet details...</div>
    {:else if !pet}
        <div class="no-data">Pet not found</div>
    {:else}
        <div class="pet-header">
            <button class="back-btn" on:click={() => goto('/pets')}>
                ← Back to Pets
            </button>
            
            <div class="header-actions">
                {#if canEdit()}
                    <button class="edit-btn" on:click={() => isEditing = true}>
                        Edit Pet
                    </button>
                    <button class="delete-btn" on:click={deletePet}>
                        Delete Pet
                    </button>
                {/if}
            </div>
        </div>

        <div class="pet-content">
            <div class="pet-main-info">
                <div class="pet-image-section">
                    {#if pet.image_url}
                        <img src={pet.image_url} alt={pet.name} class="pet-image" />
                    {:else}
                        <div class="pet-image-placeholder">🐾</div>
                    {/if}
                </div>

                <div class="pet-info-section">
                    <h1>{pet.name}</h1>
                    <div class="pet-details">
                        <div class="detail-item">
                            <strong>Breed:</strong> {pet.breed}
                        </div>
                        <div class="detail-item">
                            <strong>Color:</strong> {pet.color}
                        </div>
                        <div class="detail-item">
                            <strong>Gender:</strong> {pet.gender}
                        </div>
                        <div class="detail-item">
                            <strong>Age:</strong> {pet.age} years old
                        </div>
                        <div class="detail-item">
                            <strong>Birth Date:</strong> {formatDate(pet.birth_date)}
                        </div>
                        <div class="detail-item">
                            <strong>Neutered/Spayed:</strong> {pet.neutered_status ? 'Yes' : 'No'}
                        </div>
                    </div>
                    
                    {#if pet.allergic || pet.marks || pet.chronic_conditions}
                        <div class="additional-info">
                            <h3>Additional Information</h3>
                            {#if pet.allergic}
                                <div class="info-item">
                                    <strong>Allergies:</strong> {pet.allergic}
                                </div>
                            {/if}
                            {#if pet.marks}
                                <div class="info-item">
                                    <strong>Distinctive Marks:</strong> {pet.marks}
                                </div>
                            {/if}
                            {#if pet.chronic_conditions}
                                <div class="info-item">
                                    <strong>Chronic Conditions:</strong> {pet.chronic_conditions}
                                </div>
                            {/if}
                        </div>
                    {/if}
                </div>
            </div>

            <div class="vaccination-section">
                <div class="section-header">
                    <h2>Vaccination History {pet.total_vaccinations ? `(${pet.total_vaccinations})` : ''}</h2>
                    {#if canAddVaccination()}
                        <button class="add-vaccination-btn" on:click={() => showAddVaccination = true}>
                            Add Vaccination
                        </button>
                    {/if}
                </div>

                {#if pet.vaccinations && pet.vaccinations.length > 0}
                    <div class="vaccinations-list">
                        {#each pet.vaccinations as vaccination (vaccination.id)}
                            <div class="vaccination-card">
                                <div class="vaccination-info">
                                    <h4>{vaccination.vaccine_name}</h4>
                                    <p class="vaccination-date">Date: {formatDate(vaccination.date)}</p>
                                    {#if vaccination.remarks}
                                        <p class="vaccination-notes">Remarks: {vaccination.remarks}</p>
                                    {/if}
                                </div>
                            </div>
                        {/each}
                    </div>
                {:else}
                    <div class="no-vaccinations">
                        No vaccination records yet.
                    </div>
                {/if}
            </div>

            <div class="appointments-section">
                <div class="section-header">
                    <h2>Appointment History {pet.total_appointments ? `(${pet.total_appointments})` : ''}</h2>
                    <button class="book-appointment-btn" on:click={() => goto('/appointments')}>
                        Book New Appointment
                    </button>
                </div>

                {#if pet.appointments && pet.appointments.length > 0}
                    <div class="appointments-list">
                        {#each pet.appointments as appointment (appointment.id)}
                            <div class="appointment-card" on:click={() => viewAppointment(appointment.id)} role="button" tabindex="0" on:keydown={(e) => e.key === 'Enter' && viewAppointment(appointment.id)}>
                                <div class="appointment-header">
                                    <div class="appointment-status" style="background-color: {getStatusColor(appointment.status)}">
                                        {getStatusText(appointment.status)}
                                    </div>
                                    <div class="appointment-date">
                                        {formatDateTime(appointment.date)}
                                    </div>
                                </div>
                                <div class="appointment-content">
                                    <h4 class="appointment-purpose">{appointment.purpose}</h4>
                                    {#if appointment.assigned_vet}
                                        <p class="appointment-vet">Assigned Vet: {appointment.assigned_vet}</p>
                                    {/if}
                                </div>
                                <div class="appointment-footer">
                                    <span class="view-details">Click to view details →</span>
                                </div>
                            </div>
                        {/each}
                    </div>
                {:else}
                    <div class="no-appointments">
                        No appointment records yet.
                    </div>
                {/if}
            </div>
        </div>
    {/if}

    <!-- Edit Pet Modal -->
    {#if isEditing && pet}
        <div class="modal-overlay" role="dialog" tabindex="-1" on:click={() => isEditing = false} on:keydown={(e) => e.key === 'Escape' && (isEditing = false)}>
            <div class="modal-content" role="document" tabindex="0" on:click|stopPropagation on:keydown|stopPropagation>
                <h2>Edit Pet Information</h2>
                <form on:submit|preventDefault={updatePet} class="edit-form">
                    <div class="form-group">
                        <label for="editName">Pet Name *</label>
                        <input type="text" id="editName" bind:value={editData.name} required />
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="editBreed">Breed *</label>
                            <input type="text" id="editBreed" bind:value={editData.breed} required />
                        </div>
                        <div class="form-group">
                            <label for="editColor">Color *</label>
                            <input type="text" id="editColor" bind:value={editData.color} required />
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="editGender">Gender</label>
                            <select id="editGender" bind:value={editData.gender}>
                                <option value="Male">Male</option>
                                <option value="Female">Female</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="editBirthDate">Birth Date *</label>
                            <input type="date" id="editBirthDate" bind:value={editData.birth_date} required />
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="editAllergic">Allergies</label>
                        <textarea id="editAllergic" bind:value={editData.allergic}></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="editMarks">Distinctive Marks</label>
                        <textarea id="editMarks" bind:value={editData.marks}></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="editChronic">Chronic Conditions</label>
                        <textarea id="editChronic" bind:value={editData.chronic_conditions}></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" bind:checked={editData.neutered_status} />
                            Neutered/Spayed
                        </label>
                    </div>
                    
                    <div class="form-group">
                        <label for="editImage">Update Photo</label>
                        <input type="file" id="editImage" accept="image/*" on:change={handleImageChange} />
                    </div>
                    {#if error}
                        <div class="error-message">{error}</div>
                    {/if}
                    <div class="form-actions">
                        <button type="button" class="cancel-btn" on:click={() => isEditing = false}>
                            Cancel
                        </button>
                        <button type="submit" class="submit-btn">Update Pet</button>
                    </div>
                </form>
            </div>
        </div>
    {/if}

    <!-- Add Vaccination Modal -->
    {#if showAddVaccination}
        <div class="modal-overlay" role="dialog" tabindex="-1" on:click={() => showAddVaccination = false} on:keydown={(e) => e.key === 'Escape' && (showAddVaccination = false)}>
            <div class="modal-content" role="document" tabindex="0" on:click|stopPropagation on:keydown|stopPropagation>
                <h2>Add Vaccination Record</h2>
                <form on:submit|preventDefault={addVaccination} class="vaccination-form">
                    <div class="form-group">
                        <label for="vaccine">Vaccine *</label>
                        <select id="vaccine" bind:value={newVaccination.vaccine_id} required>
                            <option value={null}>Select a vaccine</option>
                            {#each vaccines as vaccine (vaccine.id)}
                                <option value={vaccine.id}>{vaccine.name}</option>
                            {/each}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="date">Vaccination Date *</label>
                        <input type="date" id="date" bind:value={newVaccination.date} max={getTodayDate()} required />
                    </div>
                    
                    <div class="form-group">
                        <label for="remarks">Remarks</label>
                        <textarea id="remarks" bind:value={newVaccination.remarks} rows="3"></textarea>
                    </div>
                    {#if error}
                        <div class="error-message">{error}</div>
                    {/if}
                    <div class="form-actions">
                        <button type="button" class="cancel-btn" on:click={() => showAddVaccination = false}>
                            Cancel
                        </button>
                        <button type="submit" class="submit-btn">Add Vaccination</button>
                    </div>
                </form>
            </div>
        </div>
    {/if}
</div>

<style>
    .pet-detail-container {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }

    .pet-header {
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
    }

    .back-btn:hover {
        background: #f3e8a6;
    }

    .header-actions {
        display: flex;
        gap: 0.5rem;
    }

    .edit-btn {
        background: #daa520;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        cursor: pointer;
    }

    .delete-btn {
        background: #dc3545;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        cursor: pointer;
    }

    .pet-content {
        background: white;
        border-radius: 12px;
        border: 1px solid #f3e8a6;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(184, 134, 11, 0.1);
    }

    .pet-main-info {
        display: grid;
        grid-template-columns: 300px 1fr;
        gap: 2rem;
        padding: 2rem;
    }

    .pet-image {
        width: 100%;
        height: 300px;
        object-fit: cover;
        border-radius: 8px;
    }

    .pet-image-placeholder {
        width: 100%;
        height: 300px;
        background: #f8f6f0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 4rem;
        border-radius: 8px;
    }

    .pet-info-section h1 {
        margin: 0 0 1.5rem 0;
        color: #b8860b;
        font-size: 2.5rem;
    }

    .pet-details {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
    }

    .detail-item {
        background: #fff8e1;
        padding: 1rem;
        border-radius: 8px;
    }

    .detail-item strong {
        color: #b8860b;
    }

    .additional-info {
        margin-top: 2rem;
        padding: 1.5rem;
        background: #f8f6f0;
        border-radius: 8px;
        border-left: 4px solid #daa520;
    }

    .additional-info h3 {
        margin: 0 0 1rem 0;
        color: #b8860b;
        font-size: 1.2rem;
    }

    .info-item {
        margin-bottom: 1rem;
    }

    .info-item:last-child {
        margin-bottom: 0;
    }

    .info-item strong {
        color: #b8860b;
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

    .vaccination-section {
        padding: 2rem;
        border-top: 1px solid #f3e8a6;
    }

    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
    }

    .section-header h2 {
        margin: 0;
        color: #b8860b;
        font-size: 1.5rem;
    }

    .add-vaccination-btn, .book-appointment-btn {
        background: linear-gradient(135deg, #daa520 0%, #b8860b 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
    }

    .vaccinations-list {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 1rem;
    }

    .vaccination-card {
        background: #fff8e1;
        border-radius: 8px;
        padding: 1.5rem;
        border-left: 4px solid #daa520;
    }

    .vaccination-card h4 {
        margin: 0 0 0.5rem 0;
        color: #b8860b;
        font-size: 1.1rem;
    }

    .vaccination-date {
        margin: 0 0 0.5rem 0;
        color: #666;
        font-weight: 600;
    }

    .vaccination-notes {
        margin: 0;
        color: #666;
        font-style: italic;
    }

    .no-vaccinations, .no-appointments {
        text-align: center;
        padding: 2rem;
        color: #666;
        font-style: italic;
    }

    .appointments-section {
        padding: 2rem;
        border-top: 1px solid #f3e8a6;
    }

    .appointments-list {
        display: grid;
        gap: 1rem;
    }

    .appointment-card {
        background: #fff;
        border: 2px solid #f3e8a6;
        border-radius: 12px;
        padding: 1.5rem;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(184, 134, 11, 0.1);
    }

    .appointment-card:hover {
        border-color: #daa520;
        box-shadow: 0 4px 8px rgba(184, 134, 11, 0.2);
        transform: translateY(-2px);
    }

    .appointment-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }

    .appointment-status {
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: uppercase;
    }

    .appointment-date {
        color: #666;
        font-weight: 600;
        font-size: 0.95rem;
    }

    .appointment-content {
        margin-bottom: 1rem;
    }

    .appointment-purpose {
        margin: 0 0 0.5rem 0;
        color: #333;
        font-size: 1.1rem;
        font-weight: 600;
    }

    .appointment-vet {
        margin: 0;
        color: #b8860b;
        font-weight: 500;
    }

    .appointment-footer {
        text-align: right;
    }

    .view-details {
        color: #daa520;
        font-size: 0.9rem;
        font-weight: 500;
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

    .edit-form, .vaccination-form {
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

    .form-group input, .form-group select, .form-group textarea {
        padding: 0.75rem;
        border: 2px solid #f3e8a6;
        border-radius: 8px;
        font-size: 0.95rem;
    }

    .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
        outline: none;
        border-color: #daa520;
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
        .pet-main-info {
            grid-template-columns: 1fr;
        }

        .pet-details {
            grid-template-columns: 1fr;
        }

        .form-row {
            grid-template-columns: 1fr;
        }

        .pet-header {
            flex-direction: column;
            gap: 1rem;
        }

        .appointment-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.5rem;
        }

        .appointment-date {
            font-size: 0.875rem;
        }

        .section-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 1rem;
        }

        .add-vaccination-btn, .book-appointment-btn {
            width: 100%;
        }
    }
</style>