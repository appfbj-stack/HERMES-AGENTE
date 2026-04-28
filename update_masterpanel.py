import re

with open('frontend/src/MasterPanel.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Atualizar imports
old_import_pattern = r'import \{\s*addAdminCredits,\s*createAdminTenant,\s*deleteAdminTenant,\s*getAdminTenants,\s*getMasterBotInfo,\s*setAdminTenantModules,\s*updateAdminTenant,\s*type MasterBotInfo,\s*\} from "\./api";'

new_import = '''import {
  addAdminCredits,
  createAdminTenant,
  deleteAdminTenant,
  getAdminTenants,
  getMasterBotInfo,
  setAdminTenantModules,
  updateAdminTenant,
  type MasterBotInfo,
  hermesAdminChat,
  getHermesAdminDashboard,
} from "./api";'''

content = re.sub(old_import_pattern, new_import, content)

# Atualizar types import
old_types_import = 'import type { AdminTenant, NicheTemplate } from "./types";'
new_types_import = 'import type { AdminTenant, NicheTemplate, HermesAdminDashboard } from "./types";'
content = content.replace(old_types_import, new_types_import)

# Adicionar estados novos após o estado qrTenant
qrTenant_line = 'const [qrTenant, setQrTenant] = useState<AdminTenant | null>(null);'
new_states = '''const [qrTenant, setQrTenant] = useState<AdminTenant | null>(null);
  const [showHermesAdmin, setShowHermesAdmin] = useState(false);
  const [hermesTab, setHermesTab] = useState<'chat' | 'tasks' | 'projects' | 'routines' | 'memory' | 'logs'>('chat');
  const [hermesMessages, setHermesMessages] = useState<Array<{role: string, content: string}>>([]);
  const [hermesInput, setHermesInput] = useState('');
  const [hermesDashboard, setHermesDashboard] = useState<HermesAdminDashboard | null>(null);
  const [hermesLoading, setHermesLoading] = useState(false);'''

content = content.replace(qrTenant_line, new_states)

# Adicionar função loadHermesDashboard
load_function_pattern = r'(async function load\(\) \{[\s\S]*?\n  \})'
def add_hermes_load(match):
    original = match.group(1)
    hermes_load = '''async function load() {
    setLoading(true);
    setError("");
    try {
      const [tenantsData, botData, hermesData] = await Promise.all([
        getAdminTenants(),
        getMasterBotInfo().catch(() => null),
        getHermesAdminDashboard().catch(() => null),
      ]);
      setTenants(tenantsData);
      setMasterBot(botData);
      setHermesDashboard(hermesData);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro");
    } finally {
      setLoading(false);
    }
  }'''
    return hermes_load

content = re.sub(load_function_pattern, add_hermes_load, content)

with open('frontend/src/MasterPanel.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print('MasterPanel.tsx atualizado!')
