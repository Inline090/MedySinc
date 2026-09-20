const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(message, status, fields = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fields = fields;
  }
}

async function request(path, { method = "GET", body, isForm = false } = {}) {
  const headers = {};

  if (body !== undefined && !isForm) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: isForm ? body : body === undefined ? undefined : JSON.stringify(body),
    credentials: "include",
  });

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    throw new ApiError(
      payload?.error?.message ?? `Request failed with status ${response.status}`,
      response.status,
      payload?.error?.fields ?? [],
    );
  }

  return payload;
}

function withQuery(path, params) {
  const query = new URLSearchParams(
    Object.entries(params).filter(([, value]) => value !== "" && value !== null && value !== undefined),
  ).toString();

  return query ? `${path}?${query}` : path;
}

export const api = {
  register: (body) => request("/api/v1/auth/register", { method: "POST", body }),
  login: (body) => request("/api/v1/auth/login", { method: "POST", body }),
  logout: () => request("/api/v1/auth/logout", { method: "POST" }),
  currentUser: () => request("/api/v1/auth/me"),
  listDocuments: (params = {}) => request(withQuery("/api/v1/documents", params)),
  getDocument: (id) => request(`/api/v1/documents/${id}`),
  uploadDocument: (formData) =>
    request("/api/v1/documents", { method: "POST", body: formData, isForm: true }),
  deleteDocument: (id) => request(`/api/v1/documents/${id}`, { method: "DELETE" }),
  summarizeDocument: (id) => request(`/api/v1/documents/${id}/summary`, { method: "POST" }),
  ask: (question) => request("/api/v1/ask", { method: "POST", body: { question } }),
};
