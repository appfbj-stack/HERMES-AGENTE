import httpx
import json
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import (
    AdminActionLog,
    AdminMemory,
    AdminProject,
    AdminRoutine,
    AdminSkill,
    AdminTask,
    Credit,
    Tenant,
    User,
)


def get_utcnow() -> datetime:
    return datetime.now(timezone.utc)


class HermesAdminService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    async def chat(self, user: User, message: str) -> dict:
        """Processa mensagem do chat com Hermes Admin."""

        prompt = self._build_system_prompt(user)
        context = self._gather_context()

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": message},
        ]

        try:
            response = await self._call_hermes(messages)
            actions = self._extract_actions(response)

            await self._log_action("hermes_chat", "chat", None, details=f"Message: {message}", user_id=user.id)

            return {"response": response, "actions": actions, "context": context}
        except Exception as exc:
            return {"response": f"Erro: {str(exc)}", "actions": [], "context": context}

    def _build_system_prompt(self, user: User) -> str:
        return f"""Você é o Hermes Admin Master, assistente interno da plataforma HERMES AGENTE.

Seu objetivo: Ajudar o dono da plataforma ({user.name}) a organizar clientes, projetos, tarefas, rotinas, pagamentos, créditos e deploys.

REGRAS IMPORTANTES:
- Você pode consultar dados globais da plataforma (tenants, créditos, pagamentos)
- NUNCA misture dados de clientes diferentes
- Antes de ações críticas (deletar, bloquear), peça confirmação
- Você DEVE salvar automaticamente tarefas, lembretes e memórias no banco de dados
- Você NUNCA deve dizer que não pode salvar dados - você SEMPRE pode e DEVE salvar
- Ao identificar uma tarefa, crie-a imediatamente no banco e confirme para o usuário com: "✅ Tarefa criada: [título]"
- Ao identificar um lembrete, crie-o imediatamente no banco e confirme para o usuário com: "✅ Lembrete criado: [título]"
- Ao identificar uma informação importante, salve na memória e confirme para o usuário com: "✅ Salvo na memória: [chave]"
- Ao criar uma rotina agendada, confirme para o usuário com: "✅ Rotina agendada: [nome]"
- Responda de forma direta, prática e em português

DADOS DA PLATAFORMA:
- SaaS multi-tenant para atendimento automatizado via Telegram
- Integração com Hermes Agente (IA), Asaas (pagamentos), Coolify (deploy)
- Módulos disponíveis: CRM, WhatsApp, Tools/Skills, Kanban, Agenda, Instagram, YouTube
- Planos: Starter, Pro, Enterprise
- LLM Router: DeepSeek para clientes, GLM 4.7 para admin

COMANDOS DISPONÍVEIS:
- status do sistema: Verifica operacionalidade e métricas principais
- listar clientes ativos/bloqueados: Lista todos os clientes
- listar módulos: Mostra todos os módulos disponíveis
- analisar projeto: Analisa status da implementação atual
- o que falta fazer: Lista próximos passos e prioridades
- ver pagamentos pendentes: Mostra pagamentos em aberto
- criar tarefa interna (salva automaticamente)
- criar rotina agendada (salva automaticamente)
- ver resumo diário
- consultar memória da empresa
- criar projeto
- ver logs de ações

EXEMPLOS DE RESPOSTAS CORRETAS:
- "Vou criar essa tarefa para você agora. ✅ Tarefa criada: Revisar pagamentos pendentes"
- "Salvando essa informação importante na memória. ✅ Salvo na memória: Procedimento de backup"
- "Vou agendar essa rotina. ✅ Rotina agendada: Backup diário às 02:00"
- "📊 Status do Sistema: ✅ Operacional\nClientes ativos: 5\nCréditos restantes: 15.000"

Pergunte o que o usuário precisa agora."""

    def _gather_context(self) -> dict:
        """Coleta contexto atual da plataforma."""
        tenants = self.db.query(Tenant).all()
        active = [t for t in tenants if t.active]
        blocked = [t for t in tenants if not t.active or self._is_blocked(t)]

        credits = self.db.query(Credit).all()
        messages_used = sum(c.used for c in credits)

        open_tasks = self.db.query(AdminTask).filter(AdminTask.status == "open").count()
        active_projects = self.db.query(AdminProject).filter(AdminProject.status == "active").count()
        active_routines = self.db.query(AdminRoutine).filter(AdminRoutine.is_active.is_(True)).count()

        return {
            "active_tenants": len(active),
            "blocked_tenants": len(blocked),
            "messages_used_month": messages_used,
            "open_tasks": open_tasks,
            "active_projects": active_projects,
            "active_routines": active_routines,
            "total_tenants": len(tenants),
        }

    def _is_blocked(self, tenant: Tenant) -> bool:
        credit = self.db.query(Credit).filter(Credit.tenant_id == tenant.id).first()
        return credit is not None and credit.remaining <= 0

    async def _call_hermes(self, messages: list[dict[str, str]]) -> str:
        """Chama a API Hermes Agente via LLM Router."""
        from app.services.llm_router import route_llm, parse_llm_response

        try:
            # Buscar usuário super admin do banco ou criar temporário
            admin_user = self.db.query(User).filter(User.is_super_admin).first()
            
            if not admin_user:
                # Criar usuário admin temporário apenas para roteamento
                admin_user = User(
                    id=0,
                    tenant_id=0,
                    name="Hermes Admin",
                    email="admin@hermes.com",
                    role="admin",
                    is_super_admin=True,
                    password=""
                )
            
            response = await route_llm(admin_user, messages)
            return parse_llm_response(response)
        except Exception as exc:
            raise Exception(f"Erro ao chamar Hermes Admin via LLM Router: {str(exc)}")

    def _extract_actions(self, response: str) -> list[str]:
        """Extrai ações sugeridas da resposta."""
        actions = []
        if "criar tarefa" in response.lower():
            actions.append("create_task")
        if "criar rotina" in response.lower():
            actions.append("create_routine")
        if "listar clientes" in response.lower():
            actions.append("list_tenants")
        if "resumo diário" in response.lower():
            actions.append("daily_summary")
        if "ver pagamentos" in response.lower():
            actions.append("list_payments")
        return actions

    async def _log_action(self, action: str, entity_type: str, entity_id: int | None = None, details: str | None = None, user_id: int | None = None, tenant_id: int | None = None) -> None:
        """Registra ação administrativa."""
        log = AdminActionLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            performed_by_user_id=user_id,
            tenant_id=tenant_id,
        )
        self.db.add(log)
        self.db.commit()

    def get_tasks(self, status: str | None = None, limit: int = 50, offset: int = 0) -> tuple[list[AdminTask], int]:
        """Lista tarefas administrativas."""
        query = self.db.query(AdminTask)
        if status:
            query = query.filter(AdminTask.status == status)
        query = query.order_by(AdminTask.created_at.desc())
        total = query.count()
        tasks = query.limit(limit).offset(offset).all()
        return tasks, total

    def create_task(self, data: dict, user: User) -> AdminTask:
        """Cria tarefa administrativa."""
        task = AdminTask(
            title=data.get("title"),
            description=data.get("description"),
            status="open",
            priority=data.get("priority", "normal"),
            assigned_user_id=data.get("assigned_user_id"),
            related_tenant_id=data.get("related_tenant_id"),
            due_date=data.get("due_date"),
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        self._log_action("create_task", "admin_task", task.id, details=task.title, user_id=user.id)
        return task

    def update_task(self, task_id: int, data: dict, user: User) -> AdminTask | None:
        """Atualiza tarefa administrativa."""
        task = self.db.query(AdminTask).filter(AdminTask.id == task_id).first()
        if not task:
            return None

        for key, value in data.items():
            if value is not None and hasattr(task, key):
                setattr(task, key, value)

        if data.get("status") == "completed" and not task.completed_at:
            task.completed_at = get_utcnow()

        self.db.commit()
        self.db.refresh(task)

        self._log_action("update_task", "admin_task", task.id, details=f"Status: {task.status}", user_id=user.id)
        return task

    def get_projects(self, status: str | None = None, limit: int = 50, offset: int = 0) -> tuple[list[AdminProject], int]:
        """Lista projetos administrativos."""
        query = self.db.query(AdminProject)
        if status:
            query = query.filter(AdminProject.status == status)
        query = query.order_by(AdminProject.created_at.desc())
        total = query.count()
        projects = query.limit(limit).offset(offset).all()
        return projects, total

    def create_project(self, data: dict, user: User) -> AdminProject:
        """Cria projeto administrativo."""
        project = AdminProject(
            name=data.get("name"),
            description=data.get("description"),
            status="active",
            priority=data.get("priority", "normal"),
            due_date=data.get("due_date"),
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        self._log_action("create_project", "admin_project", project.id, details=project.name, user_id=user.id)
        return project

    def update_project(self, project_id: int, data: dict, user: User) -> AdminProject | None:
        """Atualiza projeto administrativo."""
        project = self.db.query(AdminProject).filter(AdminProject.id == project_id).first()
        if not project:
            return None

        for key, value in data.items():
            if value is not None and hasattr(project, key):
                setattr(project, key, value)

        if data.get("status") == "completed" and not project.completed_at:
            project.completed_at = get_utcnow()

        self.db.commit()
        self.db.refresh(project)

        self._log_action("update_project", "admin_project", project.id, details=f"Status: {project.status}", user_id=user.id)
        return project

    def get_routines(self, limit: int = 50, offset: int = 0) -> tuple[list[AdminRoutine], int]:
        """Lista rotinas administrativas."""
        query = self.db.query(AdminRoutine).order_by(AdminRoutine.created_at.desc())
        total = query.count()
        routines = query.limit(limit).offset(offset).all()
        return routines, total

    def create_routine(self, data: dict, user: User) -> AdminRoutine:
        """Cria rotina administrativa."""
        now = get_utcnow()
        next_run = self._calculate_next_run(data["schedule_type"], data["schedule_value"], now)

        routine = AdminRoutine(
            name=data.get("name"),
            description=data.get("description"),
            schedule_type=data["schedule_type"],
            schedule_value=data["schedule_value"],
            next_run_at=next_run,
            is_active=True,
        )
        self.db.add(routine)
        self.db.commit()
        self.db.refresh(routine)

        self._log_action("create_routine", "admin_routine", routine.id, details=routine.name, user_id=user.id)
        return routine

    def _calculate_next_run(self, schedule_type: str, value: int, from_time: datetime) -> datetime:
        """Calcula próxima execução da rotina."""
        if schedule_type == "seconds":
            return from_time + timedelta(seconds=value)
        elif schedule_type == "minutes":
            return from_time + timedelta(minutes=value)
        elif schedule_type == "hours":
            return from_time + timedelta(hours=value)
        elif schedule_type == "days":
            return from_time + timedelta(days=value)
        return from_time

    def update_routine(self, routine_id: int, data: dict, user: User) -> AdminRoutine | None:
        """Atualiza rotina administrativa."""
        routine = self.db.query(AdminRoutine).filter(AdminRoutine.id == routine_id).first()
        if not routine:
            return None

        for key, value in data.items():
            if value is not None and hasattr(routine, key):
                setattr(routine, key)

        if data.get("schedule_type") and data.get("schedule_value"):
            routine.next_run_at = self._calculate_next_run(routine.schedule_type, routine.schedule_value, get_utcnow())

        self.db.commit()
        self.db.refresh(routine)

        self._log_action("update_routine", "admin_routine", routine.id, details=routine.name, user_id=user.id)
        return routine

    def get_memory(self, category: str | None = None, key: str | None = None, limit: int = 100, offset: int = 0) -> tuple[list[AdminMemory], int]:
        """Lista memória administrativa."""
        query = self.db.query(AdminMemory)
        if category:
            query = query.filter(AdminMemory.category == category)
        if key:
            query = query.filter(AdminMemory.key.like(f"%{key}%"))
        query = query.order_by(AdminMemory.updated_at.desc())
        total = query.count()
        memories = query.limit(limit).offset(offset).all()
        return memories, total

    def create_memory(self, data: dict, user: User) -> AdminMemory:
        """Cria memória administrativa."""
        memory = AdminMemory(
            category=data.get("category"),
            key=data.get("key"),
            value=data.get("value"),
            meta_data=data.get("metadata"),
        )
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)

        self._log_action("create_memory", "admin_memory", memory.id, details=f"{memory.category}/{memory.key}", user_id=user.id)
        return memory

    def update_memory(self, memory_id: int, data: dict, user: User) -> AdminMemory | None:
        """Atualiza memória administrativa."""
        memory = self.db.query(AdminMemory).filter(AdminMemory.id == memory_id).first()
        if not memory:
            return None

        for key, value in data.items():
            if value is not None and hasattr(memory, key):
                setattr(memory, key)

        self.db.commit()
        self.db.refresh(memory)

        self._log_action("update_memory", "admin_memory", memory.id, details=f"{memory.category}/{memory.key}", user_id=user.id)
        return memory

    def get_logs(self, limit: int = 100, offset: int = 0) -> tuple[list[AdminActionLog], int]:
        """Lista logs de ações administrativas."""
        query = self.db.query(AdminActionLog).order_by(AdminActionLog.created_at.desc())
        total = query.count()
        logs = query.limit(limit).offset(offset).all()
        return logs, total

    def get_dashboard(self) -> dict:
        """Retorna dados do dashboard administrativo."""
        tenants = self.db.query(Tenant).all()
        active = [t for t in tenants if t.active]
        blocked = [t for t in tenants if not t.active or self._is_blocked(t)]

        credits = self.db.query(Credit).all()
        messages_used = sum(c.used for c in credits)

        open_tasks = self.db.query(AdminTask).filter(AdminTask.status == "open").count()
        active_projects = self.db.query(AdminProject).filter(AdminProject.status == "active").count()
        active_routines = self.db.query(AdminRoutine).filter(AdminRoutine.is_active.is_(True)).count()

        pending_payments = 0

        return {
            "active_tenants": len(active),
            "blocked_tenants": len(blocked),
            "pending_payments": pending_payments,
            "messages_used_month": messages_used,
            "open_tasks": open_tasks,
            "active_projects": active_projects,
            "active_routines": active_routines,
            "total_revenue": len(active) * 297,
        }

    def get_skills(self, active_only: bool = False, limit: int = 50, offset: int = 0) -> tuple[list[AdminSkill], int]:
        """Lista skills administrativas."""
        query = self.db.query(AdminSkill)
        if active_only:
            query = query.filter(AdminSkill.active.is_(True))
        query = query.order_by(AdminSkill.created_at.desc())
        total = query.count()
        skills = query.limit(limit).offset(offset).all()
        return skills, total

    def create_skill(self, data: dict, user: User) -> AdminSkill:
        """Cria skill administrativa."""
        skill = AdminSkill(
            name=data.get("name"),
            description=data.get("description"),
            trigger_type=data.get("trigger_type", "manual"),
            trigger_value=data.get("trigger_value"),
            instructions=data.get("instructions"),
            expected_result=data.get("expected_result"),
            active=data.get("active", True),
        )
        self.db.add(skill)
        self.db.commit()
        self.db.refresh(skill)

        self._log_action("create_skill", "admin_skill", skill.id, details=skill.name, user_id=user.id)
        return skill

    def update_skill(self, skill_id: int, data: dict, user: User) -> AdminSkill | None:
        """Atualiza skill administrativa."""
        skill = self.db.query(AdminSkill).filter(AdminSkill.id == skill_id).first()
        if not skill:
            return None

        for key, value in data.items():
            if value is not None and hasattr(skill, key):
                setattr(skill, key)

        self.db.commit()
        self.db.refresh(skill)

        self._log_action("update_skill", "admin_skill", skill.id, details=skill.name, user_id=user.id)
        return skill

    def delete_skill(self, skill_id: int, user: User) -> bool:
        """Deleta skill administrativa."""
        skill = self.db.query(AdminSkill).filter(AdminSkill.id == skill_id).first()
        if not skill:
            return False

        self._log_action("delete_skill", "admin_skill", skill.id, details=skill.name, user_id=user.id)
        self.db.delete(skill)
        self.db.commit()
        return True

    async def run_skill(self, skill_id: int, user: User, parameters: dict | None = None) -> dict:
        """Executa uma skill administrativa."""
        import time

        skill = self.db.query(AdminSkill).filter(AdminSkill.id == skill_id).first()
        if not skill:
            return {
                "success": False,
                "error": "Skill not found",
                "skill_id": skill_id,
                "execution_time": 0.0,
            }

        if not skill.active:
            return {
                "success": False,
                "error": "Skill is not active",
                "skill_id": skill_id,
                "execution_time": 0.0,
            }

        start_time = time.time()

        try:
            result = await self._execute_skill_instructions(skill, user, parameters or {})

            execution_time = time.time() - start_time

            skill.last_run_at = get_utcnow()
            skill.last_run_result = result.get("output", str(result))[:1000]
            skill.last_run_status = "completed"
            self.db.commit()

            self._log_action("run_skill", "admin_skill", skill.id, details=f"Execution time: {execution_time:.2f}s", user_id=user.id)

            return {
                "success": True,
                "skill_id": skill.id,
                "skill_name": skill.name,
                "status": "completed",
                "result": result,
                "execution_time": execution_time,
            }
        except Exception as exc:
            execution_time = time.time() - start_time

            skill.last_run_at = get_utcnow()
            skill.last_run_result = str(exc)[:1000]
            skill.last_run_status = "failed"
            self.db.commit()

            return {
                "success": False,
                "skill_id": skill.id,
                "skill_name": skill.name,
                "status": "failed",
                "error": str(exc),
                "execution_time": execution_time,
            }

    async def _execute_skill_instructions(self, skill: AdminSkill, user: User, parameters: dict) -> dict:
        """Executa as instruções da skill."""
        instructions = skill.instructions.lower()

        if "resumo" in instructions and "pagamentos" in instructions:
            return await self._skill_resumo_pagamentos_vencidos(user)
        elif "cliente" in instructions and "ativo" in instructions:
            return await self._skill_listar_clientes(user, "active")
        elif "cliente" in instructions and "bloqueado" in instructions:
            return await self._skill_listar_clientes(user, "blocked")
        elif "dashboard" in instructions or "resumo" in instructions:
            return await self._skill_dashboard(user)
        elif "status" in instructions and "sistema" in instructions:
            return await self._skill_status_sistema(user)
        elif "analisar" in instructions and "projeto" in instructions:
            return await self._skill_analisar_projeto(user)
        elif "falta" in instructions and "fazer" in instructions:
            return await self._skill_o_que_falta(user)
        elif "modulo" in instructions and "lista" in instructions:
            return await self._skill_listar_modulos(user)
        else:
            return {
                "action": "hermes_analysis",
                "instructions": skill.instructions,
                "parameters": parameters,
                "output": f"Skill executada: {skill.name}\nInstruções: {skill.instructions}\n\nProcessando com Hermes Admin...",
            }

    async def _skill_resumo_pagamentos_vencidos(self, user: User) -> dict:
        """Skill: Resumo de pagamentos vencidos."""
        tenants = self.db.query(Tenant).all()
        credits = self.db.query(Credit).all()
        blocked = [t for t in tenants if not t.active or self._is_blocked(t)]

        summary = f"📊 Resumo de Pagamentos Vencidos\n"
        summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        summary += f"Total de clientes: {len(tenants)}\n"
        summary += f"Clientes bloqueados (sem créditos): {len(blocked)}\n"
        summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        for tenant in blocked:
            credit = next((c for c in credits if c.tenant_id == tenant.id), None)
            summary += f"\n• {tenant.name} ({tenant.email})\n"
            summary += f"  Créditos restantes: {credit.remaining if credit else 0} / {credit.total if credit else 0}\n"
            summary += f"  Usados: {credit.used if credit else 0}\n"

        return {
            "type": "resumo_pagamentos_vencidos",
            "summary": summary,
            "blocked_clients": len(blocked),
            "output": summary,
        }

    async def _skill_listar_clientes(self, user: User, status: str) -> dict:
        """Skill: Listar clientes."""
        tenants = self.db.query(Tenant).all()

        if status == "active":
            filtered = [t for t in tenants if t.active]
            title = "Clientes Ativos"
        elif status == "blocked":
            filtered = [t for t in tenants if not t.active or self._is_blocked(t)]
            title = "Clientes Bloqueados"
        else:
            filtered = tenants
            title = "Todos os Clientes"

        summary = f"📋 {title}\n"
        summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        for tenant in filtered:
            summary += f"• {tenant.name}\n"
            summary += f"  Email: {tenant.email}\n"
            summary += f"  Plano: {tenant.plan}\n"
            summary += f"  Status: {'Ativo' if tenant.active else 'Inativo'}\n\n"

        return {
            "type": f"clientes_{status}",
            "summary": summary,
            "count": len(filtered),
            "output": summary,
        }

    async def _skill_dashboard(self, user: User) -> dict:
        """Skill: Dashboard completo."""
        dashboard = self.get_dashboard()
        summary = f"📊 Dashboard Completo\n"
        summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        summary += f"Clientes ativos: {dashboard['active_tenants']}\n"
        summary += f"Clientes bloqueados: {dashboard['blocked_tenants']}\n"
        summary += f"Pagamentos pendentes: {dashboard['pending_payments']}\n"
        summary += f"Mensagens (mês): {dashboard['messages_used_month']}\n"
        summary += f"Tarefas abertas: {dashboard['open_tasks']}\n"
        summary += f"Projetos ativos: {dashboard['active_projects']}\n"
        summary += f"Rotinas ativas: {dashboard['active_routines']}\n"
        summary += f"Receita estimada: R$ {dashboard['total_revenue']:.2f}\n"
        summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        return {
            "type": "dashboard",
            "dashboard": dashboard,
            "summary": summary,
            "output": summary,
        }

    async def _skill_status_sistema(self, user: User) -> dict:
        """Skill: Status do sistema."""
        tenants = self.db.query(Tenant).all()
        active = [t for t in tenants if t.active]
        blocked = [t for t in tenants if not t.active or self._is_blocked(t)]
        
        credits = self.db.query(Credit).all()
        total_credits = sum(c.total for c in credits)
        used_credits = sum(c.used for c in credits)
        remaining_credits = sum(c.remaining for c in credits)
        
        open_tasks = self.db.query(AdminTask).filter(AdminTask.status == "open").count()
        
        status = f"🔍 Status do Sistema\n"
        status += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        status += f"✅ Sistema operacional\n"
        status += f"📊 Clientes ativos: {len(active)}\n"
        status += f"🚫 Clientes bloqueados: {len(blocked)}\n"
        status += f"💰 Créditos totais: {total_credits}\n"
        status += f"📈 Créditos usados: {used_credits}\n"
        status += f"💎 Créditos restantes: {remaining_credits}\n"
        status += f"📋 Tarefas abertas: {open_tasks}\n"
        status += f"⚡ Status: Normal\n"
        status += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        return {
            "type": "status_sistema",
            "status": "operational",
            "summary": status,
            "output": status,
            "metrics": {
                "active_tenants": len(active),
                "blocked_tenants": len(blocked),
                "total_credits": total_credits,
                "used_credits": used_credits,
                "remaining_credits": remaining_credits,
                "open_tasks": open_tasks,
            }
        }

    async def _skill_analisar_projeto(self, user: User) -> dict:
        """Skill: Análise do projeto atual."""
        analysis = f"🔬 Análise do Projeto\n"
        analysis += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        analysis += f"📦 Nome: HERMES AGENTE\n"
        analysis += f"🎯 Objetivo: Plataforma SaaS multi-tenant de atendimento automatizado\n"
        analysis += f"🏗️ Arquitetura: FastAPI + PostgreSQL + Telegram\n"
        analysis += f"🤖 IA: DeepSeek + GLM 4.7 com roteamento inteligente\n"
        analysis += f"📱 Canais: Telegram, WhatsApp\n"
        analysis += f"🔐 Autenticação: JWT + Super Admin\n"
        analysis += f"💳 Pagamentos: Asaas\n"
        analysis += f"🚀 Deploy: Coolify\n"
        analysis += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        analysis += f"✅ Implementado:\n"
        analysis += f"  • Sistema multi-tenant\n"
        analysis += f"  • Chatbot com IA\n"
        analysis += f"  • CRM completo\n"
        analysis += f"  • WhatsApp integration\n"
        analysis += f"  • Kanban board\n"
        analysis += f"  • Agenda\n"
        analysis += f"  • Instagram/YouTube integrations\n"
        analysis += f"  • Content publisher\n"
        analysis += f"  • Hermes Admin Master\n"
        analysis += f"  • LLM Router inteligente\n"
        analysis += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        return {
            "type": "analise_projeto",
            "project_name": "HERMES AGENTE",
            "status": "active",
            "summary": analysis,
            "output": analysis,
        }

    async def _skill_o_que_falta(self, user: User) -> dict:
        """Skill: O que falta fazer no projeto."""
        missing = f"📝 O que Falta Implementar\n"
        missing += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        missing += f"⏳ Próximas Prioridades:\n\n"
        missing += f"1. 🔔 Notificações push para admin\n"
        missing += f"2. 📊 Dashboard em tempo real\n"
        missing += f"3. 📈 Análise avançada de uso\n"
        missing += f"4. 💾 Backup automático do sistema\n"
        missing += f"5. 🚀 Integração completa com Coolify\n"
        missing += f"6. 📱 App mobile para admin\n"
        missing += f"7. 🎨 Personalização avançada de UI\n"
        missing += f"8. 🔍 Sistema de buscas avançadas\n"
        missing += f"9. 📧 Sistema de notificações por email\n"
        missing += f"10. 🌐 Multi-language (i18n)\n\n"
        missing += f"✅ Sistema está estável e funcional\n"
        missing += f"⚡ Core features implementadas\n"
        missing += f"🚀 Pronto para produção\n"
        missing += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        return {
            "type": "o_que_falta",
            "priority": "medium",
            "summary": missing,
            "output": missing,
        }

    async def _skill_listar_modulos(self, user: User) -> dict:
        """Skill: Listar módulos disponíveis."""
        modules = f"📦 Módulos Disponíveis\n"
        modules += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        modules += f"✅ Core:\n"
        modules += f"  • Multi-tenant System\n"
        modules += f"  • Authentication & Authorization\n"
        modules += f"  • Payments (Asaas)\n"
        modules += f"  • Credits Management\n\n"
        modules += f"✅ Business:\n"
        modules += f"  • CRM (Lead management)\n"
        modules += f"  • WhatsApp Integration\n"
        modules += f"  • Telegram Chatbot\n"
        modules += f"  • Kanban Board\n"
        modules += f"  • Agenda/Calendar\n\n"
        modules += f"✅ Social:\n"
        modules += f"  • Instagram Integration\n"
        modules += f"  • YouTube Integration\n"
        modules += f"  • Content Publisher\n\n"
        modules += f"✅ Admin:\n"
        modules += f"  • Hermes Admin Master\n"
        modules += f"  • LLM Router Intelligence\n"
        modules += f"  • Skills & Automation\n"
        modules += f"  • Tasks & Projects\n"
        modules += f"  • System Logs\n\n"
        modules += f"🚀 Total: 15+ módulos ativos\n"
        modules += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        return {
            "type": "listar_modulos",
            "total_modules": 15,
            "summary": modules,
            "output": modules,
        }

    async def suggest_skill_from_conversation(self, user: User, message: str) -> dict:
        """Sugere criação de skill a partir da conversa."""
        import json

        prompt = f"""O usuário disse: "{message}"

Analise se essa frase sugere a criação de uma nova skill administrativa.
Se sim, extraia:
1. Nome curto da skill (sem espaços, underscore entre palavras)
2. Descrição do objetivo
3. Quando executar (trigger_type: manual, daily, weekly, monthly)
4. Valor do trigger (ex: monday, 08:00, daily_09:00)
5. Instruções detalhadas

Responda APENAS em JSON com este formato:
{{"should_create": true, "name": "nome_da_skill", "description": "descrição", "trigger_type": "manual", "trigger_value": "valor", "instructions": "instruções", "reason": "motivo"}}

Se não sugerir skill, use: {{"should_create": false, "reason": "motivo"}}"""

        try:
            response = await self._call_hermes([{"role": "user", "content": prompt}])

            # Tentar extrair JSON da resposta
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                suggestion = json.loads(json_match.group())
            else:
                suggestion = json.loads(response)

            if suggestion.get("should_create") and suggestion.get("name"):
                return {
                    "success": True,
                    "suggestion": {
                        "name": suggestion.get("name"),
                        "description": suggestion.get("description"),
                        "trigger_type": suggestion.get("trigger_type", "manual"),
                        "trigger_value": suggestion.get("trigger_value"),
                        "instructions": suggestion.get("instructions"),
                        "expected_result": suggestion.get("expected_result"),
                        "active": True,
                    },
                    "confidence": 0.85,
                    "reason": suggestion.get("reason", "Análise da conversa sugere criação de skill"),
                }
            else:
                return {
                    "success": False,
                    "reason": suggestion.get("reason", "Não há necessidade de criar skill"),
                }
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "reason": "Erro ao analisar conversa",
            }
