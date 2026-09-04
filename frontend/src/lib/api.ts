/**
 * API client to communicate with the FastAPI backend.
 * Base URL defaults to http://localhost:8000
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

/**
 * Standard fetch wrapper with auth header support.
 * For the MVP, we use a simple Authorization header with a dummy token.
 */
async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  // In a real app, retrieve this from localStorage or a context provider
  const token = "dummy_token_for_mvp"; 
  
  const headers = {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`,
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `API error: ${response.status}`);
  }

  return response.json();
}

// ------------------------------------------------------------------
// Dashboard API
// ------------------------------------------------------------------

export async function getStudentDashboard() {
  return fetchAPI("/api/v1/dashboard/me");
}

export async function getOfficerQueue() {
  return fetchAPI("/api/v1/dashboard/officer/queue");
}

// ------------------------------------------------------------------
// Admin API
// ------------------------------------------------------------------

export async function getSystemStats() {
  return fetchAPI("/api/v1/admin/stats");
}

export async function getDomainConfigs() {
  return fetchAPI("/api/v1/admin/domains");
}
