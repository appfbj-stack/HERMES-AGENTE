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
  };
  tenant: {
    id: number;
    name: string;
    email: string;
    plan: string;
    active: boolean;
  };
};

