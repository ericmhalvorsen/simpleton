<script lang="ts">
	import { chats, currentChatId } from '../stores/chats';
	import type { Chat } from '../api/types';

	export let onNewChat: () => void;

	function selectChat(chatId: string) {
		currentChatId.set(chatId);
	}

	function formatDate(dateString: string): string {
		const date = new Date(dateString);
		const now = new Date();
		const diffMs = now.getTime() - date.getTime();
		const diffMins = Math.floor(diffMs / 60000);
		const diffHours = Math.floor(diffMs / 3600000);
		const diffDays = Math.floor(diffMs / 86400000);

		if (diffMins < 1) return 'Just now';
		if (diffMins < 60) return `${diffMins}m ago`;
		if (diffHours < 24) return `${diffHours}h ago`;
		if (diffDays < 7) return `${diffDays}d ago`;
		return date.toLocaleDateString();
	}
</script>

<aside class="sidebar">
	<div class="sidebar-header">
		<h1>Simpleton</h1>
		<button class="new-chat-btn" on:click={onNewChat}>
			<span>+</span>
			New Chat
		</button>
	</div>

	<div class="chat-list">
		{#each $chats as chat (chat.id)}
			<button
				class="chat-item"
				class:active={$currentChatId === chat.id}
				on:click={() => selectChat(chat.id)}
			>
				<div class="chat-title">{chat.title}</div>
				<div class="chat-meta">
					<span class="chat-date">{formatDate(chat.updatedAt)}</span>
					<span class="chat-model">{chat.model}</span>
				</div>
			</button>
		{:else}
			<div class="empty-state">
				<p>No chats yet</p>
				<p class="hint">Click "New Chat" to start</p>
			</div>
		{/each}
	</div>
</aside>

<style>
	.sidebar {
		width: 260px;
		background: #1a1a1a;
		border-right: 1px solid #333;
		display: flex;
		flex-direction: column;
		height: 100vh;
	}

	.sidebar-header {
		padding: 1rem;
		border-bottom: 1px solid #333;
	}

	.sidebar-header h1 {
		font-size: 1.5rem;
		margin: 0 0 1rem 0;
		color: #fff;
		font-weight: 600;
	}

	.new-chat-btn {
		width: 100%;
		padding: 0.75rem;
		background: #2563eb;
		color: white;
		border: none;
		border-radius: 0.5rem;
		cursor: pointer;
		font-size: 0.875rem;
		font-weight: 500;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		transition: background 0.2s;
	}

	.new-chat-btn:hover {
		background: #1d4ed8;
	}

	.new-chat-btn span {
		font-size: 1.25rem;
		line-height: 1;
	}

	.chat-list {
		flex: 1;
		overflow-y: auto;
		padding: 0.5rem;
	}

	.chat-item {
		width: 100%;
		padding: 0.75rem;
		background: transparent;
		border: 1px solid transparent;
		border-radius: 0.5rem;
		cursor: pointer;
		text-align: left;
		margin-bottom: 0.25rem;
		transition: all 0.2s;
		color: #e5e5e5;
	}

	.chat-item:hover {
		background: #262626;
		border-color: #404040;
	}

	.chat-item.active {
		background: #262626;
		border-color: #2563eb;
	}

	.chat-title {
		font-size: 0.875rem;
		font-weight: 500;
		margin-bottom: 0.25rem;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.chat-meta {
		display: flex;
		justify-content: space-between;
		align-items: center;
		font-size: 0.75rem;
		color: #a3a3a3;
	}

	.chat-model {
		padding: 0.125rem 0.5rem;
		background: #333;
		border-radius: 0.25rem;
	}

	.empty-state {
		text-align: center;
		padding: 2rem 1rem;
		color: #737373;
	}

	.empty-state p {
		margin: 0.5rem 0;
	}

	.hint {
		font-size: 0.875rem;
	}

	/* Scrollbar styling */
	.chat-list::-webkit-scrollbar {
		width: 6px;
	}

	.chat-list::-webkit-scrollbar-track {
		background: transparent;
	}

	.chat-list::-webkit-scrollbar-thumb {
		background: #404040;
		border-radius: 3px;
	}

	.chat-list::-webkit-scrollbar-thumb:hover {
		background: #525252;
	}
</style>
