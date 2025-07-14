// Message types
export interface MessageSource {
  filename: string;
  chunk_index?: number;
}

export interface MessageMetadata {
  chunks_retrieved: number;
  model?: string;
}

export interface Message {
  type: 'user' | 'assistant' | 'system' | 'error';
  content: string;
  sources?: MessageSource[];
  metadata?: MessageMetadata;
  timestamp: Date;
  isLoading?: boolean;
}

// API Response types
export interface RAGQueryResponse {
  answer: string;
  sources: MessageSource[];
  metadata: MessageMetadata;
}

export interface FileUploadResponse {
  filename: string;
  chunks_created: number;
  message: string;
}

export interface FileUploadMetadata {
  uploaded_by: string;
  upload_time: string;
}

export interface ModelInfo {
  name: string;
  size: string;
  modified: string;
}

export interface ModelsResponse {
  models: ModelInfo[];
}

export interface ModelPullResponse {
  status: string;
  message: string;
}

// Component Props types
export interface ChatBoxProps {
  messages: Message[];
  onAddMessage: (message: Message) => void;
  onClearMessages: () => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}

export interface MessageListProps {
  messages: Message[];
}

export interface MessageProps {
  message: Message;
}

export interface InputFormProps {
  value: string;
  onChange: (value: string) => void;
  onSend: (message: string) => void;
  isLoading: boolean;
  placeholder: string;
}

export interface DocumentUploadProps {
  onUploadComplete?: (result: FileUploadResponse) => void;
}

// API Service types
export interface APIService {
  query: (message: string) => Promise<RAGQueryResponse>;
  uploadFile: (file: File, metadata: FileUploadMetadata) => Promise<FileUploadResponse>;
  getModels: () => Promise<ModelsResponse>;
  pullModel: (modelName: string) => Promise<ModelPullResponse>;
}

// Common utility types
export type MessageType = Message['type'];
export type LoadingState = boolean; 