import type {
  AdminTenant,
  Chat,
  Credit,
  CrmActivityLog,
  CrmConversation,
  CrmDashboard,
  CrmFollowup,
  CrmKanbanBoard,
  CrmLead,
  CrmMessage,
  CrmSettings,
  CrmTag,
  CrmTask,
  CrmWhatsAppConnection,
  CrmWhatsAppStatus,
  CreateTenantPayload,
  Lead,
  LoginResponse,
  MeResponse,
  Message,
  Task,
  HermesAdminChatResponse,
  HermesAdminDashboard,
  AdminTask,
  AdminProject,
  AdminRoutine,
  AdminMemory,
  AdminActionLog,
  AdminSkill,
  SkillSuggestion,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

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

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export async function login(email: string, password: string, tenant_email?: string) {
  return request<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password, tenant_email: tenant_email || null }),
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

export async function getLeads() {
  return request<Lead[]>("/leads");
}

export async function createLead(payload: Partial<Lead>) {
  return request<Lead>("/leads", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateLead(leadId: number, payload: Partial<Lead>) {
  return request<Lead>(`/leads/${leadId}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export async function deleteLead(leadId: number) {
  return request<void>(`/leads/${leadId}`, { method: "DELETE" });
}

export async function getTasks() {
  return request<Task[]>("/tasks");
}

export async function createTask(payload: Partial<Task>) {
  return request<Task>("/tasks", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateTask(taskId: number, payload: Partial<Task>) {
  return request<Task>(`/tasks/${taskId}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export async function deleteTask(taskId: number) {
  return request<void>(`/tasks/${taskId}`, { method: "DELETE" });
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

export async function getCrmDashboard() {
  return request<CrmDashboard>("/crm/dashboard");
}

export async function getKanbanColumns() {
  const board = await getCrmKanban();
  return board.columns;
}

export async function createKanbanColumn(payload: { name: string; color?: string; position?: number }) {
  return request("/crm/kanban", { method: "POST", body: JSON.stringify(payload) });
}

export async function getCrmLeads(params?: Record<string, string>) {
  const search = params ? `?${new URLSearchParams(params).toString()}` : "";
  return request<CrmLead[]>(`/crm/leads${search}`);
}

export async function createCrmLead(payload: {
  name: string;
  phone?: string;
  email?: string;
  origin?: string;
  status?: string;
  responsible_user_id?: number | null;
  notes?: string;
  tag_ids?: number[];
}) {
  return request<CrmLead>("/crm/leads", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateCrmLead(
  leadId: number,
  payload: {
    name?: string;
    phone?: string;
    email?: string;
    origin?: string;
    status?: string;
    responsible_user_id?: number | null;
    notes?: string;
    tag_ids?: number[];
  },
) {
  return request<CrmLead>(`/crm/leads/${leadId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteCrmLead(leadId: number) {
  return request<void>(`/crm/leads/${leadId}`, {
    method: "DELETE",
  });
}

export async function getCrmLeadActivity(leadId: number) {
  return request<CrmActivityLog[]>(`/crm/leads/${leadId}/activity`);
}

export async function getCrmConversations() {
  return request<CrmConversation[]>("/crm/conversations");
}

export async function getCrmMessages(conversationId: number) {
  return request<CrmMessage[]>(`/crm/messages?conversation_id=${conversationId}`);
}

export async function updateCrmConversationState(
  conversationId: number,
  payload: { assigned_user_id?: number | null; ai_enabled?: boolean; status?: string },
) {
  return request<CrmConversation>(`/crm/conversations/${conversationId}/state`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function sendCrmConversationMessage(conversationId: number, content: string) {
  return request<CrmMessage>(`/crm/conversations/${conversationId}/messages`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export async function getCrmKanban() {
  return request<CrmKanbanBoard>("/crm/kanban");
}

export async function moveCrmKanban(lead_id: number, status: string) {
  return request<CrmLead>("/crm/kanban/move", {
    method: "POST",
    body: JSON.stringify({ lead_id, status }),
  });
}

export async function moveLeadKanban(lead_id: number, column_id: number) {
  const columns = await getKanbanColumns();
  const column = columns.find((item: any) => item.id === column_id);
  if (!column) throw new Error("Kanban column not found");
  return moveCrmKanban(lead_id, column.name);
}

export async function getCrmFollowups(onlyToday = false) {
  return request<CrmFollowup[]>(`/crm/followups?only_today=${onlyToday}`);
}

export async function createCrmFollowup(payload: {
  lead_id: number;
  title: string;
  description?: string;
  due_at: string;
  status?: string;
  channel?: string;
  responsible_user_id?: number | null;
}) {
  return request<CrmFollowup>("/crm/followups", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export const getFollowups = getCrmFollowups;
export const createFollowup = createCrmFollowup;
export const updateFollowup = updateCrmFollowup;
export const deleteFollowup = deleteCrmFollowup;

export async function updateCrmFollowup(
  followupId: number,
  payload: {
    title?: string;
    description?: string;
    due_at?: string;
    status?: string;
    channel?: string;
    responsible_user_id?: number | null;
  },
) {
  return request<CrmFollowup>(`/crm/followups/${followupId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteCrmFollowup(followupId: number) {
  return request<void>(`/crm/followups/${followupId}`, {
    method: "DELETE",
  });
}

export async function getCrmTasks() {
  return request<CrmTask[]>("/crm/tasks");
}

export async function createCrmTask(payload: {
  title: string;
  description?: string;
  responsible_user_id?: number | null;
  due_at?: string | null;
  status?: string;
  priority?: string;
  lead_id?: number | null;
}) {
  return request<CrmTask>("/crm/tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateCrmTask(
  taskId: number,
  payload: {
    title?: string;
    description?: string;
    responsible_user_id?: number | null;
    due_at?: string | null;
    status?: string;
    priority?: string;
    lead_id?: number | null;
  },
) {
  return request<CrmTask>(`/crm/tasks/${taskId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteCrmTask(taskId: number) {
  return request<void>(`/crm/tasks/${taskId}`, {
    method: "DELETE",
  });
}

export async function getCrmTags() {
  return request<CrmTag[]>("/crm/tags");
}

export async function getCrmSettings() {
  return request<CrmSettings>("/crm/settings");
}

export async function createCrmTag(payload: { name: string; color?: string | null }) {
  return request<CrmTag>("/crm/tags", { method: "POST", body: JSON.stringify(payload) });
}

export async function deleteCrmTag(tagId: number) {
  return request<void>(`/crm/tags/${tagId}`, { method: "DELETE" });
}

export async function updateCrmSettings(payload: {
  column_names?: string[];
  status_options?: string[];
  tags?: string[];
  initial_auto_message?: string;
  business_hours?: Record<string, unknown>;
  hermes_enabled?: boolean;
}) {
  return request<CrmSettings>("/crm/settings", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function getCrmWhatsAppConnection() {
  return request<CrmWhatsAppConnection | null>("/crm/whatsapp");
}

export async function upsertCrmWhatsAppConnection(payload: {
  provider: string;
  instance_name: string;
  api_base_url?: string | null;
  api_key?: string | null;
  webhook_url?: string | null;
}) {
  return request<CrmWhatsAppConnection>("/crm/whatsapp", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function connectCrmWhatsApp() {
  return request<CrmWhatsAppStatus>("/crm/whatsapp/connect", {
    method: "POST",
  });
}

export async function getCrmWhatsAppStatus() {
  return request<CrmWhatsAppStatus>("/crm/whatsapp/status");
}

export async function getCrmWhatsAppQrCode() {
  return request<CrmWhatsAppStatus>("/crm/whatsapp/qrcode");
}

export async function disconnectCrmWhatsApp() {
  return request<{ status: string }>("/crm/whatsapp/disconnect", {
    method: "POST",
  });
}

export async function getAdminTenants() {
  return request<AdminTenant[]>("/admin/tenants");
}

export async function updateAdminTenantModules(tenantId: number, payload: Partial<{ crm: boolean; whatsapp: boolean; kanban: boolean; agenda: boolean; instagram: boolean; youtube: boolean; content_publisher: boolean }>) {
  return request<AdminTenant>(`/admin/tenants/${tenantId}/modules`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
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
  return request<AdminTenant>("/admin/tenants", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateAdminTenant(tenantId: number, payload: Record<string, unknown>) {
  return request<AdminTenant>(`/admin/tenants/${tenantId}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export async function addAdminCredits(tenantId: number, amount: number) {
  return request<AdminTenant>(`/admin/tenants/${tenantId}/credits`, { method: "POST", body: JSON.stringify({ amount }) });
}

export async function deleteAdminTenant(tenantId: number) {
  return request<void>(`/admin/tenants/${tenantId}`, { method: "DELETE" });
}

export const setAdminTenantModules = updateAdminTenantModules;


export async function getTenantModules() {
  return request<{ crm: boolean; whatsapp: boolean; kanban: boolean; agenda: boolean; instagram: boolean; youtube: boolean }>("/auth/modules");
}


export async function hermesAdminChat(message: string) {
  return request<HermesAdminChatResponse>('/admin/hermes/chat', {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}

export async function getHermesAdminDashboard() {
  return request<HermesAdminDashboard>('/admin/hermes/dashboard');
}

export async function getAdminTasks(status?: string, limit = 50, offset = 0) {
  const search = status ? `?status=${status}&limit=${limit}&offset=${offset}` : `?limit=${limit}&offset=${offset}`;
  const data = await request<{ tasks: AdminTask[]; total: number }>(`/admin/hermes/tasks${search}`);
  return { tasks: data.tasks, total: data.total };
}

export async function createAdminTask(payload: {
  title: string;
  description?: string;
  priority?: string;
  assigned_user_id?: number;
  related_tenant_id?: number;
  due_date?: string;
}) {
  return request<AdminTask>('/admin/hermes/tasks', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateAdminTask(taskId: number, payload: Partial<AdminTask>) {
  return request<AdminTask>(`/admin/hermes/tasks/${taskId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function deleteAdminTask(taskId: number) {
  return request<void>(`/admin/hermes/tasks/${taskId}`, {
    method: 'DELETE',
  });
}


export async function getAdminProjects(status?: string, limit = 50, offset = 0) {
  const search = status ? `?status=${status}&limit=${limit}&offset=${offset}` : `?limit=${limit}&offset=${offset}`;
  const data = await request<{ projects: AdminProject[]; total: number }>(`/admin/hermes/projects${search}`);
  return { projects: data.projects, total: data.total };
}

export async function createAdminProject(payload: {
  name: string;
  description?: string;
  priority?: string;
  due_date?: string;
}) {
  return request<AdminProject>('/admin/hermes/projects', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateAdminProject(projectId: number, payload: Partial<AdminProject>) {
  return request<AdminProject>(`/admin/hermes/projects/${projectId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function deleteAdminProject(projectId: number) {
  return request<void>(`/admin/hermes/projects/${projectId}`, {
    method: 'DELETE',
  });
}


export async function getAdminRoutines(limit = 50, offset = 0) {
  const search = `?limit=${limit}&offset=${offset}`;
  const data = await request<{ routines: AdminRoutine[]; total: number }>(`/admin/hermes/routines${search}`);
  return { routines: data.routines, total: data.total };
}

export async function createAdminRoutine(payload: {
  name: string;
  description?: string;
  schedule_type: string;
  schedule_value: number;
}) {
  return request<AdminRoutine>('/admin/hermes/routines', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateAdminRoutine(routineId: number, payload: Partial<AdminRoutine>) {
  return request<AdminRoutine>(`/admin/hermes/routines/${routineId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function deleteAdminRoutine(routineId: number) {
  return request<void>(`/admin/hermes/routines/${routineId}`, {
    method: 'DELETE',
  });
}


export async function getAdminMemory(category?: string, key?: string, limit = 100, offset = 0) {
  const params = new URLSearchParams({ limit: limit.toString(), offset: offset.toString() });
  if (category) params.set('category', category);
  if (key) params.set('key', key);
  const data = await request<{ memories: AdminMemory[]; total: number }>(`/admin/hermes/memory?${params.toString()}`);
  return { memories: data.memories, total: data.total };
}

export async function createAdminMemory(payload: {
  category: string;
  key: string;
  value: string;
  metadata?: string;
}) {
  return request<AdminMemory>('/admin/hermes/memory', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateAdminMemory(memoryId: number, payload: Partial<AdminMemory>) {
  return request<AdminMemory>(`/admin/hermes/memory/${memoryId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function deleteAdminMemory(memoryId: number) {
  return request<void>(`/admin/hermes/memory/${memoryId}`, {
    method: 'DELETE',
  });
}


export async function getAdminActionLogs(limit = 100, offset = 0) {
  const search = `?limit=${limit}&offset=${offset}`;
  const data = await request<{ logs: AdminActionLog[]; total: number }>(`/admin/hermes/logs${search}`);
  return { logs: data.logs, total: data.total };
}


export async function getAdminSkills(activeOnly = false, limit = 50, offset = 0) {
  const search = `?active_only=${activeOnly}&limit=${limit}&offset=${offset}`;
  const data = await request<{ skills: AdminSkill[]; total: number }>(`/admin/hermes/skills${search}`);
  return { skills: data.skills, total: data.total };
}

export async function createAdminSkill(payload: {
  name: string;
  description?: string;
  trigger_type?: string;
  trigger_value?: string;
  instructions: string;
  expected_result?: string;
  active?: boolean;
}) {
  return request<AdminSkill>('/admin/hermes/skills', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateAdminSkill(skillId: number, payload: Partial<AdminSkill>) {
  return request<AdminSkill>(`/admin/hermes/skills/${skillId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function deleteAdminSkill(skillId: number) {
  return request<void>(`/admin/hermes/skills/${skillId}`, {
    method: 'DELETE',
  });
}

export async function runAdminSkill(skillId: number, parameters?: Record<string, unknown>) {
  return request<{
    skill_id: number;
    skill_name: string;
    status: string;
    result: unknown;
    error: string | null;
    execution_time: number;
    executed_at: string;
  }>(`/admin/hermes/skills/${skillId}/run`, {
    method: 'POST',
    body: JSON.stringify({ parameters }),
  });
}

export async function suggestAdminSkill(message: string) {
  return request<SkillSuggestion>('/admin/hermes/skills/suggest', {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}

