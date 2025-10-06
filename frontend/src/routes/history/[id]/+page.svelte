<script lang="ts">
    import { onMount } from "svelte";
    import { page } from "$app/stores";
    import { treatmentApi } from "$lib/apiServices";

    interface Treatment {
        id: number;
        appointment: string;
        service: string;
        description: string;
        vaccine?: string;
        pet: string;
    }

    let treatments: Treatment[] = [];
    let isLoading = true;
    let error = "";
    let searchQuery = "";
    let purposeFilter = "";
    let serviceFilter = "";
    let petFilter = "";

    $: filteredTreatments = treatments.filter((treatment) => {
        const matchesSearch =
            !searchQuery ||
            treatment.appointment
                .toLowerCase()
                .includes(searchQuery.toLowerCase()) ||
            treatment.service
                .toLowerCase()
                .includes(searchQuery.toLowerCase()) ||
            treatment.pet
                .toLowerCase()
                .includes(searchQuery.toLowerCase()) ||
            treatment.description
                .toLowerCase()
                .includes(searchQuery.toLowerCase());
        
        const matchesPurpose = !purposeFilter || treatment.appointment === purposeFilter;
        const matchesService = !serviceFilter || treatment.service === serviceFilter;
        const matchesPet = !petFilter || treatment.pet === petFilter;

        return matchesSearch && matchesPurpose && matchesService && matchesPet;
    });

    $: availablePurposes = [...new Set(treatments.map(t => t.appointment))].sort();
    $: availableServices = [...new Set(treatments.map(t => t.service))].sort();
    $: availablePets = [...new Set(treatments.map(t => t.pet))].sort();

    // Fetch user history based on ID from the URL
    async function fetchUserHistory(userId: number) {
        try {
            isLoading = true;
            const response = await treatmentApi.getTreatmentHistory(userId);
            if (!response || !response.treatments) {
                throw new Error("No treatments found or invalid response format");
            }
            treatments = response.treatments;
        } catch (err) {
            error = err instanceof Error ? err.message : "Failed to load user history";
        } finally {
            isLoading = false;
        }
    }

    function clearFilters() {
        searchQuery = "";
        purposeFilter = "";
        serviceFilter = "";
        petFilter = "";
    }

    onMount(() => {
        const userId = parseInt($page.params.id ?? "");
        if (!isNaN(userId)) {
            fetchUserHistory(userId);
        } else {
            error = "Invalid user ID";
        }
    });
</script>

<div class="history-container">
    <div class="history-header">
        <h1>User Treatment History</h1>
    </div>

    <div class="filters-section">
        <div class="filters-row">
            <div class="filter-group">
                <label for="search">Search</label>
                <input
                    id="search"
                    type="text"
                    class="filter-input"
                    placeholder="Search treatments..."
                    bind:value={searchQuery}
                />
            </div>
            <div class="filter-group">
                <label for="pet">Pet</label>
                <select
                    id="pet"
                    class="filter-select"
                    bind:value={petFilter}
                >
                    <option value="">All Pets</option>
                    {#each availablePets as pet}
                        <option value={pet}>{pet}</option>
                    {/each}
                </select>
            </div>
            <div class="filter-group">
                <label for="purpose">Appointment Purpose</label>
                <select
                    id="purpose"
                    class="filter-select"
                    bind:value={purposeFilter}
                >
                    <option value="">All Purposes</option>
                    {#each availablePurposes as purpose}
                        <option value={purpose}>{purpose}</option>
                    {/each}
                </select>
            </div>
            <div class="filter-group">
                <label for="service">Service</label>
                <select
                    id="service"
                    class="filter-select"
                    bind:value={serviceFilter}
                >
                    <option value="">All Services</option>
                    {#each availableServices as service}
                        <option value={service}>{service}</option>
                    {/each}
                </select>
            </div>
            
            <button
                type="button"
                class="clear-filters-btn"
                on:click={clearFilters}
            >
                Clear Filters
            </button>
        </div>
    </div>

    {#if isLoading}
        <div class="loading">Loading treatment history...</div>
    {:else if error}
        <div class="error-message">{error}</div>
    {:else}
        {#if filteredTreatments.length > 0}
            <div class="history-table-container">
                <table class="history-table">
                    <thead>
                        <tr>
                            <th>Pet Name</th>
                            <th>Appointment Purpose</th>
                            <th>Service</th>
                            <th>Description</th>
                            
                        </tr>
                    </thead>
                    <tbody>
                        {#each filteredTreatments as treatment}
                            <tr>
                                <td><strong>{treatment.pet}</strong></td>
                                <td><strong>{treatment.appointment}</strong></td>
                                <td><strong>{treatment.service}</strong> {treatment.vaccine || " "}</td>
                                <td>{treatment.description}</td>
                                
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        {:else if treatments.length > 0}
            <div class="no-data">No treatments match the current filters.</div>
        {:else}
            <div class="no-data">No treatment records found for this user.</div>
        {/if}
    {/if}
</div>

<style>
    .history-container {
        padding: 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }

    .history-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
    }

    .history-header h1 {
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

    .history-table-container {
        background: white;
        border-radius: 12px;
        border: 1px solid #f3e8a6;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(184, 134, 11, 0.1);
    }

    .history-table {
        width: 100%;
        border-collapse: collapse;
    }

    .history-table th {
        background: #f8f6f0;
        color: #b8860b;
        font-weight: 700;
        padding: 1rem;
        text-align: left;
        border-bottom: 2px solid #f3e8a6;
    }

    .history-table td {
        padding: 1rem;
        border-bottom: 1px solid #f3e8a6;
        vertical-align: top;
    }

    .history-table tr:hover {
        background: #fffdf5;
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

        .history-table-container {
            overflow-x: auto;
        }

        .history-table {
            min-width: 800px;
        }
    }

    @media (max-width: 768px) {
        .history-header {
            flex-direction: column;
            gap: 1rem;
        }

        .filters-row {
            grid-template-columns: 1fr;
        }
    }
</style>