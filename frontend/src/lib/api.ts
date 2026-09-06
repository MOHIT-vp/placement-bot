/**
 * API client to communicate with the FastAPI backend.
 * Base URL defaults to http://localhost:8000
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

/**
 * Fetch wrapper — no authentication for MVP.
 */
async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const headers: Record<string, string> = {
    ...((options.headers as Record<string, string>) || {}),
  };

  // Only set Content-Type for JSON requests (not FormData)
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

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
// Process API (Workflow)
// ------------------------------------------------------------------

/** Upload resume and start real LangGraph pipeline. Returns { run_id, status, message }. */
export async function uploadResume(formData: FormData): Promise<{
  run_id: string;
  status: string;
  message: string;
}> {
  return fetchAPI("/api/v1/process/upload", {
    method: "POST",
    body: formData,
  });
}

/** Poll workflow status by run_id. */
export async function getWorkflowStatus(runId: string): Promise<{
  run_id: string;
  status: string;
  current_step: string | null;
  student_id: string | null;
}> {
  return fetchAPI(`/api/v1/process/status/${runId}`);
}

// ------------------------------------------------------------------
// Dashboard API
// ------------------------------------------------------------------

/** Fetch student dashboard by run_id (unauthenticated MVP). */
export async function getDashboardByRunId(runId: string): Promise<any> {
  return fetchAPI(`/api/v1/dashboard/student/${runId}`);
}

/** Authenticated student dashboard (for future use with login). */
export async function getStudentDashboard() {
  return fetchAPI("/api/v1/dashboard/me");
}

// ------------------------------------------------------------------
// Officer / Approval API
// ------------------------------------------------------------------

/** Get the approval queue (unauthenticated MVP). */
export async function getApprovalQueue(): Promise<any> {
  return fetchAPI("/api/v1/approvals/queue/open");
}

/** Get the full report for a workflow run. */
export async function getRunReport(runId: string): Promise<any> {
  return fetchAPI(`/api/v1/approvals/${runId}/report`);
}

/** Submit an approval decision (approve/reject). */
export async function submitDecision(
  runId: string,
  decision: "approved" | "rejected",
  comments?: string
): Promise<any> {
  return fetchAPI(`/api/v1/approvals/${runId}/decide`, {
    method: "POST",
    body: JSON.stringify({ decision, comments }),
  });
}

/** Get officer queue with auth (original, for future use). */
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

// ------------------------------------------------------------------
// Chat API
// ------------------------------------------------------------------

export async function sendChatMessage(
  message: string,
  history: { role: string; content: string }[],
  runId?: string | null
): Promise<{ response: string }> {
  return fetchAPI("/api/v1/chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      history,
      run_id: runId || null,
    }),
  });
}
