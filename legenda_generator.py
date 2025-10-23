"""
Gerador de Legendas Profissionais para Vídeos
Usa Whisper para transcrição/tradução e FFmpeg para renderização
"""
import os
import time
import logging
import tempfile
import subprocess
from pathlib import Path


class LegendaGenerator:
    """
    Classe responsável por gerar legendas estilo TikTok usando Whisper + FFmpeg.
    Separada do pipeline principal para melhor organização e reutilização.
    """
    
    def __init__(self, modelo_whisper='small', logger=None):
        """
        Inicializa o gerador de legendas.
        
        Args:
            modelo_whisper: Nome do modelo Whisper ('tiny', 'base', 'small', 'medium', 'large')
            logger: Logger opcional para saída de logs
        """
        self.modelo_whisper = modelo_whisper
        self.logger = logger or self._criar_logger_padrao()
        self.model = None
    
    def _criar_logger_padrao(self):
        """Cria um logger padrão caso nenhum seja fornecido."""
        logger = logging.getLogger("LegendaGenerator")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)-8s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _carregar_modelo(self):
        """Carrega o modelo Whisper se ainda não estiver carregado."""
        if self.model is None:
            try:
                import whisper
                self.logger.info(f"Carregando modelo Whisper '{self.modelo_whisper}'...")
                self.model = whisper.load_model(self.modelo_whisper)
                self.logger.info("✓ Modelo Whisper carregado com sucesso")
            except ImportError:
                raise ImportError(
                    "Módulo 'whisper' não encontrado. "
                    "Instale com: pip install openai-whisper"
                )
    
    def _descarregar_modelo(self):
        """Descarrega o modelo Whisper da memória."""
        if self.model is not None:
            import torch
            del self.model
            self.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            self.logger.info("✓ Modelo Whisper descarregado da memória")
    
    def _transcrever_audio(self, arquivo_video, traduzir_para_ingles=True):
        """
        Transcreve ou traduz o áudio do vídeo usando Whisper.
        
        Args:
            arquivo_video: Caminho para o arquivo de vídeo
            traduzir_para_ingles: Se True, traduz para inglês; se False, transcreve no idioma original
            
        Returns:
            Dicionário com resultados da transcrição (segments, words, etc)
        """
        self._carregar_modelo()
        
        if traduzir_para_ingles:
            self.logger.info("Modo TRADUÇÃO ativado (Áudio → Legendas em Inglês)")
            task = "translate"
        else:
            self.logger.info("Modo TRANSCRIÇÃO ativado (Áudio → Legendas no mesmo idioma)")
            task = "transcribe"
        
        self.logger.info("Transcrevendo áudio com timestamps de palavras...")
        result = self.model.transcribe(
            arquivo_video,
            task=task,
            word_timestamps=True,  # Timestamps palavra por palavra
            fp16=False  # Desativa FP16 para compatibilidade
        )
        
        # Contagem de palavras detectadas
        total_palavras = sum(
            len(seg.get('words', [])) 
            for seg in result.get('segments', [])
        )
        self.logger.info(f"✓ Transcrição completa: {total_palavras} palavras detectadas")
        
        return result
    
    def _gerar_arquivo_ass(
        self, 
        result, 
        max_palavras_por_linha=3,
        font="Impact",
        font_size=70,
        font_color="#FFFFFF",
        stroke_width=4,
        stroke_color="#000000",
        shadow_strength=2,
        highlight_current_word=False,
        word_highlight_color="#FFFF00",
        padding=80
    ):
        """
        Gera arquivo ASS (Advanced SubStation Alpha) com legendas estilizadas customizáveis.
        
        Args:
            result: Resultado da transcrição do Whisper
            max_palavras_por_linha: Quantas palavras mostrar por linha
            font: Nome ou caminho da fonte
            font_size: Tamanho da fonte
            font_color: Cor principal da fonte (hex: #RRGGBB)
            stroke_width: Largura do contorno
            stroke_color: Cor do contorno (hex: #RRGGBB)
            shadow_strength: Intensidade da sombra (0-10)
            highlight_current_word: Se True, destaca a palavra atual
            word_highlight_color: Cor do destaque (hex: #RRGGBB)
            padding: Margem inferior (distância da borda inferior)
            
        Returns:
            Caminho para o arquivo ASS temporário
        """
        arquivo_ass = tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.ass', 
            delete=False, 
            encoding='utf-8'
        )
        
        # Converte cores hex para formato ASS (BGR com transparência)
        def hex_to_ass_color(hex_color):
            """Converte #RRGGBB para &H00BBGGRR& (formato ASS)"""
            hex_color = hex_color.lstrip('#')
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            return f"&H00{b:02X}{g:02X}{r:02X}"
        
        primary_color = hex_to_ass_color(font_color)
        outline_color = hex_to_ass_color(stroke_color)
        highlight_color = hex_to_ass_color(word_highlight_color)
        
        # === CABEÇALHO ASS ===
        arquivo_ass.write("[Script Info]\n")
        arquivo_ass.write("ScriptType: v4.00+\n")
        arquivo_ass.write("PlayResX: 1080\n")
        arquivo_ass.write("PlayResY: 1920\n")
        arquivo_ass.write("WrapStyle: 0\n\n")
        
        # === ESTILOS ===
        arquivo_ass.write("[V4+ Styles]\n")
        arquivo_ass.write(
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
            "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        )
        
        # Estilo principal (customizado)
        arquivo_ass.write(
            f"Style: Default,{font},{font_size},{primary_color},{primary_color},"
            f"{outline_color},&H00000000,"
            f"-1,0,0,0,100,100,0,0,1,{stroke_width},{shadow_strength},2,"
            f"10,10,{padding},1\n"
        )
        
        # Estilo highlight (para palavra atual)
        if highlight_current_word:
            arquivo_ass.write(
                f"Style: Highlight,{font},{font_size},{highlight_color},{highlight_color},"
                f"{outline_color},&H00000000,"
                f"-1,0,0,0,100,100,0,0,1,{stroke_width},{shadow_strength},2,"
                f"10,10,{padding},1\n\n"
            )
        else:
            arquivo_ass.write("\n")
        
        # === EVENTOS (LEGENDAS) ===
        arquivo_ass.write("[Events]\n")
        arquivo_ass.write(
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )
        
        evento_id = 0
        for segment in result.get('segments', []):
            if 'words' not in segment or not segment['words']:
                continue
            
            words = segment['words']
            
            # Agrupa palavras em linhas
            for i in range(0, len(words), max_palavras_por_linha):
                group = words[i:i+max_palavras_por_linha]
                
                if highlight_current_word:
                    # Cria evento separado para cada palavra (com destaque)
                    for j, word in enumerate(group):
                        word_text = word['word'].strip()
                        word_start = self._format_ass_time(word['start'])
                        word_end = self._format_ass_time(word['end'])
                        
                        # Monta texto com palavra atual em destaque
                        text_parts = []
                        for k, w in enumerate(group):
                            w_text = w['word'].strip()
                            if k == j:
                                # Palavra atual em destaque
                                text_parts.append(f"{{\\c{highlight_color}}}{w_text}{{\\c{primary_color}}}")
                            else:
                                text_parts.append(w_text)
                        
                        full_text = " ".join(text_parts)
                        
                        # Escreve evento
                        arquivo_ass.write(
                            f"Dialogue: 0,{word_start},{word_end},Default,,0,0,0,,{full_text}\n"
                        )
                        evento_id += 1
                else:
                    # Modo simples: todas as palavras juntas
                    start_time = self._format_ass_time(group[0]['start'])
                    end_time = self._format_ass_time(group[-1]['end'])
                    
                    # Monta texto da linha
                    text_parts = [word['word'].strip() for word in group]
                    full_text = " ".join(text_parts)
                    
                    # Escreve evento ASS
                    arquivo_ass.write(
                        f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{full_text}\n"
                    )
                    evento_id += 1
        
        arquivo_ass.close()
        self.logger.info(f"✓ Arquivo ASS gerado com {evento_id} legendas: {arquivo_ass.name}")
        
        return arquivo_ass.name
    
    def _renderizar_com_ffmpeg(self, arquivo_video_entrada, arquivo_ass, arquivo_video_saida):
        """
        Usa FFmpeg para queimar as legendas ASS no vídeo.
        
        Args:
            arquivo_video_entrada: Vídeo original
            arquivo_ass: Arquivo de legendas ASS
            arquivo_video_saida: Vídeo final com legendas
        """
        self.logger.info("Renderizando vídeo com legendas...")
        
        comando_ffmpeg = [
            "ffmpeg",
            "-i", arquivo_video_entrada,
            "-vf", f"ass={arquivo_ass}",
            "-c:v", "libx264",
            "-preset", "medium",  # Balanço velocidade/qualidade
            "-crf", "23",  # Qualidade (18-28, menor = melhor)
            "-c:a", "copy",  # Copia áudio sem recodificar
            "-y",  # Sobrescrever sem perguntar
            arquivo_video_saida
        ]
        
        self.logger.debug(f"Comando FFmpeg: {' '.join(comando_ffmpeg)}")
        
        resultado = subprocess.run(
            comando_ffmpeg,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if resultado.returncode != 0:
            self.logger.error(f"FFmpeg falhou com código {resultado.returncode}")
            if resultado.stderr:
                # Mostra apenas as últimas linhas do erro
                linhas_erro = resultado.stderr.strip().split('\n')[-10:]
                self.logger.error("Últimas linhas do erro:\n" + "\n".join(linhas_erro))
            raise subprocess.CalledProcessError(
                resultado.returncode, 
                comando_ffmpeg, 
                resultado.stdout, 
                resultado.stderr
            )
        
        self.logger.info("✓ Renderização concluída com sucesso")
    
    def _format_ass_time(self, seconds):
        """
        Converte segundos para formato de timestamp ASS (H:MM:SS.cc).
        
        Args:
            seconds: Tempo em segundos (float)
            
        Returns:
            String no formato ASS (ex: "0:01:23.45")
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
    
    def _formatar_tempo(self, segundos):
        """Formata tempo em segundos para formato legível."""
        if segundos >= 60:
            minutos = int(segundos // 60)
            segs = int(segundos % 60)
            return f"{minutos}m {segs}s"
        else:
            return f"{segundos:.1f}s"
    
    def gerar_legendas(
        self, 
        arquivo_video_entrada, 
        arquivo_video_saida, 
        traduzir_para_ingles=True,
        max_palavras_por_linha=3,
        font="Impact",
        font_size=70,
        font_color="#FFFFFF",
        stroke_width=4,
        stroke_color="#000000",
        shadow_strength=2,
        highlight_current_word=False,
        word_highlight_color="#FFFF00",
        padding=80,
        manter_arquivo_ass=False
    ):
        """
        Método principal: gera legendas profissionais customizáveis para um vídeo.
        
        Args:
            arquivo_video_entrada: Caminho do vídeo original (sem legendas)
            arquivo_video_saida: Caminho do vídeo final (com legendas)
            traduzir_para_ingles: Se True, traduz para inglês; se False, transcreve
            max_palavras_por_linha: Quantas palavras mostrar por linha (2-4 recomendado)
            font: Nome ou caminho da fonte (ex: "Impact", "/path/to/font.ttf")
            font_size: Tamanho da fonte (30-150, recomendado: 70)
            font_color: Cor da fonte em hex (ex: "#FFFFFF" = branco, "#FFFF00" = amarelo)
            stroke_width: Largura do contorno (0-10, recomendado: 3-4)
            stroke_color: Cor do contorno em hex (ex: "#000000" = preto)
            shadow_strength: Intensidade da sombra (0-10, recomendado: 1-2)
            highlight_current_word: Se True, destaca palavra que está sendo falada
            word_highlight_color: Cor do destaque em hex (ex: "#FF0000" = vermelho)
            padding: Margem inferior em pixels (distância da borda, recomendado: 50-100)
            manter_arquivo_ass: Se True, salva arquivo .ass junto do vídeo
            
        Returns:
            True se sucesso, False se falhou
        """
        inicio = time.perf_counter()
        arquivo_ass = None
        
        self.logger.info("┌─────────────────────────────────────────────────────────────┐")
        self.logger.info("│      GERAÇÃO DE LEGENDAS ESTILO TIKTOK                     │")
        self.logger.info("└─────────────────────────────────────────────────────────────┘")
        
        try:
            # ETAPA 1: Transcrição com Whisper
            result = self._transcrever_audio(arquivo_video_entrada, traduzir_para_ingles)
            
            # ETAPA 2: Gerar arquivo ASS com customizações
            arquivo_ass = self._gerar_arquivo_ass(
                result=result,
                max_palavras_por_linha=max_palavras_por_linha,
                font=font,
                font_size=font_size,
                font_color=font_color,
                stroke_width=stroke_width,
                stroke_color=stroke_color,
                shadow_strength=shadow_strength,
                highlight_current_word=highlight_current_word,
                word_highlight_color=word_highlight_color,
                padding=padding
            )
            
            # ETAPA 3: Renderizar com FFmpeg
            self._renderizar_com_ffmpeg(arquivo_video_entrada, arquivo_ass, arquivo_video_saida)
            
            # Limpar arquivo temporário (se solicitado)
            if not manter_arquivo_ass:
                os.unlink(arquivo_ass)
                self.logger.debug("Arquivo ASS temporário removido")
            else:
                # Move para junto do vídeo final
                ass_final = arquivo_video_saida.replace('.mp4', '.ass')
                os.rename(arquivo_ass, ass_final)
                self.logger.info(f"Arquivo ASS salvo: {Path(ass_final).name}")
            
            # Estatísticas finais
            tempo_total = time.perf_counter() - inicio
            tamanho_saida = os.path.getsize(arquivo_video_saida) / (1024 * 1024)  # MB
            
            self.logger.info("")
            self.logger.info("✅ LEGENDAS GERADAS COM SUCESSO!")
            self.logger.info(f"  ├─ Arquivo final: {Path(arquivo_video_saida).name}")
            self.logger.info(f"  ├─ Tamanho: {tamanho_saida:.2f} MB")
            self.logger.info(f"  └─ Tempo total: {self._formatar_tempo(tempo_total)}")
            self.logger.info("")
            
            return True
        
        except ImportError as e:
            self.logger.error(f"✗ ERRO: Módulo não encontrado - {e}")
            self.logger.error("  Instale com: pip install openai-whisper")
            return False
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"✗ ERRO: FFmpeg falhou (código {e.returncode})")
            return False
        
        except Exception as e:
            tempo_total = time.perf_counter() - inicio
            self.logger.error(
                f"✗ ERRO após {self._formatar_tempo(tempo_total)}: {e}", 
                exc_info=True
            )
            return False
        
        finally:
            # Sempre descarrega o modelo ao final
            self._descarregar_modelo()
            
            # Remove arquivo ASS temporário em caso de erro
            if arquivo_ass and os.path.exists(arquivo_ass) and not manter_arquivo_ass:
                try:
                    os.unlink(arquivo_ass)
                except:
                    pass
    
    def processar_em_lote(self, lista_videos, traduzir_para_ingles=True):
        """
        Processa múltiplos vídeos em sequência.
        
        Args:
            lista_videos: Lista de tuplas (entrada, saida)
            traduzir_para_ingles: Aplica a todos os vídeos
            
        Returns:
            Dicionário com estatísticas (sucessos, falhas, tempo)
        """
        inicio_total = time.perf_counter()
        sucessos = 0
        falhas = 0
        
        self.logger.info(f"Iniciando processamento em lote: {len(lista_videos)} vídeos")
        
        for i, (entrada, saida) in enumerate(lista_videos, 1):
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Vídeo {i}/{len(lista_videos)}")
            self.logger.info(f"{'='*60}")
            
            sucesso = self.gerar_legendas(entrada, saida, traduzir_para_ingles)
            
            if sucesso:
                sucessos += 1
            else:
                falhas += 1
        
        tempo_total = time.perf_counter() - inicio_total
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info("RESUMO DO PROCESSAMENTO EM LOTE")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"Total processado: {len(lista_videos)}")
        self.logger.info(f"✅ Sucessos: {sucessos}")
        self.logger.info(f"❌ Falhas: {falhas}")
        self.logger.info(f"⏱️  Tempo total: {self._formatar_tempo(tempo_total)}")
        
        return {
            'total': len(lista_videos),
            'sucessos': sucessos,
            'falhas': falhas,
            'tempo_total': tempo_total
        }


# Exemplo de uso standalone
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Uso: python legenda_generator.py <video_entrada> <video_saida> [traduzir:sim/nao]")
        print("Exemplo: python legenda_generator.py video.mp4 video_legendado.mp4 sim")
        sys.exit(1)
    
    entrada = sys.argv[1]
    saida = sys.argv[2]
    traduzir = sys.argv[3].lower() in ['sim', 's', 'yes', 'y', 'true', '1'] if len(sys.argv) > 3 else True
    
    # Cria o gerador
    gerador = LegendaGenerator(modelo_whisper='small')
    
    # Gera as legendas
    sucesso = gerador.gerar_legendas(
        arquivo_video_entrada=entrada,
        arquivo_video_saida=saida,
        traduzir_para_ingles=traduzir
    )
    
    sys.exit(0 if sucesso else 1)

