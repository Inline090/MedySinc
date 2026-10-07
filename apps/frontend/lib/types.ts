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
  chunk_index: number;
  similarity: number;
  excerpt: string;
}

export type AnswerStatus = "answered" | "uncertain" | "not_found";

export interface Answer {
  status: AnswerStatus;
  answer: string;
  sources: AnswerSource[];
  model: string | null;
  confidence: "Low" | "High" | null;
  cached: boolean;
}

export interface Medicine {
  id: string;
  document_id: string;
  document_title: string;
  hospital: string | null;
  medicine: string;
  dose: string | null;
  frequency: string | null;
  prescribed_on: string | null;
  notes: string | null;
}

export interface MedicineListResponse {
  medicines: Medicine[];
  total: number;
  limit: number;
  offset: number;
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
