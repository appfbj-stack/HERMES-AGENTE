with open('frontend/src/MasterPanel.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

hermes_component = '''

function HermesAdminPanel({ show, tab, setTab, onClose }: { show: boolean, tab: string, setTab: (tab: any) => void, onClose: () => void }) {
  const [messages, setMessages] = useState<Array<{role: string, content: string}>>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  async function sendMessage() {
    if (!input.trim()) return;
    setLoading(true);
    try {
      const userMsg = { role: 'user', content: input };
      const newMessages = [...messages, userMsg];
      setMessages(newMessages);
      setInput('');
      const response = await hermesAdminChat(input);
      setMessages([...newMessages, { role: 'assistant', content: response.response }]);
    } catch (e) {
      setMessages([...messages, { role: 'assistant', content: 'Erro ao processar mensagem.' }]);
    } finally {
      setLoading(false);
    }
  }

  if (!show) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="h-[85vh] w-full max-w-4xl overflow-hidden rounded-[32px] bg-white shadow-2xl">
        <div className="flex h-full">
          <div className="w-64 border-r border-black/5 bg-panel">
            <div className="flex items-center justify-between border-b border-black/5 p-4">
              <h3 className="font-serif text-lg">Hermes Admin</h3>
              <button onClick={onClose} className="text-2xl text-slate-400 hover:text-slate-600">×</button>
            </div>
            <nav className="p-2 space-y-1">
              <button
                onClick={() => setTab('chat')}
                className={`w-full rounded-xl px-4 py-2 text-left text-sm transition ${tab === 'chat' ? 'bg-emerald-100 text-emerald-700' : 'hover:bg-slate-100'}`}
              >
                💬 Chat
              </button>
              <button
                onClick={() => setTab('tasks')}
                className={`w-full rounded-xl px-4 py-2 text-left text-sm transition ${tab === 'tasks' ? 'bg-emerald-100 text-emerald-700' : 'hover:bg-slate-100'}`}
              >
                ✅ Tarefas
              </button>
              <button
                onClick={() => setTab('projects')}
                className={`w-full rounded-xl px-4 py-2 text-left text-sm transition ${tab === 'projects' ? 'bg-emerald-100 text-emerald-700' : 'hover:bg-slate-100'}`}
              >
                📁 Projetos
              </button>
              <button
                onClick={() => setTab('routines')}
                className={`w-full rounded-xl px-4 py-2 text-left text-sm transition ${tab === 'routines' ? 'bg-emerald-100 text-emerald-700' : 'hover:bg-slate-100'}`}
              >
                ⏰ Rotinas
              </button>
              <button
                onClick={() => setTab('memory')}
                className={`w-full rounded-xl px-4 py-2 text-left text-sm transition ${tab === 'memory' ? 'bg-emerald-100 text-emerald-700' : 'hover:bg-slate-100'}`}
              >
                🧠 Memória
              </button>
              <button
                onClick={() => setTab('logs')}
                className={`w-full rounded-xl px-4 py-2 text-left text-sm transition ${tab === 'logs' ? 'bg-emerald-100 text-emerald-700' : 'hover:bg-slate-100'}`}
              >
                📋 Logs
              </button>
            </nav>
          </div>

          <div className="flex-1 overflow-hidden">
            {tab === 'chat' && (
              <div className="flex h-full flex-col">
                <div className="flex-1 overflow-y-auto p-6">
                  <div className="space-y-4">
                    {messages.length === 0 && (
                      <div className="rounded-2xl bg-panel p-6 text-center text-slate-500">
                        <div className="text-4xl mb-2">🤖</div>
                        <div>Olá! Sou o Hermes Admin Master.</div>
                        <div className="mt-2 text-sm">Posso ajudar você a:</div>
                        <ul className="mt-4 inline-block text-left text-sm space-y-2">
                          <li>• Listar clientes ativos/bloqueados</li>
                          <li>• Ver pagamentos pendentes</li>
                          <li>• Criar tarefas e rotinas</li>
                          <li>• Consultar memória da empresa</li>
                        </ul>
                      </div>
                    )}
                    {messages.map((msg, i) => (
                      <div
                        key={i}
                        className={`rounded-2xl p-4 ${msg.role === 'user' ? 'bg-emerald-600 text-white ml-12' : 'bg-panel text-ink mr-12'}`}
                      >
                        {msg.content}
                      </div>
                    ))}
                    {loading && (
                      <div className="rounded-2xl bg-panel p-4 text-slate-500 mr-12">Digitando...</div>
                    )}
                  </div>
                </div>
                <div className="border-t border-black/5 p-4">
                  <div className="flex gap-2">
                    <input
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                      placeholder="Digite sua mensagem..."
                      className="flex-1 rounded-full border-2 border-black/10 px-4 py-2 focus:border-emerald-500 focus:outline-none"
                    />
                    <button
                      onClick={sendMessage}
                      disabled={loading || !input.trim()}
                      className="rounded-full bg-emerald-600 px-6 py-2 text-white hover:bg-emerald-700 disabled:opacity-50"
                    >
                      Enviar
                    </button>
                  </div>
                </div>
              </div>
            )}

            {tab === 'tasks' && (
              <div className="h-full overflow-y-auto p-6">
                <h3 className="mb-4 font-serif text-xl">Tarefas Internas</h3>
                <div className="rounded-2xl bg-panel p-8 text-center text-slate-500">
                  <div className="text-4xl mb-2">📋</div>
                  <div>Gerenciamento de tarefas administrativas</div>
                  <div className="mt-2 text-sm">Em breve: CRUD completo de tarefas</div>
                </div>
              </div>
            )}

            {tab === 'projects' && (
              <div className="h-full overflow-y-auto p-6">
                <h3 className="mb-4 font-serif text-xl">Projetos</h3>
                <div className="rounded-2xl bg-panel p-8 text-center text-slate-500">
                  <div className="text-4xl mb-2">📁</div>
                  <div>Gerenciamento de projetos administrativos</div>
                  <div className="mt-2 text-sm">Em breve: CRUD completo de projetos</div>
                </div>
              </div>
            )}

            {tab === 'routines' && (
              <div className="h-full overflow-y-auto p-6">
                <h3 className="mb-4 font-serif text-xl">Rotinas</h3>
                <div className="rounded-2xl bg-panel p-8 text-center text-slate-500">
                  <div className="text-4xl mb-2">⏰</div>
                  <div>Gerenciamento de rotinas agendadas</div>
                  <div className="mt-2 text-sm">Em breve: CRUD completo de rotinas</div>
                </div>
              </div>
            )}

            {tab === 'memory' && (
              <div className="h-full overflow-y-auto p-6">
                <h3 className="mb-4 font-serif text-xl">Memória da Empresa</h3>
                <div className="rounded-2xl bg-panel p-8 text-center text-slate-500">
                  <div className="text-4xl mb-2">🧠</div>
                  <div>Memória corporativa do Hermes Admin</div>
                  <div className="mt-2 text-sm">Em breve: CRUD completo de memória</div>
                </div>
              </div>
            )}

            {tab === 'logs' && (
              <div className="h-full overflow-y-auto p-6">
                <h3 className="mb-4 font-serif text-xl">Logs de Ações</h3>
                <div className="rounded-2xl bg-panel p-8 text-center text-slate-500">
                  <div className="text-4xl mb-2">📋</div>
                  <div>Log de ações administrativas</div>
                  <div className="mt-2 text-sm">Em breve: Listagem completa de logs</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
'''

# Inserir antes da função genPassword
if 'function genPassword(): string' in content:
    content = content.replace('function genPassword(): string', hermes_component + 'function genPassword(): string')
    print('Componente HermesAdmin adicionado!')
else:
    print('Não encontrou o ponto de inserção')

with open('frontend/src/MasterPanel.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print('MasterPanel.tsx atualizado com componente HermesAdmin!')
