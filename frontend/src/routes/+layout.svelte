<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import { isAuthenticated } from '$lib/auth';
	import { page } from '$app/stores';
	import Navbar from '$lib/components/Navbar.svelte';

	let { children } = $props();

	// Don't show navbar on login/register pages
	const showNavbar = $derived($isAuthenticated && !($page.route.id?.includes('login') || $page.route.id?.includes('register')));
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{#if showNavbar}
	<Navbar />
{/if}

<main class:has-navbar={showNavbar}>
	{@render children?.()}
</main>

<style>
	:global(body) {
		margin: 0;
		font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
		background-color: #faf8f3;
	}

	main {
		min-height: 100vh;
	}

	main.has-navbar {
		padding-top: 70px; /* Account for fixed navbar height */
	}
</style>
