// API Types for Simpleton Backend

export interface ChatMessage {
	role: 'system' | 'user' | 'assistant';
	content: string;
	timestamp?: string;
}

export interface Chat {
	id: string;
	title: string;
	messages: ChatMessage[];
	model: string;
	createdAt: string;
	updatedAt: string;
}

export interface GenerateRequest {
	prompt: string;
	model?: string;
	temperature?: number;
	max_tokens?: number;
	stream?: boolean;
}

export interface ChatRequest {
	messages: ChatMessage[];
	model?: string;
	temperature?: number;
	max_tokens?: number;
	stream?: boolean;
}

export interface ChatResponse {
	message: ChatMessage;
	model: string;
	created_at: string;
	done: boolean;
}

export interface Model {
	name: string;
	size?: number;
	modified_at?: string;
	digest?: string;
}

export interface ModelsResponse {
	models: Model[];
}

export interface RAGQueryRequest {
	query: string;
	collection?: string;
	top_k?: number;
	model?: string;
}

export interface RAGQueryResponse {
	query: string;
	answer: string;
	sources: Array<{
		chunk_id: string;
		content: string;
		score: number;
		metadata?: Record<string, any>;
	}>;
	model: string;
	collection: string;
}
