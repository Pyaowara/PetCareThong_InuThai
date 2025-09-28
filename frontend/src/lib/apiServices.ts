import { apiJson, apiFormData, API_CONFIG } from './api';

// User Management
export const userApi = {
    // Get all users (Staff only)
    getUsers: () => apiJson('/users/'),
    
    // Get current user profile
    getProfile: () => apiJson('/auth/profile/'),
    
    // Update current user profile
    updateProfile: (profileData: any) => apiJson('/auth/profile/', {
        method: 'PUT',
        body: JSON.stringify(profileData)
    }),
    
    // Get specific user details (Staff only)
    getUserDetail: (userId: number) => apiJson(`/users/${userId}/`),
    
    // Update user (Staff only)
    updateUser: (userId: number, userData: FormData) => apiFormData(`/users/${userId}/`, userData, { method: 'PUT' }),
    
    // Update user status (Staff only)
    updateUserStatus: (userId: number, isActive: boolean) => apiJson(`/users/${userId}/`, {
        method: 'PUT',
        body: JSON.stringify({ is_active: isActive })
    }),
    
    // Delete user (Staff only)
    deleteUser: (userId: number) => apiJson(`/users/${userId}/`, { method: 'DELETE' }),
};

// Pet Management
export const petApi = {
    // Get all pets (role-based filtering on backend)
    getPets: () => apiJson('/pets/'),
    
    // Create new pet
    createPet: (petData: FormData) => apiFormData('/pets/', petData),
    
    // Get specific pet details
    getPetDetail: (petId: number) => apiJson(`/pets/${petId}/`),
    
    // Update pet
    updatePet: (petId: number, petData: FormData) => apiFormData(`/pets/${petId}/`, petData, { method: 'PUT' }),
    
    // Delete pet
    deletePet: (petId: number) => apiJson(`/pets/${petId}/`, { method: 'DELETE' }),
};

// Vaccine Management
export const vaccineApi = {
    // Get all vaccines
    getVaccines: () => apiJson('/vaccines/'),
    
    // Create new vaccine (Staff/Vet only)
    createVaccine: (vaccineData: any) => apiJson('/vaccines/', {
        method: 'POST',
        body: JSON.stringify(vaccineData)
    }),
    
    // Get specific vaccine
    getVaccineDetail: (vaccineId: number) => apiJson(`/vaccines/${vaccineId}/`),
    
    // Update vaccine (Staff/Vet only)
    updateVaccine: (vaccineId: number, vaccineData: any) => apiJson(`/vaccines/${vaccineId}/`, {
        method: 'PUT',
        body: JSON.stringify(vaccineData)
    }),
    
    // Delete vaccine (Staff/Vet only)
    deleteVaccine: (vaccineId: number) => apiJson(`/vaccines/${vaccineId}/`, { method: 'DELETE' }),
};

// Vaccination Management
export const vaccinationApi = {
    // Get vaccinations with optional filters
    getVaccinations: (filters: { pet_id?: number; vaccine_id?: number; owner_id?: number } = {}) => {
        const params = new URLSearchParams();
        if (filters.pet_id) params.append('pet_id', filters.pet_id.toString());
        if (filters.vaccine_id) params.append('vaccine_id', filters.vaccine_id.toString());
        if (filters.owner_id) params.append('owner_id', filters.owner_id.toString());
        
        const queryString = params.toString();
        return apiJson(`/vaccinations/${queryString ? '?' + queryString : ''}`);
    },
    
    // Create vaccination record (Staff/Vet only)
    createVaccination: (vaccinationData: any) => apiJson('/vaccinations/', {
        method: 'POST',
        body: JSON.stringify(vaccinationData)
    }),
    
    // Get specific vaccination
    getVaccinationDetail: (vaccinationId: number) => apiJson(`/vaccinations/${vaccinationId}/`),
    
    // Update vaccination (Staff/Vet only)
    updateVaccination: (vaccinationId: number, vaccinationData: any) => apiJson(`/vaccinations/${vaccinationId}/`, {
        method: 'PUT',
        body: JSON.stringify(vaccinationData)
    }),
    
    // Delete vaccination (Staff/Vet only)
    deleteVaccination: (vaccinationId: number) => apiJson(`/vaccinations/${vaccinationId}/`, { method: 'DELETE' }),
};

// Service Management (if needed in future)
export const serviceApi = {
    getServices: () => apiJson('/services/'),
    createService: (serviceData: any) => apiJson('/services/', {
        method: 'POST',
        body: JSON.stringify(serviceData)
    }),
    getServiceDetail: (serviceId: number) => apiJson(`/services/${serviceId}/`),
    updateService: (serviceId: number, serviceData: any) => apiJson(`/services/${serviceId}/`, {
        method: 'POST',
        body: JSON.stringify(serviceData)
    }),
    deleteService: (serviceId: number) => apiJson(`/services/${serviceId}/`, { method: 'DELETE' }),
};

export const appointmentApi = {
    getAppointment: () => apiJson('/appointments/'),
    bookAppointment: (appointmentData: any) => apiJson('/appointments/book/', {
        method: 'POST',
        body: JSON.stringify(appointmentData)
    }),
    getAppointmentDetail: (appointmentId: number) => apiJson(`/appointments/${appointmentId}/`),
    updateAppointment: (appointmentId: number, appointmentData: any) => apiJson(`/appointments/update/${appointmentId}/`, {
        method: 'POST',
        body: JSON.stringify(appointmentData)
    }),
    deleteAppointment: (appointmentId: number) => apiJson(`/appointments/update/${appointmentId}/`, { method: 'DELETE' }),
};