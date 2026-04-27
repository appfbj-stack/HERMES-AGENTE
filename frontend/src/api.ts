import type {
  AdminTenant,
  Chat,
  CreateTenantPayload,
  Credit,
  CrmDashboard,
  CrmFollowup,
  CrmKanbanColumn,
  CrmSettings,
  CrmTag,
  Lead,
  LoginResponse,
  MeResponse,
  Message,
  Task,
  TenantModule,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function getToken() {
  return localStorage.getItem("hermes_token");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers || {}),
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || "Request failed");
  }

  return response.json() as Promise<T>;
}

export async function login(email: string, password: string) {
  return request<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function me() {
  return request<MeResponse>("/auth/me");
}

export async function getChats() {
  return request<Chat[]>("/chats");
}

export async function getMessages(chatId: number) {
  return request<Message[]>(`/messages/${chatId}`);
}

export async function sendMessage(chatId: number, content: string) {
  return request<Message>(`/messages/${chatId}`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export async function getLeads(params?: { status?: string; origem?: string; search?: string }) {
  const q = new URLSearchParams();
  if (params?.status) q.set("status", params.status);
  if (params?.origem) q.set("origem", params.origem);
  if (params?.search) q.set("search", params.search);
  const qs = q.toString() ? `?${q}` : "";
  return request<Lead[]>(`/leads${qs}`);
}

export async function getLead(id: number) {
  return request<Lead>(`/leads/${id}`);
}

export async function createLead(payload: Partial<Lead>) {
  return request<Lead>("/leads", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateLead(id: number, patch: Partial<Lead>) {
  return request<Lead>(`/leads/${id}`, { method: "PATCH", body: JSON.stringify(patch) });
}

export async function deleteLead(id: number) {
  return request<void>(`/leads/${id}`, { method: "DELETE" });
}

export async function getTasks(params?: { status?: string; priority?: string; lead_id?: number }) {
  const q = new URLSearchParams();
  if (params?.status) q.set("status", params.status);
  if (params?.priority) q.set("priority", params.priority);
  if (params?.lead_id) q.set("lead_id", String(params.lead_id));
  const qs = q.toString() ? `?${q}` : "";
  return request<Task[]>(`/tasks${qs}`);
}

export async function createTask(payload: Partial<Task>) {
  return request<Task>("/tasks", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateTask(id: number, patch: Partial<Task>) {
  return request<Task>(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(patch) });
}

export async function deleteTask(id: number) {
  return request<void>(`/tasks/${id}`, { method: "DELETE" });
}

export async function getCredits() {
  return request<Credit>("/credits");
}

export async function toggleAi(chatId: number, ai_paused: boolean) {
  return request<Chat>(`/chats/${chatId}/toggle-ai`, {
    method: "POST",
    body: JSON.stringify({ ai_paused }),
  });
}

// ========== ADMIN (super admin only) ==========

export async function getAdminTenants() {
  return request<AdminTenant[]>("/admin/tenants");
}

export type MasterBotInfo = {
  username: string | null;
  configured: boolean;
  panel_url: string;
};

export async function getMasterBotInfo() {
  return request<MasterBotInfo>("/admin/master-bot");
}

export async function createAdminTenant(payload: CreateTenantPayload) {
  return request<AdminTenant>("/admin/tenants", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateAdminTenant(tenantId: number, patch: Partial<CreateTenantPayload> & { active?: boolean }) {
  return request<AdminTenant>(`/admin/tenants/${tenantId}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export async function addAdminCredits(tenantId: number, amount: number) {
  return request<AdminTenant>(`/admin/tenants/${tenantId}/credits`, {
    method: "POST",
    body: JSON.stringify({ amount }),
  });
}

export async function deleteAdminTenant(tenantId: number) {
  return request<void>(`/admin/tenants/${tenantId}`, { method: "DELETE" });
}

export async function setAdminTenantModules(tenantId: number, modules: Partial<TenantModule>) {
  return request<AdminTenant>(`/admin/tenants/${tenantId}/modules`, {
    method: "PATCH",
    body: JSON.stringify(modules),
  });
}

// ========== CRM ==========

export async function getCrmModules() {
  return request<TenantModule>("/crm/modules");
}

export async function getCrmDashboard() {
  return request<CrmDashboard>("/crm/dashboard");
}

// Kanban
export async function getKanbanColumns() {
  return request<CrmKanbanColumn[]>("/crm/kanban");
}

export async function createKanbanColumn(payload: { name: string; color?: string; position?: number }) {
  return request<CrmKanbanColumn>("/crm/kanban", { method: "POST", body: JSON.stringify(payload) });
}

export async function deleteKanbanColumn(id: number) {
  return request<void>(`/crm/kanban/${id}`, { method: "DELETE" });
}

export async function moveLeadKanban(lead_id: number, column_id: number) {
  return request<{ ok: boolean }>("/crm/kanban/move", {
    method: "POST",
    body: JSON.stringify({ lead_id, column_id }),
  });
}

// Follow-ups
export async function getFollowups(params?: { lead_id?: number; status?: string }) {
  const q = new URLSearchParams();
  if (params?.lead_id) q.set("lead_id", String(params.lead_id));
  if (params?.status) q.set("status", params.status);
  const qs = q.toString() ? `?${q}` : "";
  return request<CrmFollowup[]>(`/crm/followups${qs}`);
}

export async function createFollowup(payload: {
  lead_id: number;
  titulo: string;
  descricao?: string;
  data_hora: string;
  canal?: string;
}) {
  return request<CrmFollowup>("/crm/followups", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateFollowup(id: number, patch: Partial<CrmFollowup>) {
  return request<CrmFollowup>(`/crm/followups/${id}`, { method: "PATCH", body: JSON.stringify(patch) });
}

export async function deleteFollowup(id: number) {
  return request<void>(`/crm/followups/${id}`, { method: "DELETE" });
}

// Tags
export async function getCrmTags() {
  return request<CrmTag[]>("/crm/tags");
}

export async function createCrmTag(payload: { name: string; color?: string }) {
  return request<CrmTag>("/crm/tags", { method: "POST", body: JSON.stringify(payload) });
}

export async function deleteCrmTag(id: number) {
  return request<void>(`/crm/tags/${id}`, { method: "DELETE" });
}

export async function addTagToLead(lead_id: number, tag_id: number) {
  return request<{ ok: boolean }>(`/crm/leads/${lead_id}/tags/${tag_id}`, { method: "POST" });
}

export async function removeTagFromLead(lead_id: number, tag_id: number) {
  return request<void>(`/crm/leads/${lead_id}/tags/${tag_id}`, { method: "DELETE" });
}

// Settings
export async function getCrmSettings() {
  return request<CrmSettings>("/crm/settings");
}

export async function updateCrmSettings(patch: Partial<CrmSettings>) {
  return request<CrmSettings>("/crm/settings", { method: "PATCH", body: JSON.stringify(patch) });
}

