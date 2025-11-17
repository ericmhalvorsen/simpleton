<script lang="ts">
	import { afterUpdate } from 'svelte';
	import { currentChat, chats } from '../stores/chats';
	import { apiClient } from '../api/client';
	import ChatMessage from './ChatMessage.svelte';
	import ChatInput from './ChatInput.svelte';
	import type { ChatMessage as ChatMessageType } from '../api/types';

	let messagesContainer: HTMLDivElement;
	let isLoading = false;
	let error: string | null = null;

	$: hasMessages = $currentChat?.messages && $currentChat.messages.length > 0;

	function scrollToBottom() {
		if (messagesContainer) {
			messagesContainer.scrollTop = messagesContainer.scrollHeight;
		}
	}

	afterUpdate(() => {
		scrollToBottom();
	});

	async function handleSendMessage(event: CustomEvent<string>) {
		const content = event.detail;
		if (!$currentChat || isLoading) return;

		error = null;
		isLoading = true;

		// Add user message
		const userMessage: ChatMessageType = {
			role: 'user',
			content,
			timestamp: new Date().toISOString()
		};
		chats.addMessage($currentChat.id, userMessage);

		// Add empty assistant message that will be updated
		const assistantMessage: ChatMessageType = {
			role: 'assistant',
			content: '',
			timestamp: new Date().toISOString()
		};
		chats.addMessage($currentChat.id, assistantMessage);

		try {
			// Prepare messages for API
			const messages = $currentChat.messages.slice(0, -1); // Exclude the empty assistant message we just added

			// Stream the response
			let fullResponse = '';
			for await (const chunk of apiClient.chatStream({
				messages,
				model: $currentChat.model,
				temperature: 0.7
			})) {
				fullResponse += chunk;
				chats.updateLastMessage($currentChat.id, fullResponse);
			}

			if (!fullResponse) {
				throw new Error('No response from API');
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to send message';
			console.error('Chat error:', e);
			// Remove the failed assistant message
			chats.update((allChats) =>
				allChats.map((chat) => {
					if (chat.id === $currentChat?.id) {
						return {
							...chat,
							messages: chat.messages.slice(0, -1)
						};
					}
					return chat;
				})
			);
		} finally {
			isLoading = false;
		}
	}
</script>

<div class="chat-window">
	{#if !$currentChat}
		<div class="empty-chat">
			<div class="welcome">
				<h2>Welcome to Simpleton</h2>
				<p>Select a chat from the sidebar or create a new one to get started.</p>
				<div class="features">
					<div class="feature">
						<span class="feature-icon">💬</span>
						<span>Chat with LLMs</span>
					</div>
					<div class="feature">
						<span class="feature-icon">🔍</span>
						<span>RAG Search</span>
					</div>
					<div class="feature">
						<span class="feature-icon">🎯</span>
						<span>Multiple Models</span>
					</div>
				</div>
			</div>
		</div>
	{:else}
		<div class="messages-container" bind:this={messagesContainer}>
			{#if !hasMessages}
				<div class="chat-placeholder">
					<h3>Start a conversation</h3>
					<p>Using model: <strong>{$currentChat.model}</strong></p>
				</div>
			{:else}
				{#each $currentChat.messages as message (message.timestamp || Math.random())}
					<ChatMessage {message} />
				{/each}
			{/if}

			{#if isLoading}
				<div class="loading-indicator">
					<div class="loading-dots">
						<span></span>
						<span></span>
						<span></span>
					</div>
				</div>
			{/if}
		</div>

		{#if error}
			<div class="error-banner">
				<span class="error-icon">⚠️</span>
				{error}
			</div>
		{/if}

		<ChatInput on:send={handleSendMessage} disabled={isLoading} />
	{/if}
</div>

<style>
	.chat-window {
		flex: 1;
		display: flex;
		flex-direction: column;
		height: 100vh;
		background: #0a0a0a;
	}

	.empty-chat {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2rem;
	}

	.welcome {
		text-align: center;
		max-width: 500px;
	}

	.welcome h2 {
		font-size: 2rem;
		margin: 0 0 0.5rem 0;
		color: #e5e5e5;
	}

	.welcome p {
		color: #a3a3a3;
		margin: 0 0 2rem 0;
		font-size: 1.125rem;
	}

	.features {
		display: flex;
		gap: 1.5rem;
		justify-content: center;
		margin-top: 2rem;
	}

	.feature {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		padding: 1rem;
		background: #1a1a1a;
		border: 1px solid #333;
		border-radius: 0.5rem;
		font-size: 0.875rem;
		color: #e5e5e5;
	}

	.feature-icon {
		font-size: 2rem;
	}

	.messages-container {
		flex: 1;
		overflow-y: auto;
	}

	.chat-placeholder {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		color: #737373;
		text-align: center;
		padding: 2rem;
	}

	.chat-placeholder h3 {
		margin: 0 0 0.5rem 0;
		color: #a3a3a3;
	}

	.chat-placeholder p {
		margin: 0;
	}

	.loading-indicator {
		padding: 1.5rem;
		display: flex;
		align-items: center;
		gap: 1rem;
		background: #0a0a0a;
		border-bottom: 1px solid #262626;
	}

	.loading-dots {
		display: flex;
		gap: 0.5rem;
		padding-left: 3rem;
	}

	.loading-dots span {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: #16a34a;
		animation: bounce 1.4s infinite ease-in-out both;
	}

	.loading-dots span:nth-child(1) {
		animation-delay: -0.32s;
	}

	.loading-dots span:nth-child(2) {
		animation-delay: -0.16s;
	}

	@keyframes bounce {
		0%,
		80%,
		100% {
			transform: scale(0);
		}
		40% {
			transform: scale(1);
		}
	}

	.error-banner {
		padding: 1rem;
		background: #7f1d1d;
		color: #fecaca;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.875rem;
		border-top: 1px solid #991b1b;
	}

	.error-icon {
		font-size: 1.125rem;
	}

	/* Scrollbar styling */
	.messages-container::-webkit-scrollbar {
		width: 8px;
	}

	.messages-container::-webkit-scrollbar-track {
		background: transparent;
	}

	.messages-container::-webkit-scrollbar-thumb {
		background: #404040;
		border-radius: 4px;
	}

	.messages-container::-webkit-scrollbar-thumb:hover {
		background: #525252;
	}
</style>
