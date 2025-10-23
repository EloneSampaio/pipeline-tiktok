# 🎬 Gerador de Legendas Profissionais - Documentação

Sistema de legendas estilo TikTok/Shorts usando **Whisper + FFmpeg** com customização completa.

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Instalação](#instalação)
3. [Uso Básico](#uso-básico)
4. [Configurações](#configurações)
5. [Exemplos](#exemplos)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

### Características

- ✅ **Transcrição automática** com Whisper (OpenAI)
- ✅ **Tradução integrada** (qualquer idioma → inglês)
- ✅ **Timestamps palavra por palavra** (estilo karaoke)
- ✅ **Destaque da palavra atual** (opcional)
- ✅ **Customização completa** (fonte, cor, tamanho, contorno, sombra)
- ✅ **Formato ASS profissional** (queimado com FFmpeg)
- ✅ **100% compatível** com FFmpeg moderno (7.x)

### Como Funciona

```
Vídeo → Whisper (transcrição) → Arquivo ASS (legendas) → FFmpeg (renderização) → Vídeo Legendado
```

---

## 📦 Instalação

### Dependências

```bash
# Instalar dependências Python
pip install openai-whisper

# FFmpeg (já deve estar instalado no sistema)
ffmpeg -version  # Verificar versão
```

---

## 🚀 Uso Básico

### 1. Uso Standalone (Script Direto)

```bash
# Uso simples
python legenda_generator.py input.mp4 output.mp4

# Com tradução para inglês
python legenda_generator.py input.mp4 output.mp4 sim

# Sem tradução (transcrição no idioma original)
python legenda_generator.py input.mp4 output.mp4 nao
```

### 2. Uso como Módulo Python

```python
from legenda_generator import LegendaGenerator

# Criar instância
gerador = LegendaGenerator(modelo_whisper='small')

# Gerar legendas
sucesso = gerador.gerar_legendas(
    arquivo_video_entrada="meu_video.mp4",
    arquivo_video_saida="meu_video_legendado.mp4",
    traduzir_para_ingles=True,
    highlight_current_word=True  # Destaque palavra por palavra
)

if sucesso:
    print("✅ Legendas geradas!")
else:
    print("❌ Erro ao gerar legendas")
```

### 3. Integração com Pipeline Principal

No arquivo `config.json`, adicione a seção `legendas`:

```json
{
  "legendas": {
    "font": "Impact",
    "font_size": 70,
    "font_color": "#FFFFFF",
    "stroke_width": 4,
    "stroke_color": "#000000",
    "shadow_strength": 2,
    "highlight_current_word": true,
    "word_highlight_color": "#FFFF00",
    "max_palavras_por_linha": 3,
    "padding": 80
  }
}
```

Depois execute o pipeline normalmente:

```bash
python gerar_lote_v3.py
```

---

## ⚙️ Configurações

### Parâmetros Disponíveis

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `font` | string | "Impact" | Nome ou caminho da fonte |
| `font_size` | int | 70 | Tamanho da fonte (30-150) |
| `font_color` | string | "#FFFFFF" | Cor da fonte em hex |
| `stroke_width` | int | 4 | Largura do contorno (0-10) |
| `stroke_color` | string | "#000000" | Cor do contorno em hex |
| `shadow_strength` | int | 2 | Intensidade da sombra (0-10) |
| `highlight_current_word` | bool | false | Destaca palavra atual |
| `word_highlight_color` | string | "#FFFF00" | Cor do destaque em hex |
| `max_palavras_por_linha` | int | 3 | Palavras por linha (1-5) |
| `padding` | int | 80 | Margem inferior em pixels |

### Cores Comuns (Hexadecimal)

| Cor | Código Hex |
|-----|------------|
| Branco | `#FFFFFF` |
| Preto | `#000000` |
| Amarelo | `#FFFF00` |
| Vermelho | `#FF0000` |
| Verde | `#00FF00` |
| Azul | `#0000FF` |
| Ciano | `#00FFFF` |
| Magenta | `#FF00FF` |
| Laranja | `#FF8800` |

### Modelos Whisper

| Modelo | Velocidade | Precisão | VRAM | Recomendado para |
|--------|------------|----------|------|------------------|
| `tiny` | ⚡⚡⚡⚡⚡ | ⭐⭐ | ~1GB | Testes rápidos |
| `base` | ⚡⚡⚡⚡ | ⭐⭐⭐ | ~1GB | Uso leve |
| `small` | ⚡⚡⚡ | ⭐⭐⭐⭐ | ~2GB | **Recomendado** |
| `medium` | ⚡⚡ | ⭐⭐⭐⭐⭐ | ~5GB | Alta precisão |
| `large` | ⚡ | ⭐⭐⭐⭐⭐ | ~10GB | Máxima precisão |

---

## 💡 Exemplos de Presets

### 🎪 Estilo TikTok Clássico (Padrão)

```python
gerador.gerar_legendas(
    arquivo_video_entrada="video.mp4",
    arquivo_video_saida="video_legendado.mp4",
    font="Impact",
    font_size=70,
    font_color="#FFFFFF",
    stroke_width=4,
    stroke_color="#000000",
    shadow_strength=2,
    highlight_current_word=True,
    word_highlight_color="#FFFF00",
    max_palavras_por_linha=3
)
```

### 🎨 Estilo Minimalista

```python
gerador.gerar_legendas(
    arquivo_video_entrada="video.mp4",
    arquivo_video_saida="video_legendado.mp4",
    font="Arial-Bold",
    font_size=60,
    font_color="#FFFFFF",
    stroke_width=2,
    stroke_color="#000000",
    shadow_strength=1,
    highlight_current_word=False,
    max_palavras_por_linha=4
)
```

### 🌈 Estilo Neon

```python
gerador.gerar_legendas(
    arquivo_video_entrada="video.mp4",
    arquivo_video_saida="video_legendado.mp4",
    font="Impact",
    font_size=75,
    font_color="#00FFFF",  # Ciano
    stroke_width=5,
    stroke_color="#FF00FF",  # Magenta
    shadow_strength=3,
    highlight_current_word=True,
    word_highlight_color="#FFFF00",  # Amarelo
    max_palavras_por_linha=2
)
```

### 🎬 Estilo Sutil/Profissional

```python
gerador.gerar_legendas(
    arquivo_video_entrada="video.mp4",
    arquivo_video_saida="video_legendado.mp4",
    font="Helvetica",
    font_size=50,
    font_color="#FFFFFF",
    stroke_width=1,
    stroke_color="#000000",
    shadow_strength=0,
    highlight_current_word=False,
    max_palavras_por_linha=5
)
```

---

## 🎯 Uso Avançado

### Processamento em Lote

```python
from legenda_generator import LegendaGenerator

gerador = LegendaGenerator(modelo_whisper='small')

# Lista de vídeos
videos = [
    ("video1.mp4", "video1_legendado.mp4"),
    ("video2.mp4", "video2_legendado.mp4"),
    ("video3.mp4", "video3_legendado.mp4"),
]

# Processar todos
stats = gerador.processar_em_lote(videos, traduzir_para_ingles=True)

print(f"Processados: {stats['total']}")
print(f"Sucessos: {stats['sucessos']}")
print(f"Falhas: {stats['falhas']}")
```

### Manter Arquivo ASS

Útil para edição manual das legendas:

```python
gerador.gerar_legendas(
    arquivo_video_entrada="video.mp4",
    arquivo_video_saida="video_legendado.mp4",
    manter_arquivo_ass=True  # Salva video_legendado.ass
)

# Depois você pode:
# 1. Editar video_legendado.ass manualmente
# 2. Re-renderizar com FFmpeg:
# ffmpeg -i video.mp4 -vf ass=video_legendado.ass output.mp4
```

### Usar Fontes Personalizadas

```python
gerador.gerar_legendas(
    arquivo_video_entrada="video.mp4",
    arquivo_video_saida="video_legendado.mp4",
    font="/path/to/custom_font.ttf",  # Caminho completo
    font_size=80,
    font_color="#FF1493"  # Rosa choque
)
```

---

## 🔧 Troubleshooting

### Problema: FFmpeg não encontrado

```bash
# Verificar instalação
ffmpeg -version

# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

### Problema: Modelo Whisper muito lento

**Solução:** Use modelo menor ou GPU

```python
# Opção 1: Modelo menor
gerador = LegendaGenerator(modelo_whisper='base')  # ou 'tiny'

# Opção 2: Verificar se GPU está disponível
import torch
print(f"CUDA disponível: {torch.cuda.is_available()}")
```

### Problema: Legendas muito pequenas/grandes

**Solução:** Ajuste `font_size` e `max_palavras_por_linha`

```python
# Para vídeo vertical (1080x1920) - TikTok/Shorts
font_size=70
max_palavras_por_linha=3

# Para vídeo horizontal (1920x1080) - YouTube
font_size=45
max_palavras_por_linha=5
```

### Problema: Fonte não encontrada

**Solução:** Use nome exato da fonte do sistema ou caminho completo

```bash
# Listar fontes disponíveis no sistema
fc-list  # Linux/Mac

# Ou use caminho completo
font="/usr/share/fonts/truetype/dejavu/DejaVu-Sans-Bold.ttf"
```

### Problema: Transcrição em idioma errado

**Solução:** Whisper detecta idioma automaticamente. Para forçar:

```python
# No código atual, use tradução=False para manter idioma original
gerador.gerar_legendas(
    arquivo_video_entrada="video.mp4",
    arquivo_video_saida="video_legendado.mp4",
    traduzir_para_ingles=False  # Transcreve no idioma original
)
```

---

## 📊 Performance

### Tempos Aproximados (modelo `small`)

| Duração Vídeo | Tempo Processamento | Hardware |
|---------------|---------------------|----------|
| 30 segundos | ~15-30s | CPU (i7) |
| 30 segundos | ~5-10s | GPU (RTX 3060) |
| 1 minuto | ~30-60s | CPU (i7) |
| 1 minuto | ~10-20s | GPU (RTX 3060) |

### Otimização

1. **Use GPU** se disponível (10x mais rápido)
2. **Modelo `small`** é melhor custo-benefício
3. **Modelo `tiny`** para protótipos rápidos
4. **Modelo `medium/large`** apenas se precisar máxima precisão

---

## 📝 Notas Técnicas

### Diferenças vs Captacity Original

| Característica | Captacity | Nossa Implementação |
|----------------|-----------|---------------------|
| Compatibilidade FFmpeg | ❌ Problemas 7.x | ✅ Totalmente compatível |
| Formato legendas | Interno MoviePy | ASS profissional |
| Customização | Limitada | Completa |
| Código | Monolítico | Modular (classe separada) |
| Reutilizável | Não | ✅ Sim |

### Formato ASS (Advanced SubStation Alpha)

- Padrão da indústria para legendas
- Suporta estilos avançados
- Compatível com todos players
- Editável manualmente

---

## 🤝 Contribuindo

Encontrou um bug ou tem sugestões? Abra uma issue!

---

## 📄 Licença

Mesmo que o projeto principal.

---

## 🙏 Créditos

- **Whisper**: OpenAI (transcrição)
- **FFmpeg**: Renderização de vídeo
- **Inspiração**: Captacity (unconv)

---

**Feito com ❤️ para criadores de conteúdo**

