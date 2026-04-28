with open('frontend/src/MasterPanel.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Dividir o conteúdo
# O return fecha com "  );"
# O HermesAdminPanel deve vir antes disso

# Encontrar o último "  );" antes do "function Stat"
lines = content.split('\n')

function_stat_line = -1
return_end_line = -1

for i, line in enumerate(lines):
    if 'function Stat' in line:
        function_stat_line = i
        break

# Encontrar o return_end antes de function Stat
if function_stat_line > 0:
    for i in range(function_stat_line - 20, function_stat_line):
        if '  );' in lines[i]:
            return_end_line = i
            break

print(f'function Stat na linha {function_stat_line+1}')
print(f'Return fecha na linha {return_end_line+1}')

# Remover o HermesAdminPanel que está fora do return
new_lines = []
hermes_panel = []
in_hermes = False

for line in lines:
    if '<HermesAdminPanel' in line and not in_hermes:
        in_hermes = True
    if in_hermes:
        hermes_panel.append(line)
        if '/>' in line:
            in_hermes = False
            continue
    new_lines.append(line)

print(f'Capturado HermesAdminPanel com {len(hermes_panel)} linhas')

# Inserir HermesAdminPanel antes do return_end
final_lines = []
for i, line in enumerate(new_lines):
    if i == return_end_line:
        # Inserir HermesAdminPanel antes do );
 
        # Procurar o </div> anterior para colocar o HermesAdminPanel após ele
        final_lines.extend(hermes_panel)
        final_lines.append('')  # Linha em branco
    final_lines.append(line)

with open('frontend/src/MasterPanel.tsx', 'w', encoding='utf-8') as f:
    f.write('\n'.join(final_lines))

print('HermesAdminPanel movido para dentro do return!')
