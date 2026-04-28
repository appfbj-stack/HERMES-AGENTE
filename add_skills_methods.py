with open('backend/app/services/hermes_admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Adicionar métodos de skills no final do arquivo
skills_methods = '''

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
        else:
            return {
                "action": "hermes_analysis",
                "instructions": skill.instructions,
                "parameters": parameters,
                "output": f"Skill executada: {skill.name}\\nInstruções: {skill.instructions}\\n\\nProcessando com Hermes Admin...",
            }

    async def _skill_resumo_pagamentos_vencidos(self, user: User) -> dict:
        """Skill: Resumo de pagamentos vencidos."""
        tenants = self.db.query(Tenant).all()
        credits = self.db.query(Credit).all()
        blocked = [t for t in tenants if not t.active or self._is_blocked(t)]

        summary = f"📊 Resumo de Pagamentos Vencidos\\n"
        summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n"
        summary += f"Total de clientes: {len(tenants)}\\n"
        summary += f"Clientes bloqueados (sem créditos): {len(blocked)}\\n"
        summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n"

        for tenant in blocked:
            credit = next((c for c in credits if c.tenant_id == tenant.id), None)
            summary += f"\\n• {tenant.name} ({tenant.email})\\n"
            summary += f"  Créditos restantes: {credit.remaining if credit else 0} / {credit.total if credit else 0}\\n"
            summary += f"  Usados: {credit.used if credit else 0}\\n"

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

        summary = f"📋 {title}\\n"
        summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n"

        for tenant in filtered:
            summary += f"• {tenant.name}\\n"
            summary += f"  Email: {tenant.email}\\n"
            summary += f"  Plano: {tenant.plan}\\n"
            summary += f"  Status: {'Ativo' if tenant.active else 'Inativo'}\\n\\n"

        return {
            "type": f"clientes_{status}",
            "summary": summary,
            "count": len(filtered),
            "output": summary,
        }

    async def _skill_dashboard(self, user: User) -> dict:
        """Skill: Dashboard completo."""
        dashboard = self.get_dashboard()
        summary = f"📊 Dashboard Completo\\n"
        summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n"
        summary += f"Clientes ativos: {dashboard['active_tenants']}\\n"
        summary += f"Clientes bloqueados: {dashboard['blocked_tenants']}\\n"
        summary += f"Pagamentos pendentes: {dashboard['pending_payments']}\\n"
        summary += f"Mensagens (mês): {dashboard['messages_used_month']}\\n"
        summary += f"Tarefas abertas: {dashboard['open_tasks']}\\n"
        summary += f"Projetos ativos: {dashboard['active_projects']}\\n"
        summary += f"Rotinas ativas: {dashboard['active_routines']}\\n"
        summary += f"Receita estimada: R$ {dashboard['total_revenue']:.2f}\\n"
        summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        return {
            "type": "dashboard",
            "dashboard": dashboard,
            "summary": summary,
            "output": summary,
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
            json_match = re.search(r'\\{.*\\}', response, re.DOTALL)
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
'''

content = content.rstrip() + skills_methods

with open('backend/app/services/hermes_admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Métodos de skills adicionados ao hermes_admin.py!')
