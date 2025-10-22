"""
Pipeline de Geração de Vídeos em Lote
Gera vídeos automaticamente a partir de histórias usando IA (TTS + Stable Diffusion)
"""
import os
import json
import math
import time
import logging
from datetime import datetime
from pathlib import Path

import torch
from TTS.api import TTS
from diffusers import StableDiffusionPipeline
from moviepy.editor import *

class VideoPipeline:
    """Pipeline principal para geração automatizada de vídeos em lote"""
    
    def __init__(self, config_path="config.json"):
        """
        Inicializa o pipeline carregando a configuração e configurando o logger.
        
        Args:
            config_path: Caminho para o arquivo de configuração JSON
        """
        self.logger = self._setup_logging()
        self._log_separator("=", "INICIALIZANDO PIPELINE")
        
        try:
            self.logger.info(f"Carregando arquivo de configuração: {config_path}")
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # Validação básica da configuração
            self._validar_configuracao()
            self.logger.info("✓ Configuração carregada e validada com sucesso")
            
        except FileNotFoundError:
            self.logger.error(f"✗ ERRO: Arquivo '{config_path}' não encontrado")
            raise
        except Exception as e:
            self.logger.error(f"✗ ERRO ao ler o config.json: {e}")
            raise
            
        self.modelo_tts = None
        self.modelo_t2i = None
        self.stats = {
            'tempo_audio': [],
            'tempo_imagens': [],
            'tempo_montagem': []
        }

    def _setup_logging(self):
        """
        Configura um logger para console e arquivo.
        
        Returns:
            Logger configurado
        """
        logger = logging.getLogger("VideoPipeline")
        logger.setLevel(logging.DEBUG)
        
        # Evita handlers duplicados
        if logger.hasHandlers():
            logger.handlers.clear()

        # Formato do Log com mais informações
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)-8s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Handler de Console (colorido e mais limpo)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # Handler de Arquivo (log detalhado)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"pipeline_{timestamp}.log"
        fh = logging.FileHandler(log_filename, mode='w', encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        return logger
    
    def _log_separator(self, char="=", titulo=None):
        """
        Imprime um separador visual nos logs.
        
        Args:
            char: Caractere para o separador
            titulo: Título opcional centralizado
        """
        largura = 80
        if titulo:
            linha = char * largura
            self.logger.info(linha)
            self.logger.info(f"{titulo:^{largura}}")
            self.logger.info(linha)
        else:
            self.logger.info(char * largura)
    
    def _validar_configuracao(self):
        """Valida se a configuração possui os campos necessários."""
        campos_obrigatorios = ['models', 'audio', 'video', 'json_file', 'output_folder']
        
        for campo in campos_obrigatorios:
            if campo not in self.config:
                raise ValueError(f"Campo obrigatório '{campo}' não encontrado no config.json")
        
        self.logger.debug("Configuração validada com sucesso")
    
    def _formatar_tempo(self, segundos):
        """
        Formata tempo em segundos para formato legível.
        
        Args:
            segundos: Tempo em segundos
            
        Returns:
            String formatada (ex: "2m 35s" ou "45s")
        """
        if segundos >= 60:
            minutos = int(segundos // 60)
            segs = int(segundos % 60)
            return f"{minutos}m {segs}s"
        else:
            return f"{segundos:.1f}s"

    def _gerar_audio(self, texto_narracao, arquivo_saida):
        """
        ETAPA 1: Gera o áudio da narração usando o TTS com clonagem de voz.
        
        Args:
            texto_narracao: Texto a ser convertido em áudio
            arquivo_saida: Caminho do arquivo de áudio a ser gerado
            
        Returns:
            Caminho do arquivo de áudio gerado ou None em caso de erro
        """
        inicio = time.perf_counter()
        
        self.logger.info("┌─────────────────────────────────────────────────────────────┐")
        self.logger.info("│  ETAPA 1: GERAÇÃO DE ÁUDIO (TTS)                          │")
        self.logger.info("└─────────────────────────────────────────────────────────────┘")
        
        try:
            # Informações sobre o texto
            num_palavras = len(texto_narracao.split())
            num_caracteres = len(texto_narracao)
            self.logger.info(f"📝 Texto da narração: {num_caracteres} caracteres, {num_palavras} palavras")
            
            # Carrega o modelo TTS (apenas na primeira vez)
            if self.modelo_tts is None:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self.logger.info(f"🔧 Inicializando modelo TTS: {self.config['models']['tts']}")
                self.logger.info(f"🖥️  Dispositivo: {device.upper()}")
                
                inicio_carregamento = time.perf_counter()
                self.modelo_tts = TTS(self.config['models']['tts'])
                self.modelo_tts.to(device)
                tempo_carregamento = time.perf_counter() - inicio_carregamento
                
                self.logger.info(f"✓ Modelo TTS carregado em {self._formatar_tempo(tempo_carregamento)}")
            else:
                self.logger.info("✓ Usando modelo TTS já carregado")

            # Define o speaker (clonagem de voz ou padrão)
            speaker_args = {}
            voz_clone_path = self.config['audio']['voice_clone_wav']
            
            if os.path.exists(voz_clone_path):
                self.logger.info(f"🎤 Clonagem de voz: {Path(voz_clone_path).name}")
                speaker_args['speaker_wav'] = voz_clone_path
            else:
                self.logger.warning(f"⚠️  Arquivo '{voz_clone_path}' não encontrado")
                self.logger.info("🎤 Usando voz padrão: Ana Florence")
                speaker_args['speaker'] = "Ana Florence"

            # Gera o áudio
            self.logger.info("🔊 Sintetizando áudio...")
            inicio_sintese = time.perf_counter()
            
            self.modelo_tts.tts_to_file(
                text=texto_narracao,
                language=self.config['audio']['language'],
                file_path=arquivo_saida,
                **speaker_args
            )
            
            tempo_sintese = time.perf_counter() - inicio_sintese
            tempo_total = time.perf_counter() - inicio
            
            # Informações sobre o arquivo gerado
            tamanho_arquivo = os.path.getsize(arquivo_saida) / (1024 * 1024)  # MB
            self.logger.info(f"✓ Áudio gerado com sucesso!")
            self.logger.info(f"  ├─ Arquivo: {Path(arquivo_saida).name}")
            self.logger.info(f"  ├─ Tamanho: {tamanho_arquivo:.2f} MB")
            self.logger.info(f"  ├─ Tempo de síntese: {self._formatar_tempo(tempo_sintese)}")
            self.logger.info(f"  └─ Tempo total: {self._formatar_tempo(tempo_total)}")
            
            self.stats['tempo_audio'].append(tempo_total)
            return arquivo_saida
            
        except Exception as e:
            tempo_total = time.perf_counter() - inicio
            self.logger.error(f"✗ ERRO ao gerar áudio após {self._formatar_tempo(tempo_total)}: {e}", exc_info=True)
            return None

    def _gerar_imagens(self, prompts_cenas, pasta_saida):
        """
        ETAPA 2: Gera as imagens de cada cena usando Stable Diffusion.
        
        Args:
            prompts_cenas: Lista de prompts para cada cena
            pasta_saida: Pasta onde as imagens serão salvas
            
        Returns:
            Lista com caminhos das imagens geradas ou None em caso de erro
        """
        inicio = time.perf_counter()
        
        self.logger.info("┌─────────────────────────────────────────────────────────────┐")
        self.logger.info("│  ETAPA 2: GERAÇÃO DE IMAGENS (Stable Diffusion)           │")
        self.logger.info("└─────────────────────────────────────────────────────────────┘")
        
        os.makedirs(pasta_saida, exist_ok=True)
        self.logger.info(f"📁 Pasta de saída: {pasta_saida}")
        
        try:
            num_cenas = len(prompts_cenas)
            self.logger.info(f"🎨 Total de cenas a gerar: {num_cenas}")
            
            # Carrega o modelo T2I
            self.logger.info(f"🔧 Carregando modelo: {self.config['models']['t2i']}")
            inicio_carregamento = time.perf_counter()
            
            self.modelo_t2i = StableDiffusionPipeline.from_pretrained(
                self.config['models']['t2i'],
                torch_dtype=torch.float16
            ).to("cuda")
            
            tempo_carregamento = time.perf_counter() - inicio_carregamento
            self.logger.info(f"✓ Modelo carregado na GPU em {self._formatar_tempo(tempo_carregamento)}")

            # Configuração de geração
            prompt_negativo = "blurry, low quality, deformed, disfigured, text, watermark, (bad-artist:1.2), (worst quality:1.2)"
            self.logger.info(f"⚙️  Inference steps: 25 | Guidance scale: 7.5")
            
            paths_imagens = []
            tempos_por_cena = []

            # Gera cada imagem
            for i, prompt in enumerate(prompts_cenas, 1):
                inicio_cena = time.perf_counter()
                
                # Trunca o prompt para exibição
                prompt_display = prompt[:60] + "..." if len(prompt) > 60 else prompt
                self.logger.info(f"🖼️  Cena {i}/{num_cenas}: {prompt_display}")
                
                imagem = self.modelo_t2i(
                    prompt,
                    negative_prompt=prompt_negativo,
                    num_inference_steps=25,
                    guidance_scale=7.5,
                    width=768,
                    height=1024
                ).images[0]
                
                caminho_img = os.path.join(pasta_saida, f"cena_{i:02d}.png")
                imagem.save(caminho_img)
                paths_imagens.append(caminho_img)
                
                tempo_cena = time.perf_counter() - inicio_cena
                tempos_por_cena.append(tempo_cena)
                
                # Calcula tempo estimado restante
                tempo_medio = sum(tempos_por_cena) / len(tempos_por_cena)
                cenas_restantes = num_cenas - i
                tempo_estimado = tempo_medio * cenas_restantes
                
                self.logger.info(f"  ✓ Concluída em {self._formatar_tempo(tempo_cena)}")
                if cenas_restantes > 0:
                    self.logger.info(f"  ⏱️  Estimativa restante: {self._formatar_tempo(tempo_estimado)}")

            tempo_total = time.perf_counter() - inicio
            tempo_medio_final = tempo_total / num_cenas
            
            self.logger.info(f"✓ Todas as imagens geradas com sucesso!")
            self.logger.info(f"  ├─ Total de imagens: {num_cenas}")
            self.logger.info(f"  ├─ Tempo total: {self._formatar_tempo(tempo_total)}")
            self.logger.info(f"  └─ Tempo médio por imagem: {self._formatar_tempo(tempo_medio_final)}")
            
            self.stats['tempo_imagens'].append(tempo_total)
            return paths_imagens

        except Exception as e:
            tempo_total = time.perf_counter() - inicio
            self.logger.error(f"✗ ERRO ao gerar imagens após {self._formatar_tempo(tempo_total)}: {e}", exc_info=True)
            return None
        
        finally:
            # Libera a VRAM da GPU
            if self.modelo_t2i:
                self.logger.info("🧹 Liberando VRAM da GPU...")
                del self.modelo_t2i
                self.modelo_t2i = None
                torch.cuda.empty_cache()
                self.logger.info("✓ VRAM liberada")

    def _montar_video(self, paths_imagens, path_audio, legendas_texto, arquivo_saida):
        """
        ETAPA 3: Monta o vídeo final com música, legendas e transições.
        
        Args:
            paths_imagens: Lista de caminhos das imagens
            path_audio: Caminho do arquivo de áudio
            legendas_texto: Lista de legendas para cada cena
            arquivo_saida: Caminho do vídeo final
            
        Returns:
            True se sucesso, False caso contrário
        """
        inicio = time.perf_counter()
        
        self.logger.info("┌─────────────────────────────────────────────────────────────┐")
        self.logger.info("│  ETAPA 3: MONTAGEM DO VÍDEO (MoviePy)                     │")
        self.logger.info("└─────────────────────────────────────────────────────────────┘")
        
        try:
            # Carrega narração
            self.logger.info(f"🔊 Carregando áudio: {Path(path_audio).name}")
            audio_clip = AudioFileClip(path_audio)
            duracao_total = audio_clip.duration
            self.logger.info(f"  └─ Duração: {self._formatar_tempo(duracao_total)}")
            
            # Carrega e mixa música de fundo
            musica_path = self.config['audio']['music_file']
            if os.path.exists(musica_path):
                musica_vol = self.config['audio']['music_volume']
                self.logger.info(f"🎵 Adicionando música de fundo: {Path(musica_path).name}")
                self.logger.info(f"  └─ Volume: {musica_vol * 100:.0f}%")
                
                musica_fundo = AudioFileClip(musica_path).volumex(musica_vol)
                
                if musica_fundo.duration < duracao_total:
                    musica_fundo = musica_fundo.fx(vfx.loop, duration=duracao_total)
                    self.logger.info(f"  └─ Música em loop para cobrir {self._formatar_tempo(duracao_total)}")
                else:
                    musica_fundo = musica_fundo.subclip(0, duracao_total)
                
                audio_clip = CompositeAudioClip([audio_clip, musica_fundo])
                self.logger.info("  ✓ Música mixada com sucesso")
            else:
                self.logger.warning(f"⚠️  Música '{musica_path}' não encontrada - vídeo sem música de fundo")

            # Configurações do vídeo
            num_cenas = len(paths_imagens)
            duracao_por_cena = math.ceil(duracao_total / num_cenas * 10) / 10
            w_video, h_video = self.config['video']['format']
            trans_duration = self.config['video']['transition_duration']
            
            self.logger.info(f"⚙️  Configurações do vídeo:")
            self.logger.info(f"  ├─ Resolução: {w_video}x{h_video}")
            self.logger.info(f"  ├─ FPS: {self.config['video']['fps']}")
            self.logger.info(f"  ├─ Cenas: {num_cenas}")
            self.logger.info(f"  ├─ Duração por cena: {duracao_por_cena:.1f}s")
            self.logger.info(f"  └─ Transição: {trans_duration}s crossfade")

            # Prepara clips
            self.logger.info("🎬 Processando clips...")
            clips_finais = []

            for i, path_img in enumerate(paths_imagens):
                # Progresso a cada 25%
                progresso = (i + 1) / num_cenas * 100
                if progresso % 25 == 0 or i == 0 or i == num_cenas - 1:
                    self.logger.info(f"  └─ Processando clip {i+1}/{num_cenas} ({progresso:.0f}%)")
                
                # 1. Imagem com efeito Ken Burns (Zoom)
                clip_imagem = ImageClip(path_img).set_duration(duracao_por_cena)
                clip_resized = clip_imagem.resize(height=h_video)#clip_zoom = clip_imagem.resize(1.2)

                clip_animado = clip_resized.resize(lambda t: 1 + 0.1 * t).set_pos(('center', 'center'))
                clip_cortado = vfx.crop(clip_animado, width=w_video, height=h_video, x_center=clip_animado.w/2, y_center=clip_animado.h/2)            

                # 2. Legenda (se existir)
                legenda_txt = legendas_texto[i] if i < len(legendas_texto) else ""
                
                if legenda_txt:
                    clip_legenda = TextClip(
                        legenda_txt,
                        fontsize=self.config['video']['caption_fontsize'],
                        color='white',
                        font=self.config['video']['caption_font'],
                        stroke_color='black',
                        stroke_width=self.config['video']['caption_stroke'],
                        method='caption',
                        size=(w_video * 0.9, None)
                    ).set_position(('center', h_video * 0.75)).set_duration(duracao_por_cena)

                    # 3. Combina imagem e legenda
                    cena_final = CompositeVideoClip([clip_cortado, clip_legenda])
                else:
                    cena_final = clip_cortado
                
                # 4. Adiciona transição (Crossfade)
                if i > 0:
                    cena_final = cena_final.set_start((i * duracao_por_cena) - trans_duration).crossfadein(trans_duration)
                
                clips_finais.append(cena_final)

            # 5. Monta o vídeo final
            self.logger.info("🎞️  Concatenando clips e adicionando áudio...")
            video_final = CompositeVideoClip(clips_finais, size=(w_video, h_video)).set_audio(audio_clip)
            video_final.duration = duracao_total
            
            self.logger.info(f"📽️  Renderizando vídeo final...")
            self.logger.info(f"  ├─ Codec vídeo: libx264")
            self.logger.info(f"  ├─ Codec áudio: aac")
            self.logger.info(f"  └─ Threads: {self.config['video']['threads']}")
            
            inicio_render = time.perf_counter()
            video_final.write_videofile(
                arquivo_saida,
                codec="libx264",
                audio_codec="aac",
                fps=self.config['video']['fps'],
                threads=self.config['video']['threads'],
                logger='bar'  # Mostra a barra de progresso
            )
            tempo_render = time.perf_counter() - inicio_render
            
            tempo_total = time.perf_counter() - inicio
            tamanho_video = os.path.getsize(arquivo_saida) / (1024 * 1024)  # MB
            
            self.logger.info(f"✓ Vídeo montado com sucesso!")
            self.logger.info(f"  ├─ Arquivo: {Path(arquivo_saida).name}")
            self.logger.info(f"  ├─ Tamanho: {tamanho_video:.2f} MB")
            self.logger.info(f"  ├─ Tempo de render: {self._formatar_tempo(tempo_render)}")
            self.logger.info(f"  └─ Tempo total: {self._formatar_tempo(tempo_total)}")
            
            self.stats['tempo_montagem'].append(tempo_total)
            return True

        except Exception as e:
            tempo_total = time.perf_counter() - inicio
            self.logger.error(f"✗ ERRO ao montar vídeo após {self._formatar_tempo(tempo_total)}: {e}", exc_info=True)
            return False

    def run_batch(self):
        """
        Executa o pipeline em lote para todas as histórias no arquivo JSON.
        Processa cada vídeo sequencialmente e exibe estatísticas detalhadas.
        """
        self._log_separator("=", "INICIANDO PROCESSAMENTO EM LOTE")
        
        # Carrega arquivo de histórias
        self.logger.info(f"📂 Carregando histórias de: {self.config['json_file']}")
        os.makedirs(self.config['output_folder'], exist_ok=True)
        
        try:
            with open(self.config['json_file'], 'r', encoding='utf-8') as f:
                todas_as_historias = json.load(f)
            self.logger.info(f"✓ Arquivo carregado com sucesso")
        except Exception as e:
            self.logger.error(f"✗ ERRO CRÍTICO: Não foi possível ler {self.config['json_file']}. {e}")
            return

        total_videos = len(todas_as_historias)
        self.logger.info(f"📊 Total de vídeos para processar: {total_videos}")
        self.logger.info(f"📁 Pasta de saída: {self.config['output_folder']}")
        
        # Inicia processamento
        start_time_total = time.perf_counter()
        videos_sucesso = 0
        videos_erro = 0
        lista_erros = []

        for i, historia in enumerate(todas_as_historias):
            start_time_video = time.perf_counter()
            id_video = historia.get("id_video", f"video_{i+1:03d}")
            
            self._log_separator("=", f"VÍDEO {i+1}/{total_videos}: {id_video}")
            
            try:
                # Define os caminhos
                pasta_base = self.config['output_folder']
                arquivo_audio = os.path.join(pasta_base, f"{id_video}_audio.wav")
                pasta_imagens = os.path.join(pasta_base, f"imagens_{id_video}")
                arquivo_video = os.path.join(pasta_base, f"{id_video}_video_final.mp4")

                # Extrai dados do JSON
                narracao = historia["historia_completa"]
                cenas = historia["cenas"]
                legendas = historia.get("legendas", [])

                self.logger.info(f"📋 Informações do vídeo:")
                self.logger.info(f"  ├─ ID: {id_video}")
                self.logger.info(f"  ├─ Número de cenas: {len(cenas)}")
                self.logger.info(f"  ├─ Número de legendas: {len(legendas)}")
                self.logger.info(f"  └─ Tamanho da narração: {len(narracao)} caracteres")

                if len(cenas) != len(legendas) and len(legendas) > 0:
                    self.logger.warning(f"⚠️  Número de cenas ({len(cenas)}) ≠ legendas ({len(legendas)})")

                # --- EXECUTANDO O PIPELINE ---
                
                # ETAPA 1: ÁUDIO
                path_audio = self._gerar_audio(narracao, arquivo_audio)
                if not path_audio:
                    raise Exception("Falha na Etapa 1: Geração de Áudio")
                
                # ETAPA 2: IMAGENS
                paths_imagens = self._gerar_imagens(cenas, pasta_imagens)
                if not paths_imagens:
                    raise Exception("Falha na Etapa 2: Geração de Imagens")
                
                # ETAPA 3: MONTAGEM
                sucesso_montagem = self._montar_video(paths_imagens, path_audio, legendas, arquivo_video)
                if not sucesso_montagem:
                    raise Exception("Falha na Etapa 3: Montagem do Vídeo")

                # Conclusão do vídeo
                end_time_video = time.perf_counter()
                tempo_video = end_time_video - start_time_video
                
                self._log_separator("=")
                self.logger.info(f"✅ VÍDEO {i+1}/{total_videos} CONCLUÍDO COM SUCESSO!")
                self.logger.info(f"  ├─ ID: {id_video}")
                self.logger.info(f"  ├─ Tempo total: {self._formatar_tempo(tempo_video)}")
                
                # Estimativa de tempo restante
                if videos_sucesso + videos_erro > 0:
                    tempo_decorrido = time.perf_counter() - start_time_total
                    videos_processados = videos_sucesso + videos_erro + 1
                    tempo_medio = tempo_decorrido / videos_processados
                    videos_restantes = total_videos - videos_processados
                    tempo_estimado = tempo_medio * videos_restantes
                    
                    self.logger.info(f"  └─ Tempo estimado restante: {self._formatar_tempo(tempo_estimado)}")
                
                self._log_separator("=")
                
                videos_sucesso += 1

            except Exception as e:
                # Error handling por vídeo
                end_time_video = time.perf_counter()
                tempo_video = end_time_video - start_time_video
                
                erro_info = {
                    'id': id_video,
                    'indice': i + 1,
                    'erro': str(e)
                }
                lista_erros.append(erro_info)
                
                self._log_separator("=")
                self.logger.error(f"❌ VÍDEO {i+1}/{total_videos} FALHOU!")
                self.logger.error(f"  ├─ ID: {id_video}")
                self.logger.error(f"  ├─ Tempo até falha: {self._formatar_tempo(tempo_video)}")
                self.logger.error(f"  └─ Erro: {e}")
                self._log_separator("=")
                
                videos_erro += 1
                # Continua para o próximo vídeo
                continue 

        # === RESUMO FINAL ===
        end_time_total = time.perf_counter()
        tempo_total = end_time_total - start_time_total
        
        self._log_separator("=", "RESUMO FINAL DO PROCESSAMENTO")
        
        self.logger.info(f"⏱️  Tempo total de execução: {self._formatar_tempo(tempo_total)}")
        self.logger.info(f"")
        self.logger.info(f"📊 Estatísticas:")
        self.logger.info(f"  ├─ Total processado: {total_videos}")
        self.logger.info(f"  ├─ ✅ Sucessos: {videos_sucesso} ({videos_sucesso/total_videos*100:.1f}%)")
        self.logger.info(f"  └─ ❌ Erros: {videos_erro} ({videos_erro/total_videos*100:.1f}%)")
        
        if videos_sucesso > 0:
            self.logger.info(f"")
            self.logger.info(f"⏱️  Tempos médios por etapa:")
            
            if self.stats['tempo_audio']:
                media_audio = sum(self.stats['tempo_audio']) / len(self.stats['tempo_audio'])
                self.logger.info(f"  ├─ Áudio (TTS): {self._formatar_tempo(media_audio)}")
            
            if self.stats['tempo_imagens']:
                media_imagens = sum(self.stats['tempo_imagens']) / len(self.stats['tempo_imagens'])
                self.logger.info(f"  ├─ Imagens (SD): {self._formatar_tempo(media_imagens)}")
            
            if self.stats['tempo_montagem']:
                media_montagem = sum(self.stats['tempo_montagem']) / len(self.stats['tempo_montagem'])
                self.logger.info(f"  └─ Montagem: {self._formatar_tempo(media_montagem)}")
            
            tempo_medio_total = tempo_total / videos_sucesso
            self.logger.info(f"")
            self.logger.info(f"📈 Tempo médio por vídeo (sucesso): {self._formatar_tempo(tempo_medio_total)}")
        
        if videos_erro > 0:
            self.logger.info(f"")
            self.logger.warning(f"⚠️  Vídeos com erro:")
            for erro in lista_erros:
                self.logger.warning(f"  ├─ #{erro['indice']}: {erro['id']} - {erro['erro']}")
        
        self.logger.info(f"")
        self.logger.info(f"📁 Arquivos salvos em: {os.path.abspath(self.config['output_folder'])}")
        
        self._log_separator("=", "PIPELINE FINALIZADO")
        
        # Retorna estatísticas
        return {
            'total': total_videos,
            'sucesso': videos_sucesso,
            'erro': videos_erro,
            'tempo_total': tempo_total,
            'erros': lista_erros
        }


if __name__ == "__main__":
    """Ponto de entrada principal do script"""
    try:
        print("\n" + "="*80)
        print("  🎬 PIPELINE DE GERAÇÃO AUTOMÁTICA DE VÍDEOS 🎬")
        print("="*80 + "\n")
        
        pipeline = VideoPipeline(config_path="config.json")
        resultados = pipeline.run_batch()
        
        # Código de saída baseado nos resultados
        if resultados:
            if resultados['erro'] == 0:
                print("\n✅ Todos os vídeos foram processados com sucesso!\n")
                exit(0)
            elif resultados['sucesso'] > 0:
                print(f"\n⚠️  Processamento concluído com {resultados['erro']} erro(s)\n")
                exit(1)
            else:
                print("\n❌ Nenhum vídeo foi processado com sucesso\n")
                exit(2)
        else:
            print("\n❌ Falha ao iniciar o processamento\n")
            exit(3)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrompido pelo usuário (Ctrl+C)\n")
        exit(130)
        
    except Exception as e:
        # Pega erros fatais (ex: config.json não encontrado)
        print(f"\n❌ ERRO FATAL: {e}\n")
        logging.critical(f"Uma falha crítica impediu o pipeline de iniciar: {e}", exc_info=True)
        exit(4)