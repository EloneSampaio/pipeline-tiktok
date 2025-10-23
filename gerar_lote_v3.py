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
from diffusers import StableDiffusionPipeline,StableDiffusionImg2ImgPipeline
from moviepy.editor import *
from PIL import Image
import random
import subprocess

# Importa o gerador de legendas separado
from legenda_generator import LegendaGenerator

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
        NOTA: O modelo é carregado e descarregado da VRAM a cada chamada
        para liberar memória para a Etapa 2 (Imagens).
        """
        inicio = time.perf_counter()
        
        self.logger.info("┌─────────────────────────────────────────────────────────────┐")
        self.logger.info("│  ETAPA 1: GERAÇÃO DE ÁUDIO (TTS)                          │")
        self.logger.info("└─────────────────────────────────────────────────────────────┘")
        
        # --- MUDANÇA: Modelo TTS agora é uma variável local ---
        tts = None 
        
        try:
            # Informações sobre o texto
            num_palavras = len(texto_narracao.split())
            num_caracteres = len(texto_narracao)
            self.logger.info(f"📝 Texto da narração: {num_caracteres} caracteres, {num_palavras} palavras")
            
            # --- MUDANÇA: O modelo agora é carregado TODA VEZ ---
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.logger.info(f"🔧 Inicializando modelo TTS: {self.config['models']['tts']}")
            self.logger.info(f"🖥️  Dispositivo: {device.upper()}")
            
            inicio_carregamento = time.perf_counter()
            
            # Carrega na variável local 'tts', não em 'self.modelo_tts'
            tts = TTS(self.config['models']['tts']) 
            tts.to(device)

            # --- ADICIONE ESTA LINHA ---
            self._log_vram_usage(log_prefix="[TTS Carregado]")
            
            tempo_carregamento = time.perf_counter() - inicio_carregamento
            self.logger.info(f"✓ Modelo TTS carregado em {self._formatar_tempo(tempo_carregamento)}")
            
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
            
            tts.tts_to_file( # Usa a variável local 'tts'
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
            
        finally:
            # --- MUDANÇA: A PARTE MAIS IMPORTANTE ---
            # Limpa a VRAM DEPOIS que a função termina (com sucesso ou erro)
            if tts is not None:
                del tts
                torch.cuda.empty_cache()
                # --- ADICIONE ESTA LINHA ---
                # --- ADICIONE ESTA LINHA ---
                self._log_vram_usage(log_prefix="[Pipe Descarregado]")
                self._log_vram_usage(log_prefix="[TTS descarregado]")
                self.logger.info("✓ Modelo TTS descarregado da VRAM.")

    def _gerar_imagens(self, lista_cenas, pasta_saida):
        """
        ETAPA 2: Gera imagens em modo HÍBRIDO (T2I ou I2I)
        com GERENCIAMENTO INTELIGENTE DE VRAM para 6GB.
        """
        self.logger.info(f"Iniciando Etapa 2 (Híbrida) com {self.config['models']['t2i']}")
        os.makedirs(pasta_saida, exist_ok=True)
        
        # --- Configurações ---
        modelo_id = self.config['models']['t2i']
        t2i_altura = 1024
        t2i_largura = 768
        i2i_strength = 0.7  # 0.6 = mais parecido com a base, 0.8 = mais diferente

        # --- Lógica de Gerenciamento de VRAM ---
        current_pipe = None
        current_pipe_type = None # "t2i" ou "i2i"
        # --- Fim da Lógica ---

        try:
            prompt_negativo = "blurry, low quality, deformed, disfigured, text, watermark, (bad-artist:1.2), (worst quality:1.2)"
            paths_imagens = []

            for i, cena in enumerate(lista_cenas):
                prompt = cena["prompt"]
                caminho_img_saida = os.path.join(pasta_saida, f"cena_{i+1:02d}.png")
                
                # 1. Decide qual pipeline é necessário para esta cena
                needed_pipe_type = "t2i" # Padrão
                if "imagem_base" in cena and os.path.exists(cena["imagem_base"]):
                    needed_pipe_type = "i2i"

                # 2. Verifica se precisamos "trocar" o modelo na VRAM
                if current_pipe_type != needed_pipe_type:
                    self.logger.info(f"Trocando pipeline na VRAM para: {needed_pipe_type.upper()}")
                    
                    # Se um modelo já existe (ex: o T2I), remove ele da VRAM
                    if current_pipe is not None:
                        del current_pipe
                        torch.cuda.empty_cache()
                        self.logger.info("VRAM liberada.")
                    
                    # Carrega o NOVO modelo necessário
                    if needed_pipe_type == "t2i":
                        current_pipe = StableDiffusionPipeline.from_pretrained(
                            modelo_id, torch_dtype=torch.float16
                        ).to("cuda")
                    else: # needed_pipe_type == "i2i"
                        current_pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
                            modelo_id, torch_dtype=torch.float16
                        ).to("cuda")
                    
                    current_pipe_type = needed_pipe_type

                    self._log_vram_usage(log_prefix=f"[{current_pipe_type.upper()} Carregado]")
                    self.logger.info(f"Modelo {current_pipe_type.upper()} carregado na VRAM.")
                # --- Fim da Lógica de Troca ---

                # 3. Gera a imagem com o pipeline que está na VRAM
                if current_pipe_type == "i2i":
                    # --- MODO I2I ---
                    self.logger.info(f"Gerando cena {i+1} (Modo I2I) com base em: {cena['imagem_base']}")
                    imagem_base = Image.open(cena["imagem_base"]).convert("RGB").resize((t2i_largura, t2i_altura))
                    
                    imagem = current_pipe(
                        prompt,
                        image=imagem_base,
                        strength=i2i_strength,
                        guidance_scale=7.5,
                        negative_prompt=prompt_negativo,
                        num_inference_steps=30
                    ).images[0]
                
                else: 
                    # --- MODO T2I ---
                    if "imagem_base" in cena: # Avisa se a imagem_base não foi encontrada
                        self.logger.warning(f"Cena {i+1} (Modo T2I) - Imagem base '{cena['imagem_base']}' não encontrada. Gerando do zero.")
                    else:
                        self.logger.info(f"Gerando cena {i+1} (Modo T2I) do zero.")

                    imagem = current_pipe(
                        prompt,
                        negative_prompt=prompt_negativo,
                        num_inference_steps=25,
                        guidance_scale=7.5,
                        height=t2i_altura,
                        width=t2i_largura
                    ).images[0]

                # Salva a imagem gerada
                imagem.save(caminho_img_saida)
                paths_imagens.append(caminho_img_saida)

            self.logger.info(f"Imagens salvas em: {pasta_saida}")
            return paths_imagens

        except Exception as e:
            self.logger.error(f"ERRO ao gerar imagens: {e}", exc_info=True)
            return None
        
        finally:
            # Libera a VRAM da GPU no final de tudo
            if current_pipe is not None:
                del current_pipe
                torch.cuda.empty_cache()
                self._log_vram_usage(log_prefix="[Pipe Final Descarregado]")
                self.logger.info("VRAM final liberada (pós-loop).")

    def _montar_video(self, paths_imagens, path_audio, arquivo_saida):
        """
        ETAPA 3: Monta o vídeo base (SEM LEGENDAS).
        - Música de fundo
        - Ken Burns Dinâmico (Zoom/Pan Aleatório)
        - Transições Crossfade
        """
        self.logger.info("┌─────────────────────────────────────────────────────────────┐")
        self.logger.info("│  ETAPA 3: MONTAGEM DO VÍDEO BASE (SEM LEGENDAS)           │")
        self.logger.info("└─────────────────────────────────────────────────────────────┘")
        inicio = time.perf_counter()
        
        try:
            # 1. CARREGAR ÁUDIOS
            self.logger.info(f"Carregando áudio de: {Path(path_audio).name}")
            audio_clip = AudioFileClip(path_audio)
            duracao_total = audio_clip.duration
            
            musica_path = self.config['audio']['music_file']
            if os.path.exists(musica_path):
                musica_vol = self.config['audio']['music_volume']
                musica_fundo = AudioFileClip(musica_path).volumex(musica_vol)
                
                if musica_fundo.duration < duracao_total:
                    musica_fundo = musica_fundo.fx(vfx.loop, duration=duracao_total)
                else:
                    musica_fundo = musica_fundo.subclip(0, duracao_total)
                
                audio_clip = CompositeAudioClip([audio_clip, musica_fundo])
                self.logger.info(f"Música de fundo '{musica_path}' adicionada.")
            else:
                self.logger.warning(f"⚠️  Música de fundo '{musica_path}' não encontrada.")

            # 2. PREPARAR CENAS
            num_cenas = len(paths_imagens)
            duracao_por_cena = duracao_total / num_cenas
            
            self.logger.info(f"Duração total do áudio: {duracao_total:.2f}s | Cenas: {num_cenas} | Duração/Cena: {duracao_por_cena:.2f}s")

            clips_finais = []
            w_video, h_video = self.config['video']['format']

            for i, path_img in enumerate(paths_imagens):
                self.logger.debug(f"Processando cena {i+1}/{num_cenas}")
                
                clip_imagem = ImageClip(path_img).set_duration(duracao_por_cena)
                clip_resized = clip_imagem.resize(height=h_video)
                clip_zoomed = clip_resized.resize(1.1)
                
                clip_animado = self._apply_ken_burns(clip_zoomed, duracao_por_cena, w_video, h_video)
                clip_cortado = vfx.crop(clip_animado, width=w_video, height=h_video, x_center=clip_animado.w/2, y_center=clip_animado.h/2)

                # 3. COMBINA IMAGEM (NÃO HÁ MAIS LEGENDAS AQUI)
                cena_final = CompositeVideoClip([clip_cortado])
                
                # 4. Adiciona transição (Crossfade)
                trans_duration = self.config['video']['transition_duration']
                if i > 0:
                    cena_final = cena_final.set_start((i * duracao_por_cena) - trans_duration).crossfadein(trans_duration)
                
                clips_finais.append(cena_final)

            # 5. Monta o vídeo final
            video_final = CompositeVideoClip(clips_finais, size=(w_video, h_video)).set_audio(audio_clip)
            video_final.duration = duracao_total
            
            self.logger.info("🎬 Renderizando vídeo base (sem legendas)...")
            
            video_final.write_videofile(
                arquivo_saida,
                codec="libx264",
                audio_codec="aac",
                fps=self.config['video']['fps'],
                threads=self.config['video']['threads'],
                logger='bar'
            )
            
            tempo_total = time.perf_counter() - inicio
            self.logger.info(f"✓ Montagem do vídeo base concluída!")
            # ... (seus logs de stats, etc) ...
            return True

        except Exception as e:
            tempo_total = time.perf_counter() - inicio
            self.logger.error(f"✗ ERRO ao montar vídeo base após {self._formatar_tempo(tempo_total)}: {e}", exc_info=True)
            return False
        

    def _etapa_4_legendas_whisper_ffmpeg(self, arquivo_video_base, arquivo_saida_final, legendar_em_ingles=True):
        """
        ETAPA 4: Usa a classe LegendaGenerator para adicionar legendas estilo TikTok.
        Código refatorado para melhor organização e reutilização.
        Lê configurações de estilo do config.json.
        """
        try:
            # Obtém configurações do config.json
            modelo_whisper = self.config['video'].get('whisper_model', 'small')
            config_legendas = self.config.get('legendas', {})
            
            # Cria instância do gerador com o logger do pipeline
            gerador = LegendaGenerator(modelo_whisper=modelo_whisper, logger=self.logger)
            
            # Gera as legendas com configurações customizadas
            sucesso = gerador.gerar_legendas(
                arquivo_video_entrada=arquivo_video_base,
                arquivo_video_saida=arquivo_saida_final,
                traduzir_para_ingles=legendar_em_ingles,
                max_palavras_por_linha=config_legendas.get('max_palavras_por_linha', 3),
                font=config_legendas.get('font', 'Impact'),
                font_size=config_legendas.get('font_size', 70),
                font_color=config_legendas.get('font_color', '#FFFFFF'),
                stroke_width=config_legendas.get('stroke_width', 4),
                stroke_color=config_legendas.get('stroke_color', '#000000'),
                shadow_strength=config_legendas.get('shadow_strength', 2),
                highlight_current_word=config_legendas.get('highlight_current_word', False),
                word_highlight_color=config_legendas.get('word_highlight_color', '#FFFF00'),
                padding=config_legendas.get('padding', 80),
                manter_arquivo_ass=False
            )
            
            return sucesso
            
        except Exception as e:
            self.logger.error(f"✗ ERRO ao gerar legendas: {e}", exc_info=True)
            return False
    
    def _format_timestamp(self, seconds):
        """
        Converte segundos para formato de timestamp SRT (HH:MM:SS,mmm)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _etapa_4_legendas_captacity(self, arquivo_video_base, arquivo_saida_final, legendar_em_ingles=True):
        """
        ETAPA 4: Usa 'captacity' (Whisper) para gerar legendas profissionais,
        com opção de tradução.
        NOTA: Esta função tem problemas de compatibilidade com FFmpeg 7.x
        Use _etapa_4_legendas_whisper_ffmpeg() como alternativa.
        """
        self.logger.info("┌─────────────────────────────────────────────────────────────┐")
        self.logger.info("│  ETAPA 4: GERAÇÃO DE LEGENDAS (Captacity)                 │")
        self.logger.info("└─────────────────────────────────────────────────────────────┘")
        inicio = time.perf_counter()
        
        try:
            # Modelo 'small' é um bom equilíbrio entre velocidade e precisão
            # Se for lento, mude para 'base' ou 'tiny'
            modelo_whisper = self.config['video'].get('whisper_model', 'small')
            
            # --- LÓGICA DE TRADUÇÃO ---
            task = "transcribe" # Padrão: Português -> Português
            if legendar_em_ingles:
                task = "translate"
                self.logger.info("Modo de TRADUÇÃO ativado. (Áudio -> Legendas em Inglês)")
            else:
                self.logger.info("Modo de TRANSCRIÇÃO ativado. (Áudio -> Legendas no mesmo idioma)")

            
            # O comando que vamos rodar no terminal, via Python
            comando = [
                "captacity",
                arquivo_video_base,
                "--output", arquivo_saida_final,
                "--model", modelo_whisper,
                "--task", task, # <--- AQUI ESTÁ A MÁGICA
                "--font-color", "#FFFFFF",
                "--highlight-color", "#FFFF00", # Amarelo
                "--font", "Impact" # Fonte de "meme" (precisa estar instalada)
            ]
            
            self.logger.info(f"Executando 'captacity' com o modelo '{modelo_whisper}' e tarefa '{task}'...")
            self.logger.debug(f"Comando: {' '.join(comando)}")
            
            resultado = subprocess.run(comando, capture_output=True, text=True, check=True, encoding='utf-8')
            
            self.logger.info(f"Log do Captacity:\n{resultado.stderr}")
            
            tempo_total = time.perf_counter() - inicio
            self.logger.info(f"✓ Legendas profissionais adicionadas!")
            self.logger.info(f"  ├─ Arquivo Final: {Path(arquivo_saida_final).name}")
            self.logger.info(f"  └─ Tempo total: {self._formatar_tempo(tempo_total)}")
            
            # self.stats['tempo_legenda'].append(tempo_total) # Se você tiver essa stat
            return True

        except FileNotFoundError:
            self.logger.error("✗ ERRO: 'captacity' não encontrado. Você o instalou? (pip install captacity)")
            return False
        except subprocess.CalledProcessError as e:
            self.logger.error(f"✗ ERRO durante a execução do 'captacity':")
            self.logger.error(e.stderr) 
            return False
        except Exception as e:
            tempo_total = time.perf_counter() - inicio
            self.logger.error(f"✗ ERRO ao gerar legendas após {self._formatar_tempo(tempo_total)}: {e}", exc_info=True)
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
                
                # Nomes de arquivo para o pipeline de 2 passos
                arquivo_video_base = os.path.join(pasta_base, f"{id_video}_base_sem_legenda.mp4")
                arquivo_video_final = os.path.join(pasta_base, f"{id_video}_video_final.mp4")
                
                # Pega a opção de tradução do JSON (padrão é True)
                legendar_em_ingles = historia.get("legendar_em_ingles", True)

                # Extrai dados do JSON (NÃO PRECISA MAIS DE "legendas")
                narracao = historia["historia_completa"]
                cenas = historia["cenas"]
                
                # --- EXECUTANDO O PIPELINE ---
                
                # ETAPA 1: ÁUDIO
                path_audio = self._gerar_audio(narracao, arquivo_audio)
                if not path_audio:
                    raise Exception("Falha na Etapa 1: Geração de Áudio.")
                
                # ETAPA 2: IMAGENS
                paths_imagens = self._gerar_imagens(cenas, pasta_imagens)
                if not paths_imagens:
                    raise Exception("Falha na Etapa 2: Geração de Imagens.")
                
                # ETAPA 3: MONTAGEM (Sem Legendas)
                sucesso_montagem = self._montar_video(paths_imagens, path_audio, arquivo_video_base)
                if not sucesso_montagem:
                    raise Exception("Falha na Etapa 3: Montagem do Vídeo Base.")
                    
                # ETAPA 4: LEGENDAS (Whisper + FFmpeg - solução nativa mais estável)
                sucesso_legenda = self._etapa_4_legendas_whisper_ffmpeg(arquivo_video_base, arquivo_video_final, legendar_em_ingles)
                if not sucesso_legenda:
                    raise Exception("Falha na Etapa 4: Geração de Legendas.")

                # Conclusão do vídeo
                # ... (seu código de log de sucesso) ...
                videos_sucesso += 1

            except Exception as e:
                # ... (seu código de log de erro) ...
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
    
    def _apply_ken_burns(self, clip, clip_duration, w_video, h_video):
        """
        Aplica um efeito Ken Burns (Zoom/Pan) aleatório e profissional.
        A imagem de entrada (clip) JÁ DEVE ser maior que o frame do vídeo.
        """
        
        # 1. Decide o tipo de movimento aleatório
        # 0 = Zoom In (Lento)
        # 1 = Zoom Out (Lento)
        # 2 = Pan Esquerda-para-Direita
        # 3 = Pan Direita-para-Esquerda
        effect_type = random.randint(0, 3)
        
        # Pega as dimensões da imagem (que é maior que o vídeo)
        w_img, h_img = clip.size
        
        # 2. Define a função de animação (lambda t)
        
        if effect_type == 0: # Zoom In
            # Começa em 1.0x e termina em 1.1x
            def resize_func(t):
                return 1.0 + (t / clip_duration) * 0.1
            
            # Centraliza a imagem e deixa ela "crescer"
            return clip.resize(resize_func).set_pos(('center', 'center'))

        elif effect_type == 1: # Zoom Out
            # Começa em 1.1x e termina em 1.0x
            def resize_func(t):
                return 1.1 - (t / clip_duration) * 0.1
            
            return clip.resize(resize_func).set_pos(('center', 'center'))

        elif effect_type == 2: # Pan Esquerda-para-Direita
            # O `pos` (posição) é animado
            # Começa na esquerda (x=0) e termina na direita (x = w_video - w_img)
            def pos_func(t):
                # Posição X linearmente interpolada
                x_start = 0
                x_end = w_video - w_img
                x_pos = x_start + (t / clip_duration) * (x_end - x_start)
                return (x_pos, 'center')
                
            return clip.set_pos(pos_func)

        else: # effect_type == 3 (Pan Direita-para-Esquerda)
            # Começa na direita (x = w_video - w_img) e termina na esquerda (x=0)
            def pos_func(t):
                # Posição X linearmente interpolada
                x_start = w_video - w_img
                x_end = 0
                x_pos = x_start + (t / clip_duration) * (x_end - x_start)
                return (x_pos, 'center')
            
            return clip.set_pos(pos_func)
    def _log_vram_usage(self, log_prefix=""):
        """Helper para logar o uso atual da VRAM pela PyTorch."""
        # Esta função só faz algo se a CUDA (GPU NVIDIA) estiver sendo usada
        if torch.cuda.is_available():
            
            # Função interna para converter bytes (ex: 564000000) em Megabytes (ex: 537.88 MiB)
            def to_mb(bytes_val):
                return f"{bytes_val / 1024**2:.2f} MiB"

            # Pega a memória que o PyTorch está ATIVAMENTE usando agora
            allocated = torch.cuda.memory_allocated()
            
            # Pega a memória que o PyTorch "reservou" (cache)
            reserved = torch.cuda.memory_reserved()
            
            # Pega o total da GPU para dar contexto
            _, total = torch.cuda.mem_get_info()

            log_msg = (
                f"{log_prefix} "
                f"VRAM Alocada (Script): {to_mb(allocated)} | "
                f"VRAM Reservada (Script): {to_mb(reserved)} "
                f"(Total GPU: {to_mb(total)})"
            )
            # Loga a mensagem
            self.logger.info(log_msg)


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