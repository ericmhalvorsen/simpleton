<script lang="ts">
	import type { ChatMessage } from '../api/types';

	export let message: ChatMessage;

	$: isUser = message.role === 'user';
	$: isSystem = message.role === 'system';
</script>

<div
	class="message"
	class:user={isUser}
	class:assistant={!isUser && !isSystem}
	class:system={isSystem}
>
	<div class="message-role">
		{#if isUser}
			<div class="avatar user-avatar">You</div>
		{:else if isSystem}
			<div class="avatar system-avatar">System</div>
		{:else}
			<div class="avatar assistant-avatar">AI</div>
		{/if}
	</div>
	<div class="message-content">
		{@html message.content.replace(/\n/g, '<br>')}
	</div>
</div>

<style>
	.message {
		display: flex;
		gap: 1rem;
		padding: 1.5rem;
		border-bottom: 1px solid #262626;
	}

	.message.user {
		background: #1a1a1a;
	}

	.message.assistant {
		background: #0a0a0a;
	}

	.message.system {
		background: #0f1419;
		font-size: 0.875rem;
		color: #a3a3a3;
	}

	.message-role {
		flex-shrink: 0;
	}

	.avatar {
		width: 36px;
		height: 36px;
		border-radius: 0.375rem;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.75rem;
		font-weight: 600;
		color: white;
	}

	.user-avatar {
		background: #2563eb;
	}

	.assistant-avatar {
		background: #16a34a;
	}

	.system-avatar {
		background: #6b7280;
	}

	.message-content {
		flex: 1;
		line-height: 1.6;
		color: #e5e5e5;
		word-wrap: break-word;
	}

	.message-content :global(br) {
		display: block;
		margin: 0.5rem 0;
	}
</style>
