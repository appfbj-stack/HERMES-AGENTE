export type Chat = {
  id: number;
  channel: string;
  contact_name: string | null;
  contact_phone: string | null;
  chat_external_id: string;
  last_message: string | null;
  last_message_at: string | null;
  status: string;
  ai_paused: boolean;
  assigned_user_id: number | null;
  created_at: string;
};

export type Message = {
  id: number;
  chat_id: number;
  sender_type: "user" | "assistant" | "human";
  content: string;
  created_at: string;
};

export type Lead = {
  id: number;
  tenant_id?: number;
  name: string;
  phone: string | null;
  email?: string | null;
  interest: string | null;
  origem?: string;
  status: string;
  observacoes?: string | null;
  kanban_column_id?: number | null;
  created_at: string;
};

export type CrmTag = {
  id: number;
  name: string;
  color: string;
  created_at: string;
  updated_at: string;
};

export type CrmLead = {
  id: number;
  tenant_id: number;
  name: string;
  phone: string | null;
  email: string | null;
  origin: string;
  status: string;
  responsible_user_id: number | null;
  notes: string | null;
  interest?: string | null;
  last_contact_at: string | null;
  kanban_column_id?: number | null;
  created_at: string;
  updated_at: string;
  tags: CrmTag[];
};

export type CrmConversation = {
  id: number;
  lead_id: number | null;
  chat_id: number | null;
  channel: string;
  external_id: string;
  contact_name: string | null;
  contact_phone: string | null;
  status: string;
  ai_enabled: boolean;
  assigned_user_id: number | null;
  last_message: string | null;
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
};

export type CrmMessage = {
  id: number;
  conversation_id: number;
  legacy_message_id: number | null;
  sender_type: string;
  channel: string;
  content: string;
  created_at: string;
  updated_at: string;
};

export type CrmActivityLog = {
  id: number;
  tenant_id: number;
  lead_id: number | null;
  conversation_id: number | null;
  action: string;
  description: string | null;
  metadata_json: string | null;
  created_at: string;
  updated_at: string;
};

export type CrmKanbanColumn = {
  id: number;
  name: string;
  position: number;
  color: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
};

export type CrmKanbanCard = {
  lead: CrmLead;
  conversation: CrmConversation | null;
};

export type CrmKanbanBoard = {
  columns: CrmKanbanColumn[];
  cards: Record<string, CrmKanbanCard[]>;
};

export type CrmFollowup = {
  id: number;
  tenant_id: number;
  lead_id: number;
  title: string;
  titulo?: string;
  description: string | null;
  descricao?: string | null;
  due_at: string;
  data_hora?: string;
  status: string;
  channel: string;
  canal?: string;
  responsible_user_id: number | null;
  created_at: string;
  updated_at: string;
};

export type CrmTask = {
  id: number;
  tenant_id: number;
  title: string;
  description: string | null;
  responsible_user_id: number | null;
  due_at: string | null;
  status: string;
  priority: string;
  lead_id: number | null;
  created_at: string;
  updated_at: string;
};


export type AgentReminder = {
  id: number;
  tenant_id: number;
  chat_id: number | null;
  title: string;
  description: string | null;
  remind_at: string;
  status: string;
  recurrence_rule: string | null;
  sent_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AgentAppointment = {
  id: number;
  tenant_id: number;
  chat_id: number | null;
  title: string;
  description: string | null;
  scheduled_at: string;
  location: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type CrmDashboard = {
  total_leads: number;
  new_leads: number;
  open_conversations: number;
  today_followups: number;
  active_conversations: number;
  closed_won: number;
  messages_used_month: number;
  current_plan: string;
};

export type CrmSettings = {
  id: number;
  tenant_id: number;
  status_options: string[];
  tags: string[];
  initial_auto_message: string | null;
  mensagem_inicial?: string | null;
  business_hours: Record<string, unknown>;
  hermes_enabled: boolean;
  horario_inicio?: string;
  horario_fim?: string;
  hermes_ativo?: boolean;
  notificar_followup_telegram?: boolean;
  created_at: string;
  updated_at: string;
};

export type CrmWhatsAppConnection = {
  id: number;
  tenant_id: number;
  provider: string;
  instance_name: string;
  api_base_url: string | null;
  webhook_url: string | null;
  status: string;
  connected_phone: string | null;
  qr_code_base64: string | null;
  last_error: string | null;
  last_webhook_event: string | null;
  last_webhook_payload: string | null;
  last_webhook_at: string | null;
  created_at: string;
  updated_at: string;
};

export type CrmWhatsAppStatus = {
  status: string;
  connected_phone: string | null;
  qr_code_base64: string | null;
  raw: Record<string, unknown> | unknown[] | null;
};

export type SocialIntegrationAccount = {
  id: number;
  provider: string;
  username: string | null;
  display_name: string | null;
  avatar_url: string | null;
  status: string;
  created_at: string;
  last_webhook_at: string | null;
};

export type SocialPost = {
  id: number;
  title: string;
  content: string;
  media_type: string;
  media_url: string;
  thumbnail_url: string | null;
  hashtags: string | null;
  caption: string | null;
  platforms: string[];
  scheduled_at: string | null;
  published_at: string | null;
  status: string;
  instagram_post_id: string | null;
  instagram_media_url: string | null;
  youtube_video_id: string | null;
  youtube_video_url: string | null;
  error_message: string | null;
  created_at: string;
};

export type SocialIntegrationStats = {
  accounts: {
    total: number;
    active: number;
    instagram: number;
    youtube: number;
  };
  posts: {
    total: number;
    published: number;
    scheduled: number;
    draft: number;
  };
};

export type SocialOAuthStartResponse = {
  oauth_url: string;
  state: string;
};

export type AdminTenant = {
  id: number;
  name: string;
  email: string;
  plan: string;
  active: boolean;
  niche?: string | null;
  system_prompt?: string | null;
  telegram_bot_token?: string | null;
  telegram_bot_username?: string | null;
  created_at: string;
  credits_total?: number;
  credits_used?: number;
  credits_remaining?: number;
  crm_enabled: boolean;
  whatsapp_enabled: boolean;
  whatsapp_evolution_enabled: boolean;
  kanban_enabled: boolean;
  agenda_enabled: boolean;
  followup_enabled: boolean;
  instagram_enabled: boolean;
  youtube_enabled: boolean;
  content_publisher_enabled: boolean;
};

export type CreateTenantPayload = {
  name: string;
  email: string;
  plan: string;
  niche: string | null;
  system_prompt: string | null;
  telegram_bot_token: string | null;
  telegram_bot_username: string | null;
  credits: number;
  user_name: string;
  user_email: string;
  user_password: string;
};

export type NicheTemplate = {
  id: string;
  label: string;
  emoji: string;
  defaultPlan: "starter" | "pro" | "enterprise";
  defaultCredits: number;
  systemPrompt: string;
};

export type Task = {
  id: number;
  title: string;
  description: string | null;
  due_date: string | null;
  status: string;
  created_at: string;
};

export type Credit = {
  total: number;
  used: number;
  remaining: number;
};

export type ClientProfile = {
  tenant_id: number;
  tipo_negocio: string | null;
  objetivo: string | null;
  horario_funcionamento: string | null;
  preferencias: string | null;
  nivel_automacao: string;
  created_at: string;
  updated_at: string;
};

export type ClientSkill = {
  id: number;
  tenant_id: number;
  nome_skill: string;
  descricao: string | null;
  ativa: boolean;
  configuracao: string | null;
  created_at: string;
  updated_at: string;
};

export type ClientSuggestion = {
  skill_key: string;
  message: string;
  suggested_at: string | null;
  active: boolean;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
};

export type TenantModules = {
  crm: boolean;
  whatsapp: boolean;
  whatsapp_evolution: boolean;
  kanban: boolean;
  agenda: boolean;
  followup: boolean;
  instagram: boolean;
  youtube: boolean;
  content_publisher: boolean;
};

export type MeResponse = {
  user: {
    id: number;
    tenant_id: number;
    name: string;
    email: string;
    role: string;
    is_super_admin: boolean;
  };
  tenant: {
    id: number;
    name: string;
    email: string;
    plan: string;
    active: boolean;
  };
  modules: TenantModules;
};


export type HermesAdminChatResponse = {
  response: string;
  message?: string;
  dashboard?: HermesAdminDashboard | null;
  suggested_skills?: SkillSuggestion[] | null;
  actions: string[];
  context: Record<string, unknown>;
};

export type AdminTask = {
  id: number;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  assigned_user_id: number | null;
  related_tenant_id: number | null;
  due_date: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AdminProject = {
  id: number;
  name: string;
  description: string | null;
  status: string;
  priority: string;
  due_date: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AdminRoutine = {
  id: number;
  name: string;
  description: string | null;
  schedule_type: string;
  schedule_value: number;
  schedule?: string;
  last_run_at: string | null;
  next_run_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type AdminMemory = {
  id: number;
  category: string;
  key: string;
  value: string;
  metadata: string | null;
  created_at: string;
  updated_at: string;
};

export type AdminActionLog = {
  id: number;
  action: string;
  action_type?: string;
  entity_type: string;
  entity_id: number | null;
  details: string | null;
  description?: string;
  performed_by_user_id: number | null;
  tenant_id: number | null;
  created_at: string;
};

export type HermesAdminDashboard = {
  active_tenants: number;
  blocked_tenants: number;
  pending_payments: number;
  messages_used_month: number;
  open_tasks: number;
  active_projects: number;
  active_routines: number;
  total_revenue: number;
};


export type AdminSkill = {
  id: number;
  name: string;
  description: string | null;
  trigger_type: string;
  trigger_value: string | null;
  instructions: string;
  expected_result: string | null;
  active: boolean;
  last_run_at: string | null;
  last_run_result: string | null;
  last_run_status: string | null;
  created_at: string;
  updated_at: string;
};

export type SkillSuggestion = {
  suggestion: {
    name: string;
    description: string | null;
    trigger_type: string;
    trigger_value: string | null;
    instructions: string;
    expected_result: string | null;
    active: boolean;
  };
  confidence: number;
  reason: string;
};

export type Priority = "baixa" | "media" | "alta";
