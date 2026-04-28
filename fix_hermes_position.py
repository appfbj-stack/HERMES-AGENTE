with open('frontend/src/MasterPanel.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# O problema: HermesAdminPanel está FORA do return
# Linha 517 fecha o return, linha 519 é o HermesAdminPanel

# Remover o HermesAdminPanel da posição atual (fora do return)
hermes_panel_lines = []
in_hermes_panel = False
hermes_start = -1
hermes_end = -1

for i, line in enumerate(lines):
    if '<HermesAdminPanel' in line:
        hermes_start = i
        in_hermes_panel = True
    if in_hermes_panel:
        hermes_panel_lines.append(line)
        if '/>' in line:
            hermes_end = i
            break

# Encontrar onde inserir (antes do fechamento do return, linha 517)
# O fechamento deve estar após o QRCodeModal

insert_pos = 517  # Linha onde fecha o return atual

# Remover o HermesAdminPanel da posição atual
new_lines = lines[:hermes_start] + lines[hermes_end+1:]

# Inserir HermesAdminPanel antes do fechamento do return
new_lines[insert_pos:insert_pos] = hermes_panel_lines

with open('frontend/src/MasterPanel.tsx', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f'HermesAdminPanel movido para DENTRO do return (posição {insert_pos+1})')
print('MasterPanel.tsx corrigido!')
