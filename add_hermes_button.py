with open('frontend/src/MasterPanel.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Adicionar botão Hermes Admin após o botão "+ Novo cliente"
old_button = '''          <button
            onClick={() => setShowForm(true)}
            className="rounded-full bg-emerald-600 px-5 py-2 text-sm font-semibold text-white hover:bg-emerald-700"
          >
            + Novo cliente
          </button>'''

new_buttons = '''          <button
            onClick={() => setShowForm(true)}
            className="rounded-full bg-emerald-600 px-5 py-2 text-sm font-semibold text-white hover:bg-emerald-700"
          >
            + Novo cliente
          </button>
          <button
            onClick={() => setShowHermesAdmin(true)}
            className="rounded-full bg-violet-600 px-5 py-2 text-sm font-semibold text-white hover:bg-violet-700"
          >
            🤖 Hermes Admin
          </button>'''

content = content.replace(old_button, new_buttons)

# Adicionar shortcuts (atalhos rápidos) após os stats
stats_section_end = '''        <Stat
          label="Receita estimada"
          value={`R$ ${totalRevenue.toLocaleString("pt-BR")}`}
          color="emerald"
        />
      </div>'''

shortcuts_section = stats_section_end + '''

      <div className="rounded-[32px] bg-gradient-to-r from-violet-50 to-purple-50 p-6">
        <h3 className="mb-4 font-serif text-xl">⚡ Atalhos Rápidos</h3>
        <div className="grid gap-3 md:grid-cols-4">
          <button
            onClick={() => setShowHermesAdmin(true)}
            className="rounded-xl bg-white px-4 py-3 text-left text-sm transition hover:shadow-md"
          >
            <div className="font-medium text-emerald-700">🤖 Chat com Hermes</div>
            <div className="text-xs text-slate-500">Perguntar ao assistente</div>
          </button>
          <div className="rounded-xl bg-white px-4 py-3 text-left text-sm transition hover:shadow-md">
            <div className="font-medium text-emerald-700">✅ Clientes ativos</div>
            <div className="text-xs text-slate-500">{tenants.filter((t) => t.active).length} clientes</div>
          </div>
          <div className="rounded-xl bg-white px-4 py-3 text-left text-sm transition hover:shadow-md">
            <div className="font-medium text-red-700">⚠️ Bloqueados</div>
            <div className="text-xs text-slate-500">{tenants.filter((t) => t.credits_remaining <= 0).length} clientes</div>
          </div>
          <div className="rounded-xl bg-white px-4 py-3 text-left text-sm transition hover:shadow-md">
            <div className="font-medium text-amber-700">💰 Mensagens</div>
            <div className="text-xs text-slate-500">{totalUsedMessages.toLocaleString("pt-BR")} este mês</div>
          </div>
        </div>
      </div>
'''

content = content.replace(stats_section_end, shortcuts_section)

# Adicionar componente HermesAdminPanel após o modal QRCode
qr_modal_end = '''        </QRCodeModal>
      )}
    </div>
  );
}'''

new_end = '''        </QRCodeModal>
      )}

      <HermesAdminPanel
        show={showHermesAdmin}
        tab={hermesTab}
        setTab={setHermesTab}
        onClose={() => setShowHermesAdmin(false)}
      />
    </div>
  );
}'''

content = content.replace(qr_modal_end, new_end)

with open('frontend/src/MasterPanel.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print('MasterPanel.tsx atualizado com botão e componente HermesAdmin!')
