#!/bin/bash

echo "=== VERIFICAÇÃO DE CONFIGURAÇÕES FRONTEND ==="
echo ""

# Verificar se existe .env no frontend
if [ -f "frontend/.env" ]; then
    echo "✅ Arquivo frontend/.env existe"
    echo ""
    echo "Conteúdo:"
    cat frontend/.env
else
    echo "❌ Arquivo frontend/.env não encontrado"
fi

echo ""
echo "=== VERIFICAÇÃO DE BUILD ==="
cd frontend

if [ -d "dist" ]; then
    echo "✅ Diretório dist existe"
    echo "  Arquivos:"
    ls -la dist/
else
    echo "❌ Diretório dist não encontrado"
    echo "  Execute: npm run build"
fi

echo ""
echo "=== VERIFICAÇÃO DE PACKAGE.JSON ==="
if [ -f "package.json" ]; then
    echo "✅ package.json existe"
    echo ""
    echo "Scripts de build:"
    grep -A 5 '"scripts"' package.json
else
    echo "❌ package.json não encontrado"
fi

echo ""
echo "=== VERIFICAÇÃO DE VITE CONFIG ==="
if [ -f "vite.config.ts" ]; then
    echo "✅ vite.config.ts existe"
    echo ""
    echo "Configuração proxy:"
    grep -A 10 "proxy" vite.config.ts || echo "  Nenhum proxy configurado"
else
    echo "❌ vite.config.ts não encontrado"
fi
