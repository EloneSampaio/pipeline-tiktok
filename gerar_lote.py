# Não precisamos mais de 'ollama' nem 're'
from TTS.api import TTS
from diffusers import StableDiffusionPipeline
import torch
from moviepy.editor import *
import os
import json
import math
from datetime import datetime
import time

# --- 1. CONFIGURAÇÕES DO PROJETO ---

ARQUIVO_HISTORIAS = "historias.json" # O ARQUIVO QUE VOCÊ CRIOU

# -- Modelos --
MODELO_T2I = "runwayml/stable-diffusion-v1-5"
MODELO_TTS = "tts_models/multilingual/multi-dataset/xtts_v2" 

# -- Idioma & Vídeo --
IDIOMA = "pt"
FORMATO_VIDEO = (1080, 1920) # Vertical (TikTok)

# --- 2. FUNÇÃO DE LOG ---

def log(mensagem, tipo="INFO"):
    """Imprime mensagem com timestamp e tipo."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{tipo}] {mensagem}")

# --- 3. FUNÇÕES DO PIPELINE (Parte 2, 3 e 4 - Com Logs Melhorados) ---

def parte_2_gerar_audio(texto_narracao, idioma, arquivo_saida):
    """Gera o arquivo de áudio da narração usando o TTS."""
    
    inicio = time.time()
    log(f"Iniciando geração de áudio com modelo {MODELO_TTS}", "AUDIO")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    log(f"Usando dispositivo: {device}", "AUDIO")
    
    log(f"Tamanho do texto: {len(texto_narracao)} caracteres", "AUDIO")
    
    log("Carregando modelo TTS...", "AUDIO")
    tts = TTS(MODELO_TTS)
    tts.to(device)
    log("Modelo TTS carregado com sucesso", "AUDIO")
    
    try:
        log("Sintetizando áudio...", "AUDIO")
        tts.tts_to_file(
            text=texto_narracao,
            speaker="Ana Florence",
            language=idioma,
            file_path=arquivo_saida
        )
        duracao = time.time() - inicio
        log(f"Áudio gerado com sucesso em {duracao:.2f}s - Salvo em: {arquivo_saida}", "AUDIO")
        return arquivo_saida
    except Exception as e:
        log(f"ERRO ao gerar áudio: {e}", "ERROR")
        return None

def parte_3_gerar_imagens(prompts_cenas, pasta_saida):
    """Gera as imagens de cada cena usando Stable Diffusion."""
    
    inicio_total = time.time()
    log(f"Iniciando geração de {len(prompts_cenas)} imagens com {MODELO_T2I}", "IMAGEM")
    
    # Cria a pasta de imagens para este vídeo específico
    os.makedirs(pasta_saida, exist_ok=True)
    log(f"Pasta de saída: {pasta_saida}", "IMAGEM")
    
    log("Carregando modelo Stable Diffusion...", "IMAGEM")
    pipe = StableDiffusionPipeline.from_pretrained(
        MODELO_T2I,
        torch_dtype=torch.float16
    )
    pipe = pipe.to("cuda")
    log("Modelo Stable Diffusion carregado com sucesso", "IMAGEM")
    
    prompt_negativo = "blurry, low quality, deformed, disfigured, text, watermark"
    
    paths_imagens = []
    for i, prompt in enumerate(prompts_cenas):
        inicio_cena = time.time()
        log(f"Gerando cena {i+1}/{len(prompts_cenas)}: '{prompt[:70]}...'", "IMAGEM")
        
        imagem = pipe(
            prompt, 
            negative_prompt=prompt_negativo,
            num_inference_steps=25,
            guidance_scale=7.5
        ).images[0]
        
        caminho_img = os.path.join(pasta_saida, f"cena_{i+1:02d}.png")
        imagem.save(caminho_img)
        paths_imagens.append(caminho_img)
        
        duracao_cena = time.time() - inicio_cena
        log(f"Cena {i+1}/{len(prompts_cenas)} concluída em {duracao_cena:.2f}s", "IMAGEM")
    
    duracao_total = time.time() - inicio_total
    log(f"Todas as {len(prompts_cenas)} imagens geradas em {duracao_total:.2f}s - Média: {duracao_total/len(prompts_cenas):.2f}s por imagem", "IMAGEM")
    
    # Libera a VRAM da GPU
    log("Liberando VRAM da GPU...", "IMAGEM")
    del pipe
    torch.cuda.empty_cache()
    
    return paths_imagens

def parte_4_montar_video(paths_imagens, path_audio, arquivo_saida, formato_vertical):
    """Monta o vídeo final com MoviePy."""
    
    inicio = time.time()
    log("Iniciando montagem do vídeo final", "VIDEO")
    
    try:
        log(f"Carregando áudio de: {path_audio}", "VIDEO")
        audio_clip = AudioFileClip(path_audio)
        duracao_total = audio_clip.duration
        
        num_imagens = len(paths_imagens)
        duracao_por_imagem = math.ceil(duracao_total / num_imagens * 10) / 10
        
        log(f"Duração total do áudio: {duracao_total:.2f}s", "VIDEO")
        log(f"Duração por imagem: {duracao_por_imagem:.2f}s", "VIDEO")
        log(f"Total de imagens: {num_imagens}", "VIDEO")

        log("Processando clips de vídeo...", "VIDEO")
        clips_video = []
        for i, path_img in enumerate(paths_imagens, 1):
            log(f"Processando clip {i}/{num_imagens}", "VIDEO")
            clip = ImageClip(path_img).set_duration(duracao_por_imagem)
            clip_zoom = clip.resize(1.2)
            w_video, h_video = formato_vertical
            
            clip_final = clip_zoom.resize(
                lambda t: 1 + 0.1 * t
            ).set_pos(('center', 'center'))

            clip_cortado = crop(clip_final, width=w_video, height=h_video, x_center=clip_final.w/2, y_center=clip_final.h/2)
            clips_video.append(clip_cortado)

        log("Concatenando clips...", "VIDEO")
        video_final = concatenate_videoclips(clips_video, method="compose")
        video_final = video_final.set_audio(audio_clip)
        video_final.duration = duracao_total
        
        log(f"Renderizando vídeo final: {arquivo_saida}", "VIDEO")
        video_final.write_videofile(
            arquivo_saida,
            codec="libx264",
            audio_codec="aac",
            fps=24
        )
        
        duracao = time.time() - inicio
        log(f"Vídeo montado com sucesso em {duracao:.2f}s - Salvo em: {arquivo_saida}", "VIDEO")

    except Exception as e:
        log(f"ERRO ao montar o vídeo: {e}", "ERROR")

# --- 4. FUNÇÃO PRINCIPAL (MAIN) ---

def main():
    inicio_geral = time.time()
    print("\n" + "="*80)
    log("INICIANDO PIPELINE DE GERAÇÃO EM LOTE", "INICIO")
    print("="*80 + "\n")
    
    # Cria a pasta 'saida' principal
    os.makedirs("saida", exist_ok=True)
    log("Pasta de saída criada/verificada: saida/", "INFO")

    # Carrega o arquivo JSON com todas as histórias
    try:
        log(f"Carregando arquivo de histórias: {ARQUIVO_HISTORIAS}", "INFO")
        with open(ARQUIVO_HISTORIAS, 'r', encoding='utf-8') as f:
            todas_as_historias = json.load(f)
        log(f"Arquivo carregado com sucesso", "INFO")
    except Exception as e:
        log(f"ERRO ao ler o arquivo {ARQUIVO_HISTORIAS}: {e}", "ERROR")
        return
    
    total_historias = len(todas_as_historias)
    log(f"Total de histórias encontradas: {total_historias}", "INFO")
    log("Iniciando produção em lote...", "INFO")
    
    # --- LOOP DE GERAÇÃO EM MASSA ---
    videos_sucesso = 0
    videos_erro = 0
    
    for i, historia in enumerate(todas_as_historias):
        inicio_video = time.time()
        
        print("\n" + "="*80)
        log(f"VÍDEO {i+1}/{total_historias}: {historia['id_video']}", "INICIO")
        print("="*80 + "\n")
        
        # Define nomes de arquivos únicos para este vídeo
        id_video = historia['id_video']
        ARQUIVO_AUDIO_VIDEO = os.path.join("saida", f"{id_video}_audio.wav")
        PASTA_IMAGENS_VIDEO = os.path.join("saida", f"imagens_{id_video}")
        ARQUIVO_VIDEO_FINAL = os.path.join("saida", f"{id_video}_video_final.mp4")
        
        # Extrai os dados do JSON
        narracao = historia["historia_completa"]
        cenas = historia["cenas"]
        
        log(f"Configurações do vídeo:", "INFO")
        log(f"  - ID: {id_video}", "INFO")
        log(f"  - Número de cenas: {len(cenas)}", "INFO")
        log(f"  - Tamanho da narração: {len(narracao)} caracteres", "INFO")
        
        try:
            # Executa o Pipeline (Partes 2, 3 e 4)
            print("\n" + "-"*80)
            log("ETAPA 1/3: GERAÇÃO DE ÁUDIO", "ETAPA")
            print("-"*80)
            path_audio = parte_2_gerar_audio(narracao, IDIOMA, ARQUIVO_AUDIO_VIDEO)
            
            if path_audio:
                print("\n" + "-"*80)
                log("ETAPA 2/3: GERAÇÃO DE IMAGENS", "ETAPA")
                print("-"*80)
                paths_imagens = parte_3_gerar_imagens(cenas, PASTA_IMAGENS_VIDEO)
                
                if paths_imagens:
                    print("\n" + "-"*80)
                    log("ETAPA 3/3: MONTAGEM DO VÍDEO", "ETAPA")
                    print("-"*80)
                    parte_4_montar_video(
                        paths_imagens,
                        path_audio,
                        ARQUIVO_VIDEO_FINAL,
                        FORMATO_VIDEO
                    )
                    
                    duracao_video = time.time() - inicio_video
                    videos_sucesso += 1
                    
                    print("\n" + "="*80)
                    log(f"VÍDEO {i+1}/{total_historias} CONCLUÍDO COM SUCESSO em {duracao_video:.2f}s", "SUCESSO")
                    print("="*80)
                else:
                    videos_erro += 1
                    log(f"Falha na geração de imagens para o vídeo {id_video}", "ERROR")
            else:
                videos_erro += 1
                log(f"Falha na geração de áudio para o vídeo {id_video}", "ERROR")
        
        except Exception as e:
            videos_erro += 1
            log(f"ERRO GERAL ao processar vídeo {id_video}: {e}", "ERROR")
        
        # Mostra progresso
        restantes = total_historias - (i + 1)
        if restantes > 0:
            log(f"Vídeos restantes: {restantes}", "INFO")
    
    # Resumo final
    duracao_geral = time.time() - inicio_geral
    print("\n" + "="*80)
    log("PIPELINE FINALIZADO", "FIM")
    print("="*80)
    log(f"Tempo total de execução: {duracao_geral:.2f}s ({duracao_geral/60:.2f} minutos)", "RESUMO")
    log(f"Vídeos concluídos com sucesso: {videos_sucesso}/{total_historias}", "RESUMO")
    log(f"Vídeos com erro: {videos_erro}/{total_historias}", "RESUMO")
    if videos_sucesso > 0:
        log(f"Tempo médio por vídeo: {duracao_geral/total_historias:.2f}s", "RESUMO")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()