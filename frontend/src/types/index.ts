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

// Job Management types
export interface JobInfo {
  job_id: string;
  job_type: 'text_ingestion' | 'file_ingestion' | 'directory_ingestion' | 'batch_ingestion';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  created_at: string;
  started_at?: string;
  completed_at?: string;
  progress: number; // 0.0 to 1.0
  message: string;
  error_message?: string;
  chunks_created: number;
  total_items: number;
  processed_items: number;
  metadata: Record<string, any>;
}

export interface JobListResponse {
  jobs: JobInfo[];
  total_count: number;
}

export interface JobStatsResponse {
  total_jobs: number;
  pending: number;
  running: number;
  completed: number;
  failed: number;
  cancelled: number;
  total_chunks_created: number;
}

export interface AsyncJobResponse {
  job_id: string;
  job_type: string;
  status: string;
  created_at: string;
  message: string;
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

// Plugin types
export interface PluginInfo {
  name: string;
  display_name: string;
  description: string;
  version: string;
  author: string;
  capabilities: string[];
  enabled: boolean;
  initialized: boolean;
  total_sources: number;
}

export interface PluginListResponse {
  plugins: PluginInfo[];
}

export interface PluginConfig {
  enabled: boolean;
  config: Record<string, any>;
}

export interface GlobalSettings {
  chunk_size: number;
  chunk_overlap: number;
  batch_size: number;
  auto_sync: boolean;
  sync_interval_hours: number;
}

export interface FullConfig {
  version: string;
  plugins: Record<string, PluginConfig>;
  global_settings: GlobalSettings;
}

export interface IngestionRequest {
  source_id: string;
  full_sync: boolean;
}

export interface IngestionResponse {
  job_id: string;
  plugin_name: string;
  source_id: string;
  sync_type: string;
}

export interface JobStatus {
  id: string;
  plugin_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  started_at?: string;
  completed_at?: string;
  total_documents: number;
  processed_documents: number;
  failed_documents: number;
  error_message?: string;
  metadata: Record<string, any>;
}

export interface SourceInfo {
  id: string;
  name: string;
  type: string;
  config: Record<string, any>;
  last_synced?: string;
  sync_mode: string;
  enabled: boolean;
}

export interface SourceListResponse {
  sources: SourceInfo[];
}

export interface GitHubRepository {
  id: string;
  owner: string;
  repo: string;
  branch: string;
  paths?: string[];
  exclude_patterns?: string[];
  last_synced?: string;
  sync_mode: 'full' | 'incremental';
}

// Component Props types
export interface ChatBoxProps {
  messages: Message[];
  onAddMessage: (message: Message) => void;
  onUpdateMessage: (message: Message) => void;
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

export interface JobManagerProps {
  className?: string;
}

// API Service types
export interface APIService {
  query: (message: string) => AsyncGenerator<string>;
  uploadFile: (file: File, metadata: FileUploadMetadata) => Promise<FileUploadResponse>;
}

// Common utility types
export type MessageType = Message['type'];
export type LoadingState = boolean;