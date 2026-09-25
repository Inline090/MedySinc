export type DocumentType =
  | "lab_report"
  | "prescription"
  | "discharge_summary"
  | "imaging"
  | "other";

export type ProcessingStatus = "pending" | "processing" | "processed" | "failed";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentSummary {
  id: string;
  title: string;
  document_type: DocumentType;
  tags: string[];
  notes: string | null;
  original_name: string;
  mime_type: string;
  size_bytes: number;
  processing_status: ProcessingStatus;
  created_at: string;
  updated_at: string;
}

export interface DocumentDetail extends DocumentSummary {
  extracted_text: string | null;
  summary: string | null;
  summary_model: string | null;
}

export interface AnswerSource {
  document_id: string;
  document_title: string;
  document_type: DocumentType;
  chunk_index: number;
  similarity: number;
  excerpt: string;
}

export interface Answer {
  answer: string;
  sources: AnswerSource[];
  model: string | null;
  cached: boolean;
}

export interface UserResponse {
  user: User;
}

export interface DocumentResponse {
  document: DocumentDetail;
}

export interface DocumentListResponse {
  documents: DocumentSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface SummaryResponse {
  summary: string;
  model: string;
}

export interface MessageResponse {
  message: string;
}

export interface ErrorField {
  field?: string;
  message?: string;
}

export interface ErrorPayload {
  error?: {
    message?: string;
    fields?: ErrorField[];
  };
}
