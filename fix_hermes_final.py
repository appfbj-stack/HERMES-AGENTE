with open('frontend/src/MasterPanel.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# O return fecha na linha 517
# O HermesAdminPanel está na linha 518 (fora do return)

# Remover o HermesAdminPanel da posição atual
hermes_panel_lines = []
hermes_start = 518
hermes_end = 524

for i in range(hermes_start, hermes_end + 1):
    hermes_panel_lines.append(lines[i])

# Remover o HermesAdminPanel
new_lines = lines[:hermes_start] + lines[hermes_end+1:]

# Inserir HermesAdminPanel ANTES do fechamento do return (linha 517)
insert_pos = 517  # Antes da linha onde está o ); no arquivo original

new_lines[insert_pos:insert_pos] = hermes_panel_lines

with open('frontend/src/MasterPanel.tsx', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('HermesAdminPanel movido para DENTRO do return')
print('MasterPanel.tsx corrigido!')
