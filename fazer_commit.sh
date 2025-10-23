#!/bin/bash

# Script para fazer commit das mudanças do sistema de legendas

echo "🔍 Verificando status do Git..."
git status

echo ""
echo "📝 Arquivos que serão commitados:"
echo ""

# Adicionar arquivos novos
git add legenda_generator.py
git add README_LEGENDAS.md
git add GUIA_FONTES_TIKTOK.md
git add RESUMO_IMPLEMENTACAO.md
git add config.legendas.exemplo.json
git add teste_legenda_generator.py
git add teste_fonte_tiktok.py
git add COMMIT_MESSAGE.txt

# Adicionar arquivos modificados
git add gerar_lote_v3.py
git add config.json

echo "✅ Arquivos adicionados ao staging"
echo ""
echo "📋 Mensagem do commit:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat COMMIT_MESSAGE.txt
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

read -p "❓ Deseja fazer o commit? (s/n): " resposta

if [ "$resposta" = "s" ] || [ "$resposta" = "S" ]; then
    echo ""
    echo "🚀 Fazendo commit..."
    git commit -F COMMIT_MESSAGE.txt
    
    echo ""
    echo "✅ Commit realizado com sucesso!"
    echo ""
    echo "💡 Próximos passos:"
    echo "   git push origin main"
else
    echo ""
    echo "⏸️  Commit cancelado."
    echo ""
    echo "💡 Para commitar manualmente:"
    echo "   git commit -F COMMIT_MESSAGE.txt"
fi

