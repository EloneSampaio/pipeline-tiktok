# 🔧 Comandos Git para Commit

## 📝 Opção 1: Usando o script automático (Recomendado)

```bash
chmod +x fazer_commit.sh
./fazer_commit.sh
```

---

## 📝 Opção 2: Commit manual (passo a passo)

### 1. Adicionar arquivos novos
```bash
git add legenda_generator.py
git add README_LEGENDAS.md
git add GUIA_FONTES_TIKTOK.md
git add RESUMO_IMPLEMENTACAO.md
git add config.legendas.exemplo.json
git add teste_legenda_generator.py
git add teste_fonte_tiktok.py
```

### 2. Adicionar arquivos modificados
```bash
git add gerar_lote_v3.py
git add config.json
```

### 3. Verificar o que será commitado
```bash
git status
```

### 4. Fazer o commit com a mensagem preparada
```bash
git commit -F COMMIT_MESSAGE.txt
```

### 5. Enviar para o repositório remoto
```bash
git push origin main
```

---

## 📝 Opção 3: Commit simplificado (uma linha)

```bash
git add legenda_generator.py README_LEGENDAS.md GUIA_FONTES_TIKTOK.md RESUMO_IMPLEMENTACAO.md config.legendas.exemplo.json teste_legenda_generator.py teste_fonte_tiktok.py gerar_lote_v3.py config.json && git commit -m "feat: Sistema de legendas profissionais com Whisper + FFmpeg

- Nova classe LegendaGenerator (modular e reutilizável)
- Suporte completo a customização (fonte, cor, tamanho, etc)
- Highlight palavra por palavra (estilo karaoke)
- Tradução automática integrada
- Compatível com FFmpeg 7.x
- Documentação completa
- Fonte TikTok Sans configurada
- Fix: BrokenPipeError com captacity
- Fix: PIL.Image.ANTIALIAS com Pillow 12"
```

---

## 🔍 Comandos úteis

### Ver o que mudou
```bash
git diff
```

### Ver status dos arquivos
```bash
git status
```

### Ver últimos commits
```bash
git log --oneline -5
```

### Desfazer staging (se adicionou algo por engano)
```bash
git reset HEAD <arquivo>
```

---

## 📋 Resumo do que será commitado

### ✨ Arquivos Novos (7 arquivos)
- `legenda_generator.py` - Classe principal (520 linhas)
- `README_LEGENDAS.md` - Documentação completa
- `GUIA_FONTES_TIKTOK.md` - Guia de fontes
- `RESUMO_IMPLEMENTACAO.md` - Resumo técnico
- `config.legendas.exemplo.json` - Exemplos
- `teste_legenda_generator.py` - Script de teste
- `teste_fonte_tiktok.py` - Teste TikTok Sans

### ✏️ Arquivos Modificados (2 arquivos)
- `gerar_lote_v3.py` - Refatorado para usar LegendaGenerator
- `config.json` - Nova seção "legendas"

---

## ⚠️ Antes de fazer push

1. ✅ Teste se tudo funciona:
   ```bash
   python teste_legenda_generator.py
   ```

2. ✅ Verifique se há erros de linting:
   ```bash
   # (se tiver linter configurado)
   pylint legenda_generator.py
   ```

3. ✅ Revise as mudanças:
   ```bash
   git diff --staged
   ```

---

## 🎯 Mensagem do commit

A mensagem completa está em `COMMIT_MESSAGE.txt` e segue o padrão:

```
feat: Implementar sistema de legendas profissionais com Whisper + FFmpeg

🎬 Sistema completo de legendas estilo TikTok/Shorts...
```

**Tipo:** `feat` (nova funcionalidade)  
**Escopo:** Sistema de legendas  
**Breaking Changes:** Nenhum  
**Backward Compatible:** Sim  

---

## 💡 Dica

Se preferir, pode revisar e editar a mensagem antes de commitar:
```bash
nano COMMIT_MESSAGE.txt
git commit -F COMMIT_MESSAGE.txt
```

