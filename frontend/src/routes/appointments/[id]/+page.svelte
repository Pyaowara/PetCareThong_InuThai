<script lang="ts">
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import { isAuthenticated, user, authService } from '$lib/auth';
    import { appointmentApi, petApi, vaccinationApi, vaccineApi } from '$lib/apiServices';

    interface Appointment {
        id: number;
        user_name: string;
        purpose: string;
        pet: Pet;
        status: string;
        remarks?: string;
        assigned_vet?: string;
        vet_note?:string;
        date:string;
        created_at:string;
        updated_at:string;
        vaccinations?: Vaccination[];
        total_vaccinations?: number;
    }

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
    }

    interface Vaccination {
        id: number;
        vaccine_name: string;
        vaccine_id: number;
        date: string;
        remarks?: string;
    }

    interface Vaccine {
        id: number;
        name: string;
        description?: string;
    }
    let appointment: Appointment | null = null;
    // let pet: Pet | null = null;
    let vaccines: Vaccine[] = [];
    let isLoading = false;
    let error = '';
    let showAddVaccination = false;
    let isEditing = false;

    // Edit form data
    let editData = {
        id: 0,
        user: '',
        pet_form: '',
        purpose: '',
        remarks: null,
        date: '',
    };

    // Vaccination form data
    let newVaccination = {
        vaccine_id: null as number | null,
        date: '',
        remarks: ''
    };

    $: appointmentId = parseInt($page.params.id || '0');

    onMount(async () => {
        if (!$isAuthenticated) {
            goto('/login');
            return;
        }
        
        // await loadPetDetails();
        await loadAppointment();
        await loadVaccines();
    });
     async function loadAppointment() {
        try {
            isLoading = true;
            appointment = await appointmentApi.getAppointmentDetail(appointmentId);
            
            // Initialize edit form with current data
            // if (appointment) {
            //     editData = {
            //         id: appointment.id,
            //         user: appointment.user_name,
            //         pet_form: appointment.pet.name,
            //         purpose: appointment.purpose,
            //         remarks: appointment.remarks,
            //         date: appointment.date,
            //     };
            // }
            
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

    // async function updatePet() {
    //     if (!pet) return;
        
    //     try {
    //         const formData = new FormData();
    //         formData.append('name', editData.name);
    //         formData.append('breed', editData.breed);
    //         formData.append('color', editData.color);
    //         formData.append('gender', editData.gender);
    //         formData.append('birth_date', editData.birth_date);
    //         formData.append('neutered_status', editData.neutered_status.toString());
    //         if (editData.allergic) formData.append('allergic', editData.allergic);
    //         if (editData.marks) formData.append('marks', editData.marks);
    //         if (editData.chronic_conditions) formData.append('chronic_conditions', editData.chronic_conditions);
    //         if (editData.image) formData.append('image', editData.image);

    //         await petApi.updatePet(pet.id, formData);
    //         await loadPetDetails();
    //         isEditing = false;
    //     } catch (err) {
    //         error = err instanceof Error ? err.message : 'Failed to update pet';
    //     }
    // }

    // async function addVaccination() {
    //     if (!pet || !newVaccination.vaccine_id || !newVaccination.date) return;
        
    //     try {
    //         await vaccinationApi.createVaccination({
    //             pet: pet.id,
    //             vaccine: newVaccination.vaccine_id,
    //             date: newVaccination.date,
    //             remarks: newVaccination.remarks
    //         });
            
    //         // Reset form
    //         newVaccination = { vaccine_id: null, date: '', remarks: '' };
    //         showAddVaccination = false;
            
    //         // Reload pet details to get updated vaccinations
    //         await loadPetDetails();
    //     } catch (err) {
    //         error = err instanceof Error ? err.message : 'Failed to add vaccination';
    //     }
    // }

    // async function deletePet() {
    //     if (!pet || !confirm('Are you sure you want to delete this pet? This action cannot be undone.')) return;
        
    //     try {
    //         await petApi.deletePet(pet.id);
    //         goto('/pets');
    //     } catch (err) {
    //         error = err instanceof Error ? err.message : 'Failed to delete pet';
    //     }
    // }

    

    // function canEdit(): boolean {
    //     if (!$user || !pet) return false;
    //     return $user.role === 'staff' || pet.user === $user.id;
    // }
    function formatDatetime(dateString: string): string {
        
        return new Date(dateString).toISOString().replace("T", " ").split("Z")[0].slice(0, -7);

    }
    function canAddVaccination(): boolean {
        return $user?.role === 'staff' || $user?.role === 'vet';
    }

    function formatDate(dateString: string): string {
        return new Date(dateString).toLocaleDateString();
    }
</script>

<svelte:head>
    <title>{appointment ? `${appointment?.purpose} - Appointment Details` : 'Appointment Details'} - PetCare</title>
</svelte:head>

<div class="pet-detail-container">
    {#if error}
        <div class="error-message">{error}</div>
    {/if}

    {#if isLoading}
        <div class="loading">Loading Appointment details...</div>
    {:else if !appointment}
        <div class="no-data">Appointment not found</div>
    {:else}
        <div class="pet-header">
            <button class="back-btn" on:click={() => goto('/appointments')}>
                ← Back to Appointment
            </button>
            
            <div class="header-actions">
                <!-- {#if canEdit()}
                    <button class="edit-btn" on:click={() => isEditing = true}>
                        Edit Appointment
                    </button>
                    <button class="delete-btn" on:click={deletePet}>
                        Delete Pet
                    </button>
                {/if} -->
            </div>
        </div>

        <div class="pet-content">
            <div class="vaccination-section">
                <div class="pet-info-section">
                    <div class="section-header">
                        <h1>Appointment Information</h1>
                    </div>
                    <div class="additional-info">
                        <div class="info-item">
                            <h2><strong>Purpose:</strong> {appointment.purpose}</h2>
                        </div>
                        <div class="info-item">
                            <h2><strong>Owner name:</strong> {appointment.user_name}</h2>
                        </div>
                        <div class="info-item">
                            <h2><strong>Appointment time:</strong> {formatDatetime(appointment.date)}</h2>
                        </div>
                        <div class="info-item">
                            <h2><strong>Remarks:</strong> {appointment.remarks}</h2>
                        </div>
                        <div class="info-item">
                            <h2><strong>Status:</strong> {appointment.status}</h2>
                        </div>
                        <div class="info-item">
                            <h2><strong>Assigned Vet:</strong> {appointment.assigned_vet}</h2>
                        </div>
                        <div class="info-item">
                            <h2><strong>Create at:</strong> {formatDatetime(appointment.created_at)}</h2>
                        </div>
                        <div class="info-item">
                            <h2><strong>Last update at:</strong> {formatDatetime(appointment.updated_at)}</h2>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="pet-main-info">
                <div class="pet-image-section">
                    {#if appointment.pet.image_url}
                        <img src={appointment.pet.image_url} alt={appointment.pet.name} class="pet-image" />
                    {:else} 
                        <div class="pet-image-placeholder">🐾</div>
                    {/if}
                </div>

                <div class="pet-info-section">
                    <div class="info-item">
                            <h2><strong>Pet name:</strong> {appointment.pet.name}</h2>
                    </div>
                    <div class="pet-details">
                        <div class="detail-item">
                            <strong>Breed:</strong> {appointment.pet.breed}
                        </div>
                        <div class="detail-item">
                            <strong>Color:</strong> {appointment.pet.color}
                        </div>
                        <div class="detail-item">
                            <strong>Gender:</strong> {appointment.pet.gender}
                        </div>
                        <div class="detail-item">
                            <strong>Age:</strong> {appointment.pet.age} years old
                        </div>
                        <div class="detail-item">
                            <strong>Birth Date:</strong> {formatDate(appointment.pet.birth_date)}
                        </div>
                        <div class="detail-item">
                            <strong>Neutered/Spayed:</strong> {appointment.pet.neutered_status ? 'Yes' : 'No'}
                        </div>
                    </div>
                    
                    {#if appointment.pet.allergic || appointment.pet.marks || appointment.pet.chronic_conditions}
                        <div class="additional-info">
                            <h3>Additional Information</h3>
                            {#if appointment.pet.allergic}
                                <div class="info-item">
                                    <strong>Allergies:</strong> {appointment.pet.allergic}
                                </div>
                            {/if}
                            {#if appointment.pet.marks}
                                <div class="info-item">
                                    <strong>Distinctive Marks:</strong> {appointment.pet.marks}
                                </div>
                            {/if}
                            {#if appointment.pet.chronic_conditions}
                                <div class="info-item">
                                    <strong>Chronic Conditions:</strong> {appointment.pet.chronic_conditions}
                                </div>
                            {/if}
                        </div>
                    {/if}
                </div>
            </div>

            <div class="vaccination-section">
                <div class="section-header">
                    <h2>Vaccination History {appointment.pet.total_vaccinations ? `(${appointment.pet.total_vaccinations})` : ''}</h2>
                    {#if canAddVaccination()}
                        <button class="add-vaccination-btn" on:click={() => showAddVaccination = true}>
                            Add Vaccination
                        </button>
                    {/if}
                </div>

                {#if appointment.pet.vaccinations && appointment.pet.vaccinations.length > 0}
                    <div class="vaccinations-list">
                        {#each appointment.pet.vaccinations as vaccination (vaccination.id)}
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
        </div>
    {/if}

    <!-- Edit Pet Modal -->
    <!-- {#if isEditing && appointment.pet}
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
                    
                    <div class="form-actions">
                        <button type="button" class="cancel-btn" on:click={() => isEditing = false}>
                            Cancel
                        </button>
                        <button type="submit" class="submit-btn">Update Pet</button>
                    </div>
                </form>
            </div>
        </div>
    {/if} -->

    <!-- Add Vaccination Modal -->
    <!-- {#if showAddVaccination}
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
                        <input type="date" id="date" bind:value={newVaccination.date} required />
                    </div>
                    
                    <div class="form-group">
                        <label for="remarks">Remarks</label>
                        <textarea id="remarks" bind:value={newVaccination.remarks} rows="3"></textarea>
                    </div>
                    
                    <div class="form-actions">
                        <button type="button" class="cancel-btn" on:click={() => showAddVaccination = false}>
                            Cancel
                        </button>
                        <button type="submit" class="submit-btn">Add Vaccination</button>
                    </div>
                </form>
            </div>
        </div>
    {/if} -->
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

    .add-vaccination-btn {
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

    .no-vaccinations {
        text-align: center;
        padding: 2rem;
        color: #666;
        font-style: italic;
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
    }
</style>