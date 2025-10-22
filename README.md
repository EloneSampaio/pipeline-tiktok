# 🎬 Pipeline de Geração Automática de Vídeos

Pipeline completo para geração automatizada de vídeos curtos usando IA (Text-to-Speech + Stable Diffusion + MoviePy). Ideal para criação em massa de conteúdo para TikTok, YouTube Shorts e Instagram Reels.

## 📋 Índice

- [Características](#-características)
- [Requisitos](#-requisitos)
- [Instalação](#-instalação)
- [Configuração](#️-configuração)
- [Uso](#-uso)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Formato do JSON](#-formato-do-json)
- [Logs e Monitoramento](#-logs-e-monitoramento)
- [Solução de Problemas](#-solução-de-problemas)
- [Licença](#-licença)

## ✨ Características

### 🎯 Funcionalidades Principais

- **Geração de Áudio (TTS)**: Conversão de texto em voz natural com suporte a clonagem de voz
- **Geração de Imagens (IA)**: Criação de imagens a partir de prompts usando Stable Diffusion
- **Montagem Automática**: Composição de vídeo com:
  - Transições suaves (crossfade)
  - Efeito Ken Burns (zoom animado)
  - Legendas customizáveis
  - Música de fundo automática
- **Processamento em Lote**: Geração de múltiplos vídeos sequencialmente
- **Logs Detalhados**: Sistema completo de logs com timestamps e estatísticas
- **Formato Vertical**: Otimizado para TikTok (1080x1920)

### 📊 Métricas e Monitoramento

- ⏱️ Tempo de processamento por etapa
- 📈 Estimativa de tempo restante
- 💾 Tamanho dos arquivos gerados
- ✅ Taxa de sucesso/erro
- 📊 Estatísticas médias por vídeo

## 🔧 Requisitos

### Hardware Recomendado

- **GPU**: NVIDIA com pelo menos 8GB VRAM (RTX 3060 ou superior)
- **RAM**: 16GB mínimo, 32GB recomendado
- **Armazenamento**: 20GB livres (modelos + vídeos gerados)

### Software

- **Sistema Operacional**: Linux (testado no Ubuntu 22.04)
- **Python**: 3.10+
- **CUDA**: 12.1
- **FFmpeg**: Instalado no sistema

## 📦 Instalação

### 1. Clone o Repositório

```bash
git clone https://github.com/seu-usuario/pipeline-tiktok.git
cd pipeline-tiktok
```

### 2. Crie um Ambiente Virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as Dependências

```bash
pip install -r requirements.txt
```

**Nota**: A instalação pode levar alguns minutos, pois inclui PyTorch com CUDA e outros modelos pesados.

### 4. Instale FFmpeg (se necessário)

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# Verificar instalação
ffmpeg -version
```

## ⚙️ Configuração

### 1. Arquivo de Configuração (`config.json`)

Crie ou edite o arquivo `config.json`:

```json
{
  "json_file": "historias.json",
  "output_folder": "saida",
  
  "models": {
    "tts": "tts_models/multilingual/multi-dataset/xtts_v2",
    "t2i": "runwayml/stable-diffusion-v1-5"
  },
  
  "audio": {
    "language": "pt",
    "voice_clone_wav": "voz_referencia.wav",
    "music_file": "musica_fundo.mp3",
    "music_volume": 0.15
  },
  
  "video": {
    "format": [1080, 1920],
    "fps": 24,
    "threads": 4,
    "transition_duration": 0.5,
    "caption_font": "Arial-Bold",
    "caption_fontsize": 70,
    "caption_stroke": 3
  }
}
```

### 2. Arquivo de Histórias (`historias.json`)

Estruture suas histórias no formato JSON:

```json
[
  {
    "id_video": "historia_01",
    "historia_completa": "Era uma vez, em uma floresta encantada...",
    "cenas": [
      "A magical forest with tall ancient trees, cinematic lighting",
      "A small cottage in the woods, fairy tale style",
      "Mystical creatures dancing under moonlight"
    ],
    "legendas": [
      "Era uma vez...",
      "Em uma floresta encantada",
      "Criaturas mágicas dançavam"
    ]
  }
]
```

### 3. Arquivos Opcionais

- **Clonagem de Voz**: Coloque um arquivo `.wav` de 5-10 segundos da voz desejada
- **Música de Fundo**: Adicione um arquivo `.mp3` para trilha sonora

## 🚀 Uso

### Executar o Pipeline

```bash
python gerar_lote_v2.py
```

### Saída Esperada

```
================================================================================
  🎬 PIPELINE DE GERAÇÃO AUTOMÁTICA DE VÍDEOS 🎬
================================================================================

[2025-10-22 19:52:25] [INFO    ] ================================================================================
[2025-10-22 19:52:25] [INFO    ]                      INICIALIZANDO PIPELINE                      
[2025-10-22 19:52:25] [INFO    ] ================================================================================
[2025-10-22 19:52:25] [INFO    ] Carregando arquivo de configuração: config.json
[2025-10-22 19:52:25] [INFO    ] ✓ Configuração carregada e validada com sucesso

[2025-10-22 19:52:25] [INFO    ] ================================================================================
[2025-10-22 19:52:25] [INFO    ]                   INICIANDO PROCESSAMENTO EM LOTE                   
[2025-10-22 19:52:25] [INFO    ] ================================================================================
[2025-10-22 19:52:25] [INFO    ] 📂 Carregando histórias de: historias.json
[2025-10-22 19:52:25] [INFO    ] ✓ Arquivo carregado com sucesso
[2025-10-22 19:52:25] [INFO    ] 📊 Total de vídeos para processar: 2

...
```

### Arquivos Gerados

Os vídeos e arquivos intermediários serão salvos em `saida/`:

```
saida/
├── historia_01_audio.wav
├── historia_01_video_final.mp4
├── imagens_historia_01/
│   ├── cena_01.png
│   ├── cena_02.png
│   └── cena_03.png
└── pipeline_YYYYMMDD_HHMMSS.log
```

## 📁 Estrutura do Projeto

```
pipeline-tiktok/
├── gerar_lote_v2.py          # Script principal (versão 2 - recomendada)
├── gerar_lote.py             # Script original (versão 1)
├── gerar_video.py            # Script para vídeo único
├── config.json               # Configuração do pipeline
├── historias.json            # Histórias a serem processadas
├── requirements.txt          # Dependências Python
├── README.md                 # Este arquivo
├── venv/                     # Ambiente virtual (não versionado)
├── saida/                    # Vídeos gerados (não versionado)
│   ├── *.mp4                 # Vídeos finais
│   ├── *_audio.wav           # Áudios gerados
│   └── imagens_*/            # Imagens por vídeo
└── pipeline_*.log            # Logs de execução
```

## 📝 Formato do JSON

### Estrutura Completa

```json
[
  {
    "id_video": "string",           // Identificador único (sem espaços)
    "historia_completa": "string",  // Texto completo da narração
    "cenas": [                      // Array de prompts para imagens
      "string",
      "string"
    ],
    "legendas": [                   // Array de legendas (opcional)
      "string",
      "string"
    ]
  }
]
```

### Dicas para Prompts de Imagens

**✅ Bons Prompts:**
```
"A majestic lion in the African savanna at sunset, 4k, cinematic lighting, wildlife photography"
"Ancient library with floating books, magical atmosphere, fantasy art, detailed"
```

**❌ Evite:**
```
"lion"  // Muito genérico
"Uma biblioteca com livros e magia e pessoas lendo à noite com velas"  // Muito longo/confuso
```

### Exemplo Completo

```json
[
  {
    "id_video": "historia_anansi",
    "historia_completa": "Anansi era uma aranha esperta que vivia na floresta africana. Um dia, ela decidiu capturar todas as histórias do mundo.",
    "cenas": [
      "Clever spider character in African forest, animation style, vibrant colors",
      "Spider planning something clever, storybook illustration",
      "Magical stories floating in the air, mystical atmosphere"
    ],
    "legendas": [
      "Anansi, a aranha esperta",
      "Vivia na floresta",
      "E queria todas as histórias"
    ]
  }
]
```

## 📊 Logs e Monitoramento

### Sistema de Logs

O pipeline gera dois tipos de saída:

1. **Console**: Logs em tempo real com emojis e cores
2. **Arquivo**: `pipeline_YYYYMMDD_HHMMSS.log` com detalhes completos

### Níveis de Log

- `INFO`: Informações gerais de progresso
- `WARNING`: Avisos (ex: arquivo de música não encontrado)
- `ERROR`: Erros que impedem geração de um vídeo
- `CRITICAL`: Erros fatais que param o pipeline

### Estatísticas Finais

```
================================================================================
                      RESUMO FINAL DO PROCESSAMENTO                      
================================================================================
⏱️  Tempo total de execução: 15m 30s

📊 Estatísticas:
  ├─ Total processado: 5
  ├─ ✅ Sucessos: 4 (80.0%)
  └─ ❌ Erros: 1 (20.0%)

⏱️  Tempos médios por etapa:
  ├─ Áudio (TTS): 45.2s
  ├─ Imagens (SD): 2m 15s
  └─ Montagem: 1m 10s

📈 Tempo médio por vídeo (sucesso): 3m 52s
```

## 🔧 Solução de Problemas

### Erro: `ImportError: cannot import name 'BeamSearchScorer'`

**Solução**: Incompatibilidade de versão do transformers

```bash
pip install transformers==4.36.2 --force-reinstall
```

### Erro: `CUDA out of memory`

**Soluções**:
1. Reduza o número de inference steps no código (linha 269):
   ```python
   num_inference_steps=20  # ao invés de 25
   ```

2. Use resolução menor para imagens (linha 269-270):
   ```python
   width=512,   # ao invés de 768
   height=768   # ao invés de 1024
   ```

3. Feche outros programas que usam GPU

### Erro: Font não encontrada

**Solução**: Instale fontes adicionais

```bash
sudo apt install fontconfig
sudo apt install fonts-liberation
fc-cache -f -v
```

Ou mude a fonte no `config.json`:
```json
"caption_font": "DejaVu-Sans-Bold"
```

### Vídeos sem áudio

**Solução**: Verifique instalação do FFmpeg

```bash
ffmpeg -version
pip install imageio-ffmpeg --upgrade
```

### Performance lenta

**Otimizações**:
1. Aumente threads no `config.json`:
   ```json
   "threads": 8
   ```

2. Use SSD para armazenamento temporário

3. Verifique se está usando GPU:
   ```bash
   nvidia-smi
   ```

## 🎯 Roadmap

- [ ] Suporte a múltiplas vozes por vídeo
- [ ] Geração de legendas automáticas (ASR)
- [ ] Interface web para configuração
- [ ] Suporte a vídeos horizontais
- [ ] Efeitos de transição adicionais
- [ ] Exportação direta para redes sociais
- [ ] Processamento paralelo de vídeos

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🙏 Agradecimentos

- [Coqui TTS](https://github.com/coqui-ai/TTS) - Text-to-Speech
- [Stable Diffusion](https://github.com/huggingface/diffusers) - Geração de Imagens
- [MoviePy](https://zulko.github.io/moviepy/) - Edição de Vídeo

---

**Desenvolvido com ❤️ para criadores de conteúdo**

Para dúvidas ou suporte, abra uma [issue](https://github.com/seu-usuario/pipeline-tiktok/issues).

