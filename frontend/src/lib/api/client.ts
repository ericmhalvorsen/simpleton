// API Client for Simpleton Backend

import type {
	ChatRequest,
	ChatResponse,
	GenerateRequest,
	ModelsResponse,
	RAGQueryRequest,
	RAGQueryResponse
} from './types';

// Environment variables
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_API_KEY || '';

class APIClient {
	private baseURL: string;
	private apiKey: string;

	constructor(baseURL: string = API_BASE_URL, apiKey: string = API_KEY) {
		this.baseURL = baseURL;
		this.apiKey = apiKey;
	}

	private getHeaders(): HeadersInit {
		return {
			'Content-Type': 'application/json',
			'X-API-Key': this.apiKey
		};
	}

	async chat(request: ChatRequest): Promise<ChatResponse> {
		const response = await fetch(`${this.baseURL}/inference/chat`, {
			method: 'POST',
			headers: this.getHeaders(),
			body: JSON.stringify(request)
		});

		if (!response.ok) {
			throw new Error(`API Error: ${response.statusText}`);
		}

		return response.json();
	}

	async *chatStream(request: ChatRequest): AsyncGenerator<string, void, unknown> {
		const response = await fetch(`${this.baseURL}/inference/chat`, {
			method: 'POST',
			headers: this.getHeaders(),
			body: JSON.stringify({ ...request, stream: true })
		});

		if (!response.ok) {
			throw new Error(`API Error: ${response.statusText}`);
		}

		const reader = response.body?.getReader();
		if (!reader) {
			throw new Error('No response body');
		}

		const decoder = new TextDecoder();
		let buffer = '';

		while (true) {
			const { done, value } = await reader.read();
			if (done) break;

			buffer += decoder.decode(value, { stream: true });
			const lines = buffer.split('\n');
			buffer = lines.pop() || '';

			for (const line of lines) {
				if (line.trim()) {
					try {
						const data = JSON.parse(line);
						if (data.message?.content) {
							yield data.message.content;
						}
					} catch (e) {
						console.error('Error parsing stream chunk:', e);
					}
				}
			}
		}
	}

	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	async generate(request: GenerateRequest): Promise<any> {
		const response = await fetch(`${this.baseURL}/inference/generate`, {
			method: 'POST',
			headers: this.getHeaders(),
			body: JSON.stringify(request)
		});

		if (!response.ok) {
			throw new Error(`API Error: ${response.statusText}`);
		}

		return response.json();
	}

	async getModels(): Promise<ModelsResponse> {
		const response = await fetch(`${this.baseURL}/models`, {
			headers: this.getHeaders()
		});

		if (!response.ok) {
			throw new Error(`API Error: ${response.statusText}`);
		}

		return response.json();
	}

	async ragQuery(request: RAGQueryRequest): Promise<RAGQueryResponse> {
		const response = await fetch(`${this.baseURL}/rag/query`, {
			method: 'POST',
			headers: this.getHeaders(),
			body: JSON.stringify(request)
		});

		if (!response.ok) {
			throw new Error(`API Error: ${response.statusText}`);
		}

		return response.json();
	}

	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	async healthCheck(): Promise<any> {
		const response = await fetch(`${this.baseURL}/health`);
		return response.json();
	}
}

export const apiClient = new APIClient();
export default APIClient;
