<script lang="ts">
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import { isAuthenticated, user } from '$lib/auth';
    import { appointmentApi, petApi, userApi, vaccineApi, serviceApi } from '$lib/apiServices';
    const options = { timeZone: "Asia/Bangkok" };
    interface Appointment {
        id: number;
        user: User;
        purpose: string;
        pet: Pet;
        status: string;
        remarks?: string;
        assigned_vet?: User | null;
        vet_note?:string;
        date:string;
        created_at:string;
        updated_at:string;
        vaccinations?: Vaccination[];
        total_vaccinations?: number;
        treatments?: Treatment[]; // <-- Add this line
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
    interface Service {
        id: number;
        title: string;
        description: string;
    }

    interface Treatment {
        id?: number;
        service: number;
        appointment: number;
        description: string;
        vaccine: Vaccine | null; // Add this field
    }

    let appointment: Appointment | null = null;
    // let pet: Pet | null = null;
    let vaccines: Vaccine[] = [];
    let isLoading = false;
    let error = '';
    let showAddVaccination = false;
    let isEditing = false;
    let isUpdatingTreatment = false;
    let vets: User[] = [];
    let pets: Pet[] = [];
    let services: Service[] = [];
    let treatments: Treatment[] = [];
    let vetNote: string = '';

    // Edit form data
    let editData = {
        purpose: '',
        remarks: '',
        date: '',
        status: '',
        assigned_vet: null as number | null,
        pet: null as Pet | null,
    };

    // Vaccination form data
    let newVaccination = {
        vaccine_id: null as number | null,
        date: '',
        remarks: ''
    };

    let selectedPetId: number | null = null;

    $: if (appointment && isEditing) {
        editData.purpose = appointment.purpose;
        editData.remarks = appointment.remarks ?? '';
        // set date เป็น datetime-local format (yyyy-MM-ddTHH:mm)
        editData.date = appointment.date ? new Date(appointment.date).toISOString().slice(0,16) : '';
        editData.assigned_vet = appointment.assigned_vet?.id ?? null;
        editData.pet = appointment.pet;
        editData.status = appointment.status;
        selectedPetId = appointment.pet?.id ?? null;
    }

    $: appointmentId = parseInt($page.params.id || '0');
    onMount(async () => {
        if (!$isAuthenticated) {
            goto('/login');
            return;
        }
        await loadAppointment();
        await loadVaccines();
        await loadVets();
        await loadPets();
        await loadServices();
    });
    async function loadPets() {
        try {
            pets = await petApi.getPets();
        } catch (err) {
            console.error('Failed to load pets:', err);
        }
    };
    async function loadVets() {
        try {
            vets = await userApi.getUsersByRole('vet');
        } catch (err) {
            console.error('Failed to load vets:', err);
        }
    };
     async function loadAppointment() {
        try {
            isLoading = true;
            appointment = await appointmentApi.getAppointmentDetail(appointmentId);
            
            // Initialize edit form with current data
            if (appointment) {
                editData = {
                    purpose: appointment.purpose,
                    remarks: appointment.remarks ?? '',
                    date: appointment.date,
                    assigned_vet: null,
                    pet: appointment.pet,
                    status: appointment.status
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

    async function loadServices() {
        try {
            services = await serviceApi.getServices();
        } catch (err) {
            console.error('Failed to load services:', err);
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

    async function updateAppointment() {
        if (!appointment) return;

        try {
            const payload: any = {
                purpose: editData.purpose,
                remarks: editData.remarks,
                date: editData.date,
                user : appointment.user.id,
                pet: selectedPetId,
            };
            if ($user?.role === 'staff') {
                payload.status = editData.status,
                payload.assigned_vet = editData.assigned_vet;
                
            }
            await appointmentApi.editAppointment(appointment.id, payload);
            await loadAppointment();
            isEditing = false;
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to update appointment';
        }
    }

    function addTreatmentCard() {
        treatments = [...treatments, { 
            service: 0, 
            description: '',
            appointment: appointmentId,
            vaccine: null 
        }];
    }

    function removeTreatmentCard(index: number) {
        treatments = treatments.filter((_, i) => i !== index);
    }

    async function submitTreatment() {
        if (!appointment) return;

        try {
            const payload = {
                vet_note: vetNote,
                treatment: treatments
                    .filter(t => t.service !== 0)
                    .map(t => ({
                        ...t,
                        vaccine: t.vaccine || null, // Only include if selected
                        appointment: appointmentId
                    })),
                appointment : appointment.id
            };
            await appointmentApi.updateTreatment(appointment.id, payload);
            await loadAppointment();
            isUpdatingTreatment = false;
            treatments = [];
            vetNote = '';
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to update treatment';
        }
    }

    function canEdit(): boolean {
        if (!$user || !appointment) return false;
        return $user.role === 'staff' || (appointment.user.id === $user.id && appointment.status == 'booked');
    }
    function formatDatetime(dateString: string): string {
        const date = new Date(dateString).toLocaleString("en-US", { timeZone: "Asia/Bangkok" });
        const dateObj = new Date(date);
        const dd = String(dateObj.getDate()).padStart(2, "0");
        const mm = String(dateObj.getMonth() + 1).padStart(2, "0");
        const yyyy = dateObj.getFullYear();
        const hh = String(dateObj.getHours()).padStart(2, "0");
        const min = String(dateObj.getMinutes()).padStart(2, "0");

    return `${dd}-${mm}-${yyyy} ${hh}:${min}`;
    }
    function formatDate(dateString: string): string {
        const date = new Date(dateString).toLocaleString("en-US", { timeZone: "Asia/Bangkok" });
        const dateObj = new Date(date);
        const dd = String(dateObj.getDate()).padStart(2, "0");
        const mm = String(dateObj.getMonth() + 1).padStart(2, "0");
        const yyyy = dateObj.getFullYear();
        return `${yyyy}-${mm}-${dd}`;
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
        <div class="loading">
            <div class="loading-spinner"></div>
            Loading Appointment details...
        </div>
    {:else if !appointment}
        <div class="no-data">Appointment not found</div>
    {:else}
        <div class="page-header">
            <button class="back-btn" on:click={() => goto('/appointments')}>
                ← Back to Appointments
            </button>
            <div class="header-actions">
                {#if canEdit()}
                    <button class="create-btn" on:click={() => isEditing = true}>
                        Edit Appointment
                    </button>
                    
                {/if}
                {#if $user?.role === 'vet' && appointment.status === 'confirmed'}
                        <button class="treatment-btn" on:click={() => isUpdatingTreatment = true}>
                            Update Treatment
                        </button>
                    {/if}
            </div>
        </div>

        <div class="purpose-header">
            <h1>{appointment.purpose}</h1>
            
        </div>

        <div class="main-content">
            <!-- Appointment Info Card -->
            <div class="info-card appointment-info">
                <div class="card-header">
                    <h2>📅 Appointment Details</h2>
                    <span class="status-badge {appointment.status}">{appointment.status}</span>
                </div>
                <div class="card-content">
                    <div class="info-grid">
                        <div class="info-item">
                            <span class="label">Time</span>
                            <span class="value">{formatDatetime(appointment.date)}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">Owner</span>
                            <span class="value">{appointment.user.full_name}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">Assigned Vet</span>
                            <span class="value">{appointment.assigned_vet?.full_name || 'Not assigned'}</span>
                        </div>
                        <div class="info-item full-width">
                            <span class="label">Remarks</span>
                            <span class="value remarks">{appointment.remarks || '-'}</span>
                        </div>
                        {#if appointment.vet_note}
                            <div class="info-item full-width">
                                <span class="label">Vet Note</span>
                                <span class="value remarks">{appointment.vet_note || '-'}</span>
                            </div>
                        {/if}
                        {#if $user?.role === 'staff'}
                            
                        <div class="info-item">
                            <span class="label">Created</span>
                            <span class="value timestamp">{formatDatetime(appointment.created_at)}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">Last Updated</span>
                            <span class="value timestamp">{formatDatetime(appointment.updated_at)}</span>
                        </div>
                        {/if}
                    </div>
                </div>
            </div>

            <!-- Pet Info Card -->
            <div class="info-card pet-info">
                <div class="card-header">
                    <h2>🐾 Pet Information</h2>
                </div>
                <div class="card-content">
                    <div class="pet-profile">
                        <div class="pet-image-container">
                            {#if appointment.pet.image_url}
                                <img src={appointment.pet.image_url} alt={appointment.pet.name} />
                            {:else}
                                <div class="pet-image-placeholder">🐾</div>
                            {/if}
                        </div>
                        <div class="pet-basic-info">
                            <h3>{appointment.pet.name}</h3>
                            <div class="pet-tags">
                                <span class="tag breed">{appointment.pet.breed}</span>
                                <span class="tag">{appointment.pet.gender}</span>
                                <span class="tag">{appointment.pet.age} years old</span>
                                <span class="tag neutered">{appointment.pet.neutered_status ? 'Neutered' : 'Not Neutered'}</span>
                            </div>
                        </div>
                    </div>

                    <div class="pet-details-grid">
                        <div class="detail-item">
                            <span class="label">Color</span>
                            <span class="value">{appointment.pet.color}</span>
                        </div>
                        <div class="detail-item">
                            <span class="label">Birth Date</span>
                            <span class="value">{formatDate(appointment.pet.birth_date)}</span>
                        </div>
                    </div>

                    {#if appointment.pet.allergic || appointment.pet.marks || appointment.pet.chronic_conditions}
                        <div class="pet-medical-info">
                            <h4>Medical Information</h4>
                            {#if appointment.pet.allergic}
                                <div class="medical-item">
                                    <span class="icon">🚨</span>
                                    <div class="info">
                                        <strong>Allergies</strong>
                                        <p>{appointment.pet.allergic}</p>
                                    </div>
                                </div>
                            {/if}
                            {#if appointment.pet.marks}
                                <div class="medical-item">
                                    <span class="icon">🔍</span>
                                    <div class="info">
                                        <strong>Distinctive Marks</strong>
                                        <p>{appointment.pet.marks}</p>
                                    </div>
                                </div>
                            {/if}
                            {#if appointment.pet.chronic_conditions}
                                <div class="medical-item">
                                    <span class="icon">⚕️</span>
                                    <div class="info">
                                        <strong>Chronic Conditions</strong>
                                        <p>{appointment.pet.chronic_conditions}</p>
                                    </div>
                                </div>
                            {/if}
                        </div>
                    {/if}
                </div>
            </div>
        </div>

        <!-- Replace the bottom section with this new layout -->
        <div class="bottom-section">
            <!-- Vaccination History Card -->
            <div class="info-card vaccination-history">
                <div class="card-header">
                    <h2>💉 Vaccination Records</h2>
                    {#if appointment.total_vaccinations}
                        <span class="record-badge">{appointment.total_vaccinations} records</span>
                    {/if}
                </div>
                <div class="card-content">
                    {#if appointment.vaccinations && appointment.vaccinations.length > 0}
                        <div class="history-list">
                            {#each appointment.vaccinations as vaccination (vaccination.id)}
                                <div class="history-item">
                                    <div class="history-marker"></div>
                                    <div class="history-content">
                                        <h4>{vaccination.vaccine_name}</h4>
                                        <p class="date">📅 {formatDate(vaccination.date)}</p>
                                        {#if vaccination.remarks}
                                            <p class="remarks">📝 {vaccination.remarks}</p>
                                        {/if}
                                    </div>
                                </div>
                            {/each}
                        </div>
                    {:else}
                        <div class="empty-state">
                            <span class="icon">📋</span>
                            <p>No vaccination records found</p>
                        </div>
                    {/if}
                </div>
            </div>

            <!-- Treatment History Card -->
            <div class="info-card treatment-history">
                <div class="card-header">
                    <h2>🏥 Treatment Records</h2>
                    <span class="record-badge">Past treatments</span>
                </div>
                <div class="card-content">
                    {#if appointment.treatments && appointment.treatments.length > 0}
                        <div class="history-list">
                            {#each appointment.treatments as treatment (treatment.id)}
                                <div class="history-item">
                                    <div class="history-marker"></div>
                                    <div class="history-content">
                                        <h4>{treatment.service} {treatment.vaccine || ""}</h4>
                                        {#if treatment.description}
                                            <p class="remarks">📝 {treatment.description}</p>
                                        {/if}
                                    </div>
                                </div>
                            {/each}
                        </div>
                    {:else}
                    <div class="empty-state">
                        <span class="icon">📋</span>
                        <p>No treatment records available</p>
                    </div>
                    {/if}
                    <!-- Placeholder for future treatment records -->
                </div>
            </div>
        </div>
    {/if}

    <!-- Edit Appointment Modal -->
    {#if isEditing && appointment}
        <div class="modal-overlay" role="dialog" tabindex="-1" on:click={() => isEditing = false} on:keydown={(e) => e.key === 'Escape' && (isEditing = false)}>
            <div class="modal-content" role="document" tabindex="0" on:click|stopPropagation on:keydown|stopPropagation>
                <h2>Edit Appointment</h2>
                <form on:submit|preventDefault={updateAppointment} class="edit-form">
                    <div class="form-group">
                        <label for="editPet">Pet *</label>
                        <select id="editPet" bind:value={selectedPetId} required>
                            <option value={null}>Select Pet</option>
                            {#each pets as pet_choice (pet_choice.id)}
                                <option value={pet_choice.id}>{pet_choice.name} ({pet_choice.breed})</option>
                            {/each}
                        </select>
                        <small>Current: {appointment.pet.name}</small>
                    </div>
                    <div class="form-group">
                        <label for="editPurpose">Purpose *</label>
                        <input type="text" id="editPurpose" bind:value={editData.purpose} required />
                        <small>Current: {appointment.purpose}</small>
                    </div>
                    <div class="form-group">
                        <label for="editRemarks">Remarks</label>
                        <textarea id="editRemarks" bind:value={editData.remarks}></textarea>
                        <small>Current: {appointment.remarks || '-'}</small>
                    </div>
                    <div class="form-group">
                        <label for="editDate">Appointment Date *</label>
                        <input type="datetime-local" id="editDate" bind:value={editData.date} required />
                        <small>Current: {formatDatetime(appointment.date)}</small>
                    </div>
                    
                    {#if $user?.role === 'staff'}
                    <div class="form-group">
                        <label for="editStatus">Status</label>
                        <select id="editStatus" bind:value={editData.status} required>
                            <option value="booked">booked</option>
                            <option value="confirmed">confirmed</option>
                            <option value="completed">completed</option>
                            <option value="rejected">rejected</option>
                            <option value="cancelled">cancelled</option>
                        </select>
                        <small>Current: {appointment.status}</small>
                    </div>
                        <div class="form-group">
                            <label for="editAssignedVet">Assigned Vet *</label>
                            <select id="editAssignedVet" bind:value={editData.assigned_vet} required>
                                <option value={null}>Select Vet</option>
                                {#each vets as vet (vet.id)}
                                    <option value={vet.id}>{vet.full_name}</option>
                                {/each}
                            </select>
                            <small>Current: {appointment.assigned_vet?.full_name || 'Not assign now'}</small>
                        </div>
                    {/if}
                    <div class="form-actions">
                        <button type="button" class="cancel-btn" on:click={() => isEditing = false}>
                            Cancel
                        </button>
                        <button type="submit" class="submit-btn">Update Appointment</button>
                    </div>
                </form>
            </div>
        </div>
    {/if}

    <!-- Treatment Update Modal -->
    {#if isUpdatingTreatment && appointment}
        <div class="modal-overlay" role="dialog" tabindex="-1" 
            on:click={() => isUpdatingTreatment = false} 
            on:keydown={(e) => e.key === 'Escape' && (isUpdatingTreatment = false)}>
            <div class="modal-content" role="document" tabindex="0" 
                on:click|stopPropagation on:keydown|stopPropagation>
                <div class="modal-header">
                    <h2>Update Treatment</h2>
                    <button class="close-btn" on:click={() => isUpdatingTreatment = false}>&times;</button>
                </div>
                <form on:submit|preventDefault={submitTreatment} class="treatment-form">
                    <div class="form-group">
                        <label for="vetNote">Vet Note</label>
                        <textarea id="vetNote" bind:value={vetNote} rows="3" 
                            placeholder="Enter veterinary notes here"></textarea>
                    </div>

                    <div class="treatments-container">
                        {#each treatments as treatment, i (i)}
                            <div class="treatment-card">
                                <button type="button" class="remove-treatment" 
                                    on:click={() => removeTreatmentCard(i)}>×</button>
                                <div class="form-group">
                                    <label for="service{i}">Service *</label>
                                    <select id="service{i}" bind:value={treatment.service} required>
                                        <option value={0}>Select Service</option>
                                        {#each services as service}
                                            <option value={service.id}>{service.title}</option>
                                        {/each}
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label for="description{i}">Description *</label>
                                    <textarea id="description{i}" 
                                        bind:value={treatment.description} 
                                        placeholder="Enter treatment description" required></textarea>
                                </div>
                                {#if treatment.service === 1} 
                                <div class="form-group">
                                    <label for="vaccine{i}">Vaccine</label>
                                    <select id="vaccine{i}" bind:value={treatment.vaccine}>
                                        <option value={null}>Select Vaccine</option>
                                        {#each vaccines as vaccine}
                                            <option value={vaccine.id}>{vaccine.name}</option>
                                        {/each}
                                    </select>
                                </div>
                                {/if}
                            </div>
                        {/each}
                    </div>

                    <button type="button" class="add-treatment-btn" on:click={addTreatmentCard}>
                        + Add Treatment
                    </button>

                    <div class="form-actions">
                        <button type="button" class="cancel-btn" 
                            on:click={() => isUpdatingTreatment = false}>
                            Cancel
                        </button>
                        <button type="submit" class="submit-btn">
                            Update Treatment
                        </button>
                    </div>
                </form>
            </div>
        </div>
    {/if}

   
</div>

<style>
    /* Base styles */
    .pet-detail-container {
        padding: 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }

    .page-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
    }

    .purpose-header {
        background: #fff8e1;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        border: 1px solid #f3e8a6;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .purpose-header h1 {
        color: #b8860b;
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 1px 1px 0 rgba(0,0,0,0.1);
    }

    .main-content {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
        margin-bottom: 2rem;
    }

    /* Card Styles */
    .info-card {
        background: white;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(184, 134, 11, 0.1);
        overflow: hidden;
    }

    .card-header {
        background: #fff8e1;
        padding: 1.5rem;
        border-bottom: 2px solid #f3e8a6;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .card-header h2 {
        color: #b8860b;
        margin: 0;
        font-size: 1.3rem;
    }

    .card-content {
        padding: 1.5rem;
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
    /* Status Badge */
    .status-badge {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
    }

    .status-badge.booked { background: #f4eed5; color: #c0a80b; }
    .status-badge.confirmed { background: #ebf2f9; color: #1976d2; }
    .status-badge.completed { background: #e0f7e0; color: #2d7d2d; }
    .status-badge.rejected { background: #f0dcdc; color: #d32f2f; }
    .status-badge.cancelled { background: #efdfd3; color: #e66909; }

    /* Info Grid */
    .info-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
    }

    .info-item {
        padding: 1rem;
        background: #f8f6f0;
        border-radius: 8px;
    }

    .info-item.full-width {
        grid-column: 1 / -1;
    }

    .label {
        display: block;
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }

    .value {
        color: #333;
        font-weight: 600;
    }

    .value.remarks {
        font-style: italic;
        font-weight: normal;
    }

    .value.timestamp {
        font-size: 0.9rem;
        color: #666;
    }

    /* Pet Profile */
    .pet-profile {
        display: flex;
        gap: 1.5rem;
        margin-bottom: 2rem;
    }

    .pet-image-container {
        width: 120px;
        height: 120px;
        border-radius: 60px;
        overflow: hidden;
        border: 3px solid #f3e8a6;
        flex-shrink: 0;
    }

    .pet-image-container img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .pet-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }

    .tag {
        background: #fff8e1;
        color: #b8860b;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.9rem;
    }

    .tag.breed {
        background: #daa520;
        color: white;
    }

    .tag.neutered {
        background: #e8f5e9;
        color: #2e7d32;
    }

    /* Medical Info */
    .pet-medical-info {
        margin-top: 2rem;
        padding: 1.5rem;
        background: #fff8e1;
        border-radius: 12px;
    }

    .medical-item {
        display: flex;
        gap: 1rem;
        padding: 1rem;
        border-bottom: 1px dashed #daa520;
    }

    .medical-item:last-child {
        border-bottom: none;
    }

    .medical-item .icon {
        font-size: 1.5rem;
    }

    /* Vaccination Timeline */
    .vaccination-timeline {
        position: relative;
        padding-left: 2rem;
    }

    .vaccination-item {
        position: relative;
        padding-bottom: 2rem;
    }

    .timeline-dot {
        position: absolute;
        left: -2rem;
        width: 1rem;
        height: 1rem;
        background: #daa520;
        border-radius: 50%;
        border: 3px solid #fff8e1;
    }

    .vaccination-content {
        background: #fff8e1;
        padding: 1rem;
        border-radius: 8px;
        margin-left: 1rem;
    }

    /* Loading & No Data States */
    .loading, .no-data-message {
        text-align: center;
        padding: 3rem;
        color: #666;
    }

    .loading-spinner {
        border: 3px solid #f3e8a6;
        border-top: 3px solid #daa520;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 0 auto 1rem;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    /* Edit Appointment Modal styles */
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

    .edit-form {
        display: flex;
        flex-direction: column;
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
    /* New styles for bottom section */
    .bottom-section {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 2rem;
        margin-top: 2rem;
    }

    .history-list {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .history-item {
        display: flex;
        gap: 1rem;
        padding: 1rem;
        background: #fff8e1;
        border-radius: 8px;
        position: relative;
        border-left: 4px solid #daa520;
    }

    .history-marker {
        position: absolute;
        left: -0.5rem;
        top: 50%;
        transform: translateY(-50%);
        width: 1rem;
        height: 1rem;
        background: #daa520;
        border: 3px solid #fff;
        border-radius: 50%;
    }

    .history-content {
        flex: 1;
    }

    .history-content h4 {
        color: #b8860b;
        margin: 0 0 0.5rem 0;
    }

    .record-badge {
        background: #f3e8a6;
        color: #b8860b;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.9rem;
    }

    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        color: #666;
        gap: 0.5rem;
    }

    .empty-state .icon {
        font-size: 2rem;
        opacity: 0.5;
    }

    /* Treatment Update Modal styles */
    .treatment-btn {
        background: #20a7da;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        cursor: pointer;
        margin-left: 0.5rem;
    }

    .treatments-container {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        margin: 1rem 0;
    }

    .treatment-card {
        background: #fff8e1;
        padding: 1rem;
        border-radius: 8px;
        position: relative;
        border: 1px solid #f3e8a6;
    }

    .remove-treatment {
        position: absolute;
        right: 0.5rem;
        top: 0.5rem;
        background: none;
        border: none;
        font-size: 1.5rem;
        color: #c62828;
        cursor: pointer;
        padding: 0.2rem 0.5rem;
        border-radius: 50%;
    }

    .remove-treatment:hover {
        background: #ffebee;
    }

    .add-treatment-btn {
        width: 100%;
        padding: 0.75rem;
        background: #f3e8a6;
        color: #b8860b;
        border: 2px dashed #daa520;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        margin: 1rem 0;
    }

    .add-treatment-btn:hover {
        background: #fff8e1;
    }

    .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
    }

    .close-btn {
        background: none;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        color: #666;
    }
</style>