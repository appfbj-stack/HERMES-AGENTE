import { Routes, Route, Navigate } from "react-router-dom";
import type { MeResponse } from "../types";
import CrmLeadsPage from "./LeadsPage";
import CrmKanbanPage from "./KanbanPage";
import CrmFollowupsPage from "./FollowupsPage";
import CrmSettingsPage from "./CrmSettingsPage";
import CrmConversasPage from "./ConversasPage";
import CrmDashboardPage from "./DashboardCRMPage";
import CrmTasksPage from "./TarefasPage";

export default function CrmWorkspace({ profile }: { profile: MeResponse }) {
  if (!profile.modules.crm) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <Routes>
      <Route path="/" element={<CrmDashboardPage profile={profile} />} />
      <Route path="/dashboard" element={<CrmDashboardPage profile={profile} />} />
      <Route path="/leads" element={<CrmLeadsPage />} />
      <Route
        path="/kanban"
        element={profile.modules.kanban ? <CrmKanbanPage /> : <Navigate to="/crm/dashboard" replace />}
      />
      <Route path="/conversations" element={<CrmConversasPage />} />
      <Route path="/followups" element={<CrmFollowupsPage />} />
      <Route path="/tasks" element={<CrmTasksPage />} />
      <Route path="/settings" element={<CrmSettingsPage />} />
      <Route path="*" element={<Navigate to="/crm/dashboard" replace />} />
    </Routes>
  );
}
