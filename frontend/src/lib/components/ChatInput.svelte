<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let disabled = false;
	export let placeholder = 'Type your message...';

	let input = '';
	let textareaElement: HTMLTextAreaElement;

	const dispatch = createEventDispatcher<{ send: string }>();

	function handleSubmit() {
		if (input.trim() && !disabled) {
			dispatch('send', input.trim());
			input = '';
			if (textareaElement) {
				textareaElement.style.height = 'auto';
			}
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			handleSubmit();
		}
	}

	function autoResize() {
		if (textareaElement) {
			textareaElement.style.height = 'auto';
			textareaElement.style.height = textareaElement.scrollHeight + 'px';
		}
	}
</script>

<div class="chat-input-container">
	<div class="input-wrapper">
		<textarea
			bind:this={textareaElement}
			bind:value={input}
			on:keydown={handleKeydown}
			on:input={autoResize}
			{disabled}
			{placeholder}
			rows="1"
			class="chat-textarea"
		/>
		<button
			class="send-button"
			on:click={handleSubmit}
			disabled={!input.trim() || disabled}
			aria-label="Send message"
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			>
				<line x1="22" y1="2" x2="11" y2="13"></line>
				<polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
			</svg>
		</button>
	</div>
	<div class="input-hint">
		Press <kbd>Enter</kbd> to send, <kbd>Shift+Enter</kbd> for new line
	</div>
</div>

<style>
	.chat-input-container {
		padding: 1rem;
		background: #1a1a1a;
		border-top: 1px solid #333;
	}

	.input-wrapper {
		display: flex;
		gap: 0.75rem;
		align-items: flex-end;
		background: #262626;
		border: 1px solid #404040;
		border-radius: 0.75rem;
		padding: 0.75rem;
		transition: border-color 0.2s;
	}

	.input-wrapper:focus-within {
		border-color: #2563eb;
	}

	.chat-textarea {
		flex: 1;
		background: transparent;
		border: none;
		outline: none;
		color: #e5e5e5;
		font-size: 0.9375rem;
		line-height: 1.5;
		resize: none;
		max-height: 200px;
		overflow-y: auto;
		font-family: inherit;
	}

	.chat-textarea::placeholder {
		color: #737373;
	}

	.chat-textarea:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.send-button {
		width: 36px;
		height: 36px;
		border-radius: 0.5rem;
		border: none;
		background: #2563eb;
		color: white;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: background 0.2s;
		flex-shrink: 0;
	}

	.send-button:hover:not(:disabled) {
		background: #1d4ed8;
	}

	.send-button:disabled {
		background: #404040;
		cursor: not-allowed;
		opacity: 0.5;
	}

	.send-button svg {
		width: 18px;
		height: 18px;
	}

	.input-hint {
		margin-top: 0.5rem;
		font-size: 0.75rem;
		color: #737373;
		text-align: center;
	}

	kbd {
		padding: 0.125rem 0.375rem;
		background: #333;
		border-radius: 0.25rem;
		font-family: monospace;
		font-size: 0.7rem;
	}

	/* Scrollbar styling */
	.chat-textarea::-webkit-scrollbar {
		width: 6px;
	}

	.chat-textarea::-webkit-scrollbar-track {
		background: transparent;
	}

	.chat-textarea::-webkit-scrollbar-thumb {
		background: #404040;
		border-radius: 3px;
	}
</style>
