<script lang="ts">
	import { onMount } from 'svelte';
	import ChatSidebar from '$lib/components/ChatSidebar.svelte';
	import ChatWindow from '$lib/components/ChatWindow.svelte';
	import { chats, currentChatId } from '$lib/stores/chats';
	import { apiClient } from '$lib/api/client';

	let healthStatus: 'checking' | 'online' | 'offline' = 'checking';

	onMount(async () => {
		// Check backend health
		try {
			await apiClient.healthCheck();
			healthStatus = 'online';
		} catch (e) {
			healthStatus = 'offline';
			console.error('Backend health check failed:', e);
		}

		// If no chats exist, create one
		if ($chats.length === 0) {
			handleNewChat();
		} else if (!$currentChatId) {
			// Set the first chat as active
			currentChatId.set($chats[0].id);
		}
	});

	function handleNewChat() {
		const chatId = chats.createChat();
		currentChatId.set(chatId);
	}
</script>

<svelte:head>
	<title>Simpleton - Chat Interface</title>
</svelte:head>

<div class="app">
	{#if healthStatus === 'offline'}
		<div class="offline-banner">
			<span class="status-icon">⚠️</span>
			<span>Backend is offline. Please ensure the Simpleton API is running on port 8000.</span>
		</div>
	{/if}

	<div class="app-container">
		<ChatSidebar onNewChat={handleNewChat} />
		<ChatWindow />
	</div>
</div>

<style>
	.app {
		width: 100%;
		height: 100vh;
		overflow: hidden;
	}

	.offline-banner {
		padding: 0.75rem 1rem;
		background: #7f1d1d;
		color: #fecaca;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		font-size: 0.875rem;
		font-weight: 500;
	}

	.status-icon {
		font-size: 1.125rem;
	}

	.app-container {
		display: flex;
		height: 100%;
	}

	:global(body) {
		margin: 0;
		padding: 0;
		font-family:
			-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans',
			'Helvetica Neue', sans-serif;
		background: #0a0a0a;
		color: #e5e5e5;
	}

	:global(*) {
		box-sizing: border-box;
	}
</style>
