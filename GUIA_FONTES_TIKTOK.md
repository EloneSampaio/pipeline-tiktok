# 🎨 Guia de Fontes TikTok Sans

## 📍 Localização
Suas fontes estão em: `Fonts/TikTok_Sans/static/`

---

## 🎯 Fontes Recomendadas para Legendas

### **Para Legendas Estilo TikTok (Recomendado)**

#### 1. **TikTokSans Bold** (Padrão recomendado) ⭐
```json
"font": "Fonts/TikTok_Sans/static/TikTokSans_18pt-Bold.ttf"
```
- ✅ Melhor legibilidade
- ✅ Visual profissional
- ✅ Estilo TikTok autêntico

#### 2. **TikTokSans ExtraBold** (Impacto maior)
```json
"font": "Fonts/TikTok_Sans/static/TikTokSans_18pt-ExtraBold.ttf"
```
- ✅ Mais pesado e visível
- ✅ Bom para fundos complexos

#### 3. **TikTokSans Black** (Máximo impacto)
```json
"font": "Fonts/TikTok_Sans/static/TikTokSans_18pt-Black.ttf"
```
- ✅ Peso máximo
- ✅ Ultra visível

---

## 🎬 Variações Disponíveis

### **Larguras Normais (Recomendado para Legendas)**
| Peso | Arquivo | Quando Usar |
|------|---------|-------------|
| Light | `TikTokSans_18pt-Light.ttf` | Legendas sutis |
| Regular | `TikTokSans_18pt-Regular.ttf` | Legendas leves |
| Medium | `TikTokSans_18pt-Medium.ttf` | Equilíbrio |
| SemiBold | `TikTokSans_18pt-SemiBold.ttf` | Destaque moderado |
| **Bold** | `TikTokSans_18pt-Bold.ttf` | **✅ Recomendado** |
| ExtraBold | `TikTokSans_18pt-ExtraBold.ttf` | Muito visível |
| Black | `TikTokSans_18pt-Black.ttf` | Máximo impacto |

### **Condensed (Mais estreito)**
```json
"font": "Fonts/TikTok_Sans/static/TikTokSans_18pt_Condensed-Bold.ttf"
```
- 📝 Bom para textos longos
- 📝 Cabe mais texto na linha

### **Expanded (Mais largo)**
```json
"font": "Fonts/TikTok_Sans/static/TikTokSans_18pt_Expanded-Bold.ttf"
```
- 📝 Visual mais imponente
- 📝 Ocupa mais espaço

### **Extra Expanded (Muito largo)**
```json
"font": "Fonts/TikTok_Sans/static/TikTokSans_18pt_ExtraExpanded-Bold.ttf"
```
- 📝 Máxima largura
- 📝 Visual chamativo

---

## 🎨 Configurações Completas Recomendadas

### 🏆 **Preset 1: TikTok Autêntico (Recomendado)**
```json
{
  "legendas": {
    "font": "Fonts/TikTok_Sans/static/TikTokSans_18pt-Bold.ttf",
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

### 🎯 **Preset 2: TikTok Ultra Visível**
```json
{
  "legendas": {
    "font": "Fonts/TikTok_Sans/static/TikTokSans_18pt-Black.ttf",
    "font_size": 75,
    "font_color": "#FFFFFF",
    "stroke_width": 5,
    "stroke_color": "#000000",
    "shadow_strength": 3,
    "highlight_current_word": true,
    "word_highlight_color": "#FF0000",
    "max_palavras_por_linha": 2,
    "padding": 90
  }
}
```

### 📝 **Preset 3: TikTok Condensado (Textos Longos)**
```json
{
  "legendas": {
    "font": "Fonts/TikTok_Sans/static/TikTokSans_18pt_Condensed-Bold.ttf",
    "font_size": 65,
    "font_color": "#FFFFFF",
    "stroke_width": 3,
    "stroke_color": "#000000",
    "shadow_strength": 2,
    "highlight_current_word": true,
    "word_highlight_color": "#FFFF00",
    "max_palavras_por_linha": 4,
    "padding": 70
  }
}
```

### 🌟 **Preset 4: TikTok Minimalista**
```json
{
  "legendas": {
    "font": "Fonts/TikTok_Sans/static/TikTokSans_18pt-SemiBold.ttf",
    "font_size": 60,
    "font_color": "#FFFFFF",
    "stroke_width": 2,
    "stroke_color": "#000000",
    "shadow_strength": 1,
    "highlight_current_word": false,
    "word_highlight_color": "#FFFF00",
    "max_palavras_por_linha": 4,
    "padding": 60
  }
}
```

---

## 💡 Como Trocar de Fonte

### Método 1: Editar `config.json`
```json
{
  "legendas": {
    "font": "Fonts/TikTok_Sans/static/TikTokSans_18pt-Bold.ttf",
    ...
  }
}
```

### Método 2: No código Python
```python
from legenda_generator import LegendaGenerator

gerador = LegendaGenerator()
gerador.gerar_legendas(
    arquivo_video_entrada="video.mp4",
    arquivo_video_saida="video_legendado.mp4",
    font="Fonts/TikTok_Sans/static/TikTokSans_18pt-Bold.ttf",
    font_size=70,
    font_color="#FFFFFF"
)
```

### Método 3: Via linha de comando (depois de editar config.json)
```bash
python gerar_lote_v3.py
```

---

## 🎓 Dicas de Uso

### ✅ **Fazer:**
- Use **Bold** ou **ExtraBold** para melhor legibilidade
- Mantenha `font_size` entre 60-80 para vídeos verticais
- Use `stroke_width` de 3-5 para boa visibilidade
- Ative `highlight_current_word` para estilo karaoke

### ❌ **Evitar:**
- Fontes muito leves (Light, Regular) - difícil de ler
- `font_size` muito pequeno (< 50) - ilegível em mobile
- `stroke_width` muito fino (< 2) - texto some em fundos claros

---

## 🔍 Testar Diferentes Fontes

### Script de teste rápido:
```python
from legenda_generator import LegendaGenerator

fontes = [
    "TikTokSans_18pt-Bold.ttf",
    "TikTokSans_18pt-ExtraBold.ttf",
    "TikTokSans_18pt-Black.ttf",
]

gerador = LegendaGenerator(modelo_whisper='small')

for i, fonte in enumerate(fontes):
    caminho_fonte = f"Fonts/TikTok_Sans/static/{fonte}"
    saida = f"teste_fonte_{i+1}.mp4"
    
    print(f"Testando: {fonte}")
    gerador.gerar_legendas(
        arquivo_video_entrada="seu_video.mp4",
        arquivo_video_saida=saida,
        font=caminho_fonte,
        traduzir_para_ingles=True
    )
```

---

## 📊 Comparação Visual (Peso das Fontes)

```
Light      ────────────────  (Muito fino)
Regular    ━━━━━━━━━━━━━━━━  (Fino)
Medium     ━━━━━━━━━━━━━━━━  (Médio)
SemiBold   ━━━━━━━━━━━━━━━━  (Semi-pesado)
Bold       ━━━━━━━━━━━━━━━━  ⭐ Recomendado
ExtraBold  ████████████████  (Muito pesado)
Black      ████████████████  (Ultra pesado)
```

---

## 🎯 Resumo Rápido

**Para legendas TikTok autênticas, use:**
```json
"font": "Fonts/TikTok_Sans/static/TikTokSans_18pt-Bold.ttf"
```

**Já configurado no seu `config.json`!** ✅

---

## 🚀 Próximo Passo

1. **Teste agora:**
   ```bash
   python teste_legenda_generator.py
   ```

2. **Ou rode o pipeline completo:**
   ```bash
   python gerar_lote_v3.py
   ```

3. **Compare com outras fontes** editando `config.json`

---

**Fonte TikTok Sans oficial instalada e configurada!** 🎉

