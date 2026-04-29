import { FormEvent, useEffect, useState } from "react";
import {
  getCrmTasks,
  createCrmTask,
  updateCrmTask,
  deleteCrmTask,
  type CrmTask,
} from "../api";
import type { Priority } from "../types";

export default function TarefasPage() {
  const [tasks, setTasks] = useState<CrmTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingTask, setEditingTask] = useState<CrmTask | null>(null);
  const [filterStatus, setFilterStatus] = useState<"todos" | "pendente" | "em_andamento" | "concluida">("todos");
  const [filterPriority, setFilterPriority] = useState<"todos" | "baixa" | "media" | "alta">("todos");

  const [form, setForm] = useState({
    title: "",
    description: "",
    responsible_user_id: null as number | null,
    due_at: "",
    status: "pendente" as const,
    priority: "media" as Priority,
    lead_id: null as number | null,
  });

  async function loadTasks() {
    setLoading(true);
    setError("");
    try {
      const data = await getCrmTasks();
      setTasks(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar tarefas");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!form.title.trim()) return;

    setError("");
    try {
      await createCrmTask({
        title: form.title,
        description: form.description || undefined,
        responsible_user_id: form.responsible_user_id,
        due_at: form.due_at || undefined,
        status: form.status,
        priority: form.priority,
        lead_id: form.lead_id,
      });
      setShowForm(false);
      resetForm();
      loadTasks();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao criar tarefa");
    }
  }

  async function handleUpdate(e: FormEvent) {
    e.preventDefault();
    if (!editingTask) return;

    setError("");
    try {
      await updateCrmTask(editingTask.id, {
        title: form.title,
        description: form.description || undefined,
        responsible_user_id: form.responsible_user_id,
        due_at: form.due_at || undefined,
        status: form.status,
        priority: form.priority,
        lead_id: form.lead_id,
      });
      setEditingTask(null);
      setShowForm(false);
      resetForm();
      loadTasks();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao atualizar tarefa");
    }
  }

  async function handleDelete(taskId: number) {
    if (!confirm("Tem certeza que deseja excluir esta tarefa?")) return;

    setError("");
    try {
      await deleteCrmTask(taskId);
      loadTasks();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao excluir tarefa");
    }
  }

  function handleEdit(task: CrmTask) {
    setEditingTask(task);
    setForm({
      title: task.title,
      description: task.description || "",
      responsible_user_id: task.responsible_user_id,
      due_at: task.due_at || "",
      status: task.status as any,
      priority: task.priority as Priority,
      lead_id: task.lead_id,
    });
    setShowForm(true);
  }

  function resetForm() {
    setForm({
      title: "",
      description: "",
      responsible_user_id: null,
      due_at: "",
      status: "pendente",
      priority: "media",
      lead_id: null,
    });
  }

  function getPriorityColor(priority: string) {
    switch (priority) {
      case "baixa":
        return "bg-emerald-100 text-emerald-900";
      case "media":
        return "bg-amber-100 text-amber-900";
      case "alta":
        return "bg-red-100 text-red-900";
      default:
        return "bg-slate-100 text-slate-900";
    }
  }

  function getStatusColor(status: string) {
    switch (status) {
      case "pendente":
        return "bg-slate-100 text-slate-900";
      case "em_andamento":
        return "bg-blue-100 text-blue-900";
      case "concluida":
        return "bg-emerald-100 text-emerald-900";
      default:
        return "bg-slate-100 text-slate-900";
    }
  }

  const filteredTasks = tasks.filter((task) => {
    if (filterStatus !== "todos" && task.status !== filterStatus) return false;
    if (filterPriority !== "todos" && task.priority !== filterPriority) return false;
    return true;
  });

  useEffect(() => {
    loadTasks();
  }, []);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif text-slate-900">Tarefas</h1>
          <p className="text-slate-600">Gerencie as tarefas do CRM</p>
        </div>
        <button
          onClick={() => {
            resetForm();
            setEditingTask(null);
            setShowForm(true);
          }}
          className="rounded-full bg-brand px-6 py-3 text-sm font-semibold text-white hover:bg-brand/90"
        >
          + Nova Tarefa
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      )}

      {/* Filtros */}
      <div className="mb-6 flex flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-600">Status:</label>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as any)}
            className="rounded-xl border-2 border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-brand"
          >
            <option value="todos">Todos</option>
            <option value="pendente">Pendente</option>
            <option value="em_andamento">Em Andamento</option>
            <option value="concluida">Concluída</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-600">Prioridade:</label>
          <select
            value={filterPriority}
            onChange={(e) => setFilterPriority(e.target.value as any)}
            className="rounded-xl border-2 border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-brand"
          >
            <option value="todos">Todas</option>
            <option value="baixa">Baixa</option>
            <option value="media">Média</option>
            <option value="alta">Alta</option>
          </select>
        </div>
      </div>

      {/* Formulário */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-2xl rounded-3xl bg-white p-6 shadow-2xl">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-serif font-semibold text-slate-900">
                {editingTask ? "Editar Tarefa" : "Nova Tarefa"}
              </h2>
              <button
                onClick={() => {
                  setShowForm(false);
                  resetForm();
                  setEditingTask(null);
                }}
                className="text-2xl text-slate-400 hover:text-slate-600"
              >
                ×
              </button>
            </div>

            <form onSubmit={editingTask ? handleUpdate : handleCreate} className="space-y-4">
              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Título *</label>
                <input
                  type="text"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  className="input mt-1"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Descrição</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  className="input mt-1"
                  rows={3}
                />
              </div>

              <div className="grid gap-3 md:grid-cols-3">
                <div>
                  <label className="text-xs font-semibold uppercase text-slate-500">Status</label>
                  <select
                    value={form.status}
                    onChange={(e) => setForm({ ...form, status: e.target.value as any })}
                    className="input mt-1"
                  >
                    <option value="pendente">Pendente</option>
                    <option value="em_andamento">Em Andamento</option>
                    <option value="concluida">Concluída</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold uppercase text-slate-500">Prioridade</label>
                  <select
                    value={form.priority}
                    onChange={(e) => setForm({ ...form, priority: e.target.value as Priority })}
                    className="input mt-1"
                  >
                    <option value="baixa">Baixa</option>
                    <option value="media">Média</option>
                    <option value="alta">Alta</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold uppercase text-slate-500">Prazo</label>
                  <input
                    type="datetime-local"
                    value={form.due_at}
                    onChange={(e) => setForm({ ...form, due_at: e.target.value })}
                    className="input mt-1"
                  />
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false);
                    resetForm();
                    setEditingTask(null);
                  }}
                  className="flex-1 rounded-2xl bg-slate-100 px-5 py-2 text-sm hover:bg-slate-200"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="flex-1 rounded-2xl bg-brand px-5 py-2 font-semibold text-white hover:bg-brand/90"
                >
                  {editingTask ? "Salvar" : "Criar"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Lista de Tarefas */}
      {loading ? (
        <div className="rounded-3xl border-2 border-slate-200 bg-white p-8 text-center text-slate-500">
          Carregando tarefas...
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="rounded-3xl border-2 border-slate-200 bg-white p-8 text-center text-slate-500">
          <div className="text-6xl mb-4">📝</div>
          <p className="text-lg font-medium">Nenhuma tarefa encontrada</p>
          <p className="text-sm">Crie uma nova tarefa para começar</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredTasks.map((task) => (
            <div
              key={task.id}
              className={`rounded-3xl border-2 p-6 shadow-soft ${
                task.status === "concluida" ? "border-emerald-200 bg-emerald-50/50" : "border-slate-200 bg-white"
              }`}
            >
              <div className="mb-4 flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <h3 className={`font-semibold text-slate-900 ${task.status === "concluida" ? "line-through opacity-60" : ""}`}>
                    {task.title}
                  </h3>
                  {task.description && (
                    <p className={`mt-2 text-sm text-slate-600 ${task.status === "concluida" ? "line-through opacity-60" : ""}`}>
                      {task.description}
                    </p>
                  )}
                </div>
              </div>

              <div className="mb-4 flex flex-wrap gap-2">
                <span className={`rounded-full px-2 py-1 text-[10px] font-semibold uppercase ${getStatusColor(task.status)}`}>
                  {task.status.replace("_", " ")}
                </span>
                <span className={`rounded-full px-2 py-1 text-[10px] font-semibold uppercase ${getPriorityColor(task.priority)}`}>
                  {task.priority}
                </span>
              </div>

              {task.due_at && (
                <div className="mb-4 text-xs text-slate-500">
                  📅 Prazo: {new Date(task.due_at).toLocaleString("pt-BR")}
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(task)}
                  className="flex-1 rounded-xl bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-200"
                >
                  Editar
                </button>
                <button
                  onClick={() => handleDelete(task.id)}
                  className="rounded-xl bg-red-100 px-3 py-2 text-xs font-semibold text-red-700 hover:bg-red-200"
                >
                  Excluir
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
