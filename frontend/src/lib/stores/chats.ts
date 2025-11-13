// Chat Store - Manages chat state and local storage

import { writable, derived } from 'svelte/store';
import type { Chat, ChatMessage } from '../api/types';
import { v4 as uuidv4 } from 'uuid';

// Generate a simple UUID alternative without external dependency
function generateId(): string {
	return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

function createChatsStore() {
	// Initialize from localStorage if available
	const stored = typeof window !== 'undefined' ? localStorage.getItem('simpleton-chats') : null;
	const initial: Chat[] = stored ? JSON.parse(stored) : [];

	const { subscribe, set, update } = writable<Chat[]>(initial);

	// Save to localStorage whenever chats change
	if (typeof window !== 'undefined') {
		subscribe((chats) => {
			localStorage.setItem('simpleton-chats', JSON.stringify(chats));
		});
	}

	return {
		subscribe,
		set,
		update,

		createChat: (model: string = 'qwen2.5:7b') => {
			const newChat: Chat = {
				id: generateId(),
				title: 'New Chat',
				messages: [],
				model,
				createdAt: new Date().toISOString(),
				updatedAt: new Date().toISOString()
			};

			update((chats) => [newChat, ...chats]);
			return newChat.id;
		},

		deleteChat: (id: string) => {
			update((chats) => chats.filter((chat) => chat.id !== id));
		},

		addMessage: (chatId: string, message: ChatMessage) => {
			update((chats) =>
				chats.map((chat) => {
					if (chat.id === chatId) {
						const messages = [...chat.messages, message];
						return {
							...chat,
							messages,
							updatedAt: new Date().toISOString(),
							// Update title based on first user message
							title:
								messages.length === 1 && message.role === 'user'
									? message.content.slice(0, 50) + (message.content.length > 50 ? '...' : '')
									: chat.title
						};
					}
					return chat;
				})
			);
		},

		updateLastMessage: (chatId: string, content: string) => {
			update((chats) =>
				chats.map((chat) => {
					if (chat.id === chatId && chat.messages.length > 0) {
						const messages = [...chat.messages];
						messages[messages.length - 1] = {
							...messages[messages.length - 1],
							content
						};
						return {
							...chat,
							messages,
							updatedAt: new Date().toISOString()
						};
					}
					return chat;
				})
			);
		},

		clearChat: (chatId: string) => {
			update((chats) =>
				chats.map((chat) => {
					if (chat.id === chatId) {
						return {
							...chat,
							messages: [],
							title: 'New Chat',
							updatedAt: new Date().toISOString()
						};
					}
					return chat;
				})
			);
		}
	};
}

export const chats = createChatsStore();

// Current active chat ID
export const currentChatId = writable<string | null>(null);

// Derived store for the current chat
export const currentChat = derived(
	[chats, currentChatId],
	([$chats, $currentChatId]) => {
		if (!$currentChatId) return null;
		return $chats.find((chat) => chat.id === $currentChatId) || null;
	}
);
