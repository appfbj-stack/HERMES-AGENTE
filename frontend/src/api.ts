import type { Chat, Credit, Lead, LoginResponse, MeResponse, Message, Task } from "./types";

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

export async function getLeads() {
  return request<Lead[]>("/leads");
}

export async function getTasks() {
  return request<Task[]>("/tasks");
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

