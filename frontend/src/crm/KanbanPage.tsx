import { useEffect, useRef, useState } from "react";
import { createKanbanColumn, getCrmLeads, getKanbanColumns, moveLeadKanban } from "../api";
import type { CrmKanbanColumn, CrmLead } from "../types";

const DEFAULT_COLUMNS = [
  { name: "Novo lead", color: "#3b82f6", position: 0 },
  { name: "Em atendimento", color: "#f59e0b", position: 1 },
  { name: "Aguardando resposta", color: "#8b5cf6", position: 2 },
  { name: "Orçamento enviado", color: "#f97316", position: 3 },
  { name: "Fechado", color: "#10b981", position: 4 },
  { name: "Perdido", color: "#ef4444", position: 5 },
];

const ORIGEM_ICON: Record<string, string> = {
  manual: "✏️",
  whatsapp: "📱",
  telegram: "✈️",
  site: "🌐",
};

function LeadCard({
  lead,
  onDragStart,
}: {
  lead: CrmLead;
  onDragStart: (id: number) => void;
}) {
  return (
    <div
      draggable
      onDragStart={() => onDragStart(lead.id)}
      className="cursor-grab rounded-2xl border border-slate-100 bg-white p-3 shadow-sm transition hover:shadow-md active:cursor-grabbing active:opacity-70"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-violet-100 text-xs font-bold text-violet-700">
            {lead.name.charAt(0).toUpperCase()}
          </div>
          <span className="text-sm font-medium text-ink leading-tight">{lead.name}</span>
        </div>
        <span className="text-sm">{ORIGEM_ICON[lead.origin || "manual"] || ""}</span>
      </div>
      {lead.phone && (
        <div className="mt-1.5 flex items-center gap-1 text-xs text-slate-400">
          <span>📞</span> {lead.phone}
        </div>
      )}
      {lead.notes && (
        <div className="mt-1 truncate text-xs text-slate-500">{lead.notes}</div>
      )}
      <div className="mt-2 text-[10px] text-slate-300">
        {new Date(lead.created_at).toLocaleDateString("pt-BR")}
      </div>
    </div>
  );
}

function KanbanColumn({
  column,
  leads,
  draggingId,
  onDragStart,
  onDrop,
}: {
  column: CrmKanbanColumn;
  leads: CrmLead[];
  draggingId: number | null;
  onDragStart: (id: number) => void;
  onDrop: (columnId: number) => void;
}) {
  const [isOver, setIsOver] = useState(false);

  return (
    <div
      className={`flex min-h-[200px] w-72 shrink-0 flex-col rounded-[20px] transition ${
        isOver ? "bg-slate-100 ring-2 ring-violet-400" : "bg-slate-50"
      }`}
      onDragOver={(e) => { e.preventDefault(); setIsOver(true); }}
      onDragLeave={() => setIsOver(false)}
      onDrop={() => { setIsOver(false); onDrop(column.id); }}
    >
      {/* Header da coluna */}
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: column.color }} />
          <span className="text-sm font-semibold text-slate-700">{column.name}</span>
        </div>
        <span className="rounded-full bg-white px-2 py-0.5 text-xs font-semibold text-slate-400 shadow-sm">
          {leads.length}
        </span>
      </div>

      {/* Cards */}
      <div className="flex flex-1 flex-col gap-2 overflow-y-auto px-3 pb-3">
        {leads.length === 0 && !isOver && (
          <div className="flex flex-1 items-center justify-center py-8 text-xs text-slate-300">
            Solte aqui
          </div>
        )}
        {leads.map((lead) => (
          <LeadCard
            key={lead.id}
            lead={lead}
            onDragStart={onDragStart}
          />
        ))}
        {isOver && draggingId && (
          <div className="rounded-2xl border-2 border-dashed border-violet-300 bg-violet-50 py-4 text-center text-xs text-violet-400">
            Soltar aqui
          </div>
        )}
      </div>
    </div>
  );
}

export default function KanbanPage() {
  const [columns, setColumns] = useState<CrmKanbanColumn[]>([]);
  const [leads, setLeads] = useState<CrmLead[]>([]);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [seedError, setSeedError] = useState("");
  const [loadError, setLoadError] = useState("");
  const draggingId = useRef<number | null>(null);

  async function load() {
    setLoading(true);
    setLoadError("");
    try {
      const [cols, leadsData] = await Promise.all([getKanbanColumns(), getCrmLeads()]);
      setColumns(cols);
      setLeads(leadsData);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Falha ao carregar kanban");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function seedDefaultColumns(silent = false) {
    if (seeding) return;
    setSeeding(true);
    if (!silent) {
      setSeedError("");
    }
    try {
      for (const col of DEFAULT_COLUMNS) {
        await createKanbanColumn(col);
      }
      await load();
    } catch (err) {
      if (!silent) {
        setSeedError(err instanceof Error ? err.message : "Falha ao criar colunas padrão");
      }
    } finally {
      setSeeding(false);
    }
  }

  useEffect(() => {
    if (!loading && columns.length === 0 && !seeding) {
      seedDefaultColumns(true);
    }
  }, [columns.length, loading, seeding]);

  async function handleDrop(columnId: number) {
    const id = draggingId.current;
    if (!id) return;
    draggingId.current = null;

    // Otimista: atualiza localmente imediatamente
    setLeads((prev) =>
      prev.map((l) => (l.id === id ? { ...l, kanban_column_id: columnId } : l))
    );

    try {
      await moveLeadKanban(id, columnId);
    } catch {
      // Reverte em caso de erro
      await load();
    }
  }

  // Leads sem coluna → primeira coluna (ou "sem coluna")
  function leadsForColumn(colId: number) {
    return leads.filter((l) => l.kanban_column_id === colId);
  }
  const unassigned = leads.filter((l) => !l.kanban_column_id);

  if (loading) {
    return <div className="py-20 text-center text-slate-400">Carregando kanban...</div>;
  }

  if (columns.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
        <div className="text-5xl">🗂</div>
        <h2 className="font-serif text-2xl text-ink">Kanban ainda não configurado</h2>
        <p className="max-w-sm text-sm text-slate-500">
          Crie as colunas padrão para começar a organizar seus leads visualmente.
        </p>
        <button
          onClick={() => seedDefaultColumns()}
          disabled={seeding}
          className="rounded-full bg-violet-600 px-6 py-2.5 font-semibold text-white hover:bg-violet-700 disabled:opacity-50"
        >
          {seeding ? "Criando colunas..." : "Criar colunas padrão"}
        </button>
        {loadError ? <div className="text-sm text-red-600">{loadError}</div> : null}
        {seedError ? <div className="text-sm text-red-600">{seedError}</div> : null}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-serif text-3xl text-ink">Kanban</h1>
          <p className="mt-0.5 text-sm text-slate-500">
            {leads.length} lead{leads.length !== 1 ? "s" : ""} • arraste para mover entre colunas
          </p>
        </div>
        {loadError ? <div className="text-sm text-red-600">{loadError}</div> : null}
        {unassigned.length > 0 && (
          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">
            {unassigned.length} sem coluna
          </span>
        )}
      </div>

      {/* Board */}
      <div className="overflow-x-auto pb-4">
        <div className="flex gap-4" style={{ minWidth: `${columns.length * 300}px` }}>
          {columns.map((col) => (
            <KanbanColumn
              key={col.id}
              column={col}
              leads={leadsForColumn(col.id)}
              draggingId={draggingId.current}
              onDragStart={(id) => { draggingId.current = id; }}
              onDrop={handleDrop}
            />
          ))}

          {/* Coluna "Sem coluna" se existir leads não atribuídos */}
          {unassigned.length > 0 && (
            <div className="flex w-72 shrink-0 flex-col rounded-[20px] bg-slate-50">
              <div className="flex items-center gap-2 px-4 py-3">
                <div className="h-2.5 w-2.5 rounded-full bg-slate-300" />
                <span className="text-sm font-semibold text-slate-500">Sem coluna</span>
                <span className="ml-auto rounded-full bg-white px-2 py-0.5 text-xs font-semibold text-slate-400 shadow-sm">
                  {unassigned.length}
                </span>
              </div>
              <div className="flex flex-col gap-2 px-3 pb-3">
                {unassigned.map((lead) => (
                  <LeadCard
                    key={lead.id}
                    lead={lead}
                    onDragStart={(id) => { draggingId.current = id; }}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
