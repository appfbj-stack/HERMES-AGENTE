with open('frontend/src/api.ts', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Linha 438 precisa ser corrigida
# Antes: const search = status ? ?status=&limit=&offset= : ?limit=&offset=;
# Depois: const search = status ? `?status=${status}&limit=${limit}&offset=${offset}` : `?limit=${limit}&offset=${offset}`;

lines[437] = '  const search = status ? `?status=${status}&limit=${limit}&offset=${offset}` : `?limit=${limit}&offset=${offset}`;\n'

# Linha 439 precisa ser corrigida
# Antes: const data = await request<{ tasks: AdminTask[]; total: number }>(`/admin/hermes/tasks`);
# Depois: const data = await request<{ tasks: AdminTask[]; total: number }>(`/admin/hermes/tasks${search}`);

lines[439] = '  const data = await request<{ tasks: AdminTask[]; total: number }>(`/admin/hermes/tasks${search}`);\n'

# Linha 445 precisa ser corrigida
lines[445] = '  const search = status ? `?status=${status}&limit=${limit}&offset=${offset}` : `?limit=${limit}&offset=${offset}`;\n'

# Linha 447 precisa ser corrigida
lines[447] = '  const data = await request<{ projects: AdminProject[]; total: number }>(`/admin/hermes/projects${search}`);\n'

# Linha 453 precisa ser corrigida
lines[453] = '  const search = `?limit=${limit}&offset=${offset}`;\n'

# Linha 454 precisa ser corrigida
lines[454] = '  const data = await request<{ routines: AdminRoutine[]; total: number }>(`/admin/hermes/routines${search}`);\n'

# Linha 566 precisa ser corrigida
lines[565] = '  const search = `?limit=${limit}&offset=${offset}`;\n'

# Linha 567 precisa ser corrigida
lines[566] = '  const data = await request<{ logs: AdminActionLog[]; total: number }>(`/admin/hermes/logs${search}`);\n'

# Linha 553 precisa ser corrigida (updateAdminMemory)
lines[552] = '  return request<AdminMemory>(`/admin/hermes/memory/${memoryId}`, {\n'

# Linha 560 precisa ser corrigida (deleteAdminMemory)
lines[559] = '  return request<void>(`/admin/hermes/memory/${memoryId}`, {\n'

with open('frontend/src/api.ts', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('api.ts corrigido!')
