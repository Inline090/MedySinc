import type {
  Answer,
  DocumentListResponse,
  DocumentResponse,
  ErrorField,
  ErrorPayload,
  MedicineListResponse,
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

const NO_REFRESH_PATHS = new Set([
  "/api/v1/auth/login",
  "/api/v1/auth/register",
  "/api/v1/auth/refresh",
  "/api/v1/auth/logout",
]);

let refreshing: Promise<boolean> | null = null;

function onAuthPage(): boolean {
  return window.location.pathname.startsWith("/sign-in") || window.location.pathname.startsWith("/sign-up");
}

function refreshSession(): Promise<boolean> {
  if (refreshing === null) {
    refreshing = fetch(`${API_URL}/api/v1/auth/refresh`, {
      method: "POST",
      credentials: "include",
    })
      .then((response) => response.ok)
      .catch(() => false)
      .finally(() => {
        refreshing = null;
      });
  }

  return refreshing;
}

async function send(path: string, options: RequestOptions): Promise<Response> {
  const { method = "GET", body, form } = options;
  const headers: Record<string, string> = {};

  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  return fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: form ?? (body === undefined ? undefined : JSON.stringify(body)),
    credentials: "include",
  });
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  let response: Response;

  try {
    response = await send(path, options);
  } catch {
    throw new ApiError("Could not reach the API. Is it running?", 0);
  }

  // If we get a 401 error, try refreshing the token once and retry the request.
  if (response.status === 401 && !NO_REFRESH_PATHS.has(path)) {
    if (await refreshSession()) {
      response = await send(path, options);
    } else if (!onAuthPage()) {
      window.location.assign("/sign-in");
    }
  }

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

  // Just a string URL. The browser downloads it directly instead of loading the bytes into memory.
  documentFileUrl: (id: string) => `${API_URL}/api/v1/documents/${id}/file`,

  updateDocument: (id: string, body: { title?: string; notes?: string }) =>
    request<DocumentResponse>(`/api/v1/documents/${id}`, { method: "PATCH", body }),

  uploadDocument: (form: FormData) =>
    request<DocumentResponse>("/api/v1/documents", { method: "POST", form }),

  deleteDocument: (id: string) =>
    request<MessageResponse>(`/api/v1/documents/${id}`, { method: "DELETE" }),

  summarizeDocument: (id: string) =>
    request<SummaryResponse>(`/api/v1/documents/${id}/summary`, { method: "POST" }),

  ask: (question: string) => request<Answer>("/api/v1/ask", { method: "POST", body: { question } }),

  listMedications: (filters: DocumentFilters = {}) =>
    request<MedicineListResponse>(
      withQuery("/api/v1/medications", filters as Record<string, string | number | undefined>),
    ),
};
