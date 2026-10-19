/**
 * frontend/src/api.js
 * Fetch wrapper for VirtuLab backend API (/api).
 * Automatically injects Bearer token, parses {error}, throws {status, error, extra},
 * and clears session on 401.
 */

export class ApiError extends Error {
  constructor(status, error, extra = {}) {
    super(error);
    this.name = "ApiError";
    this.status = status;
    this.error = error;
    this.extra = extra;
  }
}

/**
 * Clear session credentials from local storage and notify listeners.
 */
export function clearStoredSession() {
  localStorage.removeItem("vl_token");
  localStorage.removeItem("vl_me");
  window.dispatchEvent(new CustomEvent("vl:session_cleared"));
}

/**
 * Retrieve the active auth token from localStorage.
 */
export function getStoredToken() {
  return localStorage.getItem("vl_token");
}

/**
 * Maps any error object or reason code to a translated message in the i18n catalogue.
 * Falls back to errors.generic_error if the code is unknown.
 */
export function getTranslatedError(t, err) {
  if (!err) return "";
  const code = typeof err === "string" ? err : err.error;
  if (!code) return t("errors.generic_error");

  const key = `errors.${code}`;
  const translated = t(key);
  if (translated === key || !translated) {
    return t("errors.generic_error");
  }
  return translated;
}

/**
 * Central fetch wrapper for all API calls.
 */
export async function api(endpoint, options = {}) {
  const url = endpoint.startsWith("http")
    ? endpoint
    : endpoint.startsWith("/api")
    ? endpoint
    : `/api${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;

  const headers = new Headers(options.headers || {});

  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  // Inject Bearer token if not explicitly excluded
  const token = getStoredToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let body = options.body;
  if (body && typeof body === "object" && !(body instanceof FormData)) {
    if (!headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    body = JSON.stringify(body);
  }

  let res;
  try {
    res = await fetch(url, {
      ...options,
      headers,
      body,
    });
  } catch (netErr) {
    throw new ApiError(0, "network_error", { message: netErr.message });
  }

  // Handle 401 Unauthorized: clear session
  if (res.status === 401) {
    clearStoredSession();
  }

  let data = null;
  const contentType = res.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    try {
      data = await res.json();
    } catch {
      data = null;
    }
  }

  if (!res.ok) {
    const errorCode =
      data && data.error
        ? data.error
        : res.status === 429
        ? "rate_limited"
        : res.status === 401
        ? "not_authenticated"
        : "generic_error";

    throw new ApiError(res.status, errorCode, data || {});
  }

  return data;
}

// Convenience helpers
api.get = (url, options) => api(url, { ...options, method: "GET" });
api.post = (url, body, options) => api(url, { ...options, method: "POST", body });
api.patch = (url, body, options) => api(url, { ...options, method: "PATCH", body });
api.put = (url, body, options) => api(url, { ...options, method: "PUT", body });
api.delete = (url, options) => api(url, { ...options, method: "DELETE" });

export default api;
