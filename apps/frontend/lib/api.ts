import type {
  Answer,
  DocumentListResponse,
  DocumentResponse,
  ErrorField,
  ErrorPayload,
  MessageResponse,
  SummaryResponse,
  UserResponse,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  readonly status: number;
  readonly fields: ErrorField[];

  constructor(message: string, status: number, fields: ErrorField[] = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fields = fields;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  form?: FormData;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, form } = options;
  const headers: Record<string, string> = {};

  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: form ?? (body === undefined ? undefined : JSON.stringify(body)),
    credentials: "include",
  });

  const payload: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    const error = (payload as ErrorPayload | null)?.error;

    throw new ApiError(
      error?.message ?? `Request failed with status ${response.status}`,
      response.status,
      error?.fields ?? [],
    );
  }

  return payload as T;
}

function withQuery(path: string, params: Record<string, string | number | undefined>): string {
  const query = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      query.set(key, String(value));
    }
  }

  const encoded = query.toString();

  return encoded ? `${path}?${encoded}` : path;
}

export interface DocumentFilters {
  limit?: number;
  offset?: number;
  document_type?: string;
  tag?: string;
  search?: string;
}

export interface Credentials {
  email: string;
  password: string;
}

export const api = {
  register: (body: Credentials & { full_name?: string | null }) =>
    request<UserResponse>("/api/v1/auth/register", { method: "POST", body }),

  login: (body: Credentials) =>
    request<UserResponse>("/api/v1/auth/login", { method: "POST", body }),

  logout: () => request<MessageResponse>("/api/v1/auth/logout", { method: "POST" }),

  currentUser: () => request<UserResponse>("/api/v1/auth/me"),

  listDocuments: (filters: DocumentFilters = {}) =>
    request<DocumentListResponse>(
      withQuery("/api/v1/documents", filters as Record<string, string | number | undefined>),
    ),

  getDocument: (id: string) => request<DocumentResponse>(`/api/v1/documents/${id}`),

  uploadDocument: (form: FormData) =>
    request<DocumentResponse>("/api/v1/documents", { method: "POST", form }),

  deleteDocument: (id: string) =>
    request<MessageResponse>(`/api/v1/documents/${id}`, { method: "DELETE" }),

  summarizeDocument: (id: string) =>
    request<SummaryResponse>(`/api/v1/documents/${id}/summary`, { method: "POST" }),

  ask: (question: string) => request<Answer>("/api/v1/ask", { method: "POST", body: { question } }),
};
