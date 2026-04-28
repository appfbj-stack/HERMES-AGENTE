with open('frontend/src/MasterPanel.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remover o HermesAdminPanel duplicado (linha 649)
# Manter apenas o primeiro (linha 517)

new_lines = []
first_hermes = True

for line in lines:
    if '<HermesAdminPanel' in line:
        if first_hermes:
            new_lines.append(line)
            first_hermes = False
            print(f'HermesAdminPanel mantido na posição atual')
        else:
            print(f'HermesAdminPanel duplicado REMOVIDO')
            continue
    else:
        new_lines.append(line)

with open('frontend/src/MasterPanel.tsx', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('HermesAdminPanel duplicado removido!')
print(f'Total de linhas: {len(new_lines)} (antes era {len(lines)})')
