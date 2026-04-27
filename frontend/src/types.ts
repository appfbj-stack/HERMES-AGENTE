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
  name: string;
  phone: string | null;
  interest: string | null;
  status: string;
  created_at: string;
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

export type LoginResponse = {
  access_token: string;
  token_type: string;
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
    niche: string | null;
    system_prompt: string | null;
    telegram_bot_username: string | null;
  };
};

export type AdminTenant = {
  id: number;
  name: string;
  email: string;
  plan: string;
  active: boolean;
  niche: string | null;
  system_prompt: string | null;
  telegram_bot_token: string | null;
  telegram_bot_username: string | null;
  created_at: string;
  credits_total: number;
  credits_used: number;
  credits_remaining: number;
  crm_enabled: boolean;
};

export type TenantModule = {
  tenant_id: number;
  crm: boolean;
  whatsapp: boolean;
};

export type CrmDashboard = {
  total_leads: number;
  leads_novos: number;
  atendimentos_abertos: number;
  followups_hoje: number;
  conversas_ativas: number;
  fechamentos: number;
  mensagens_usadas_mes: number;
  plano_atual: string;
  creditos_restantes: number;
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

