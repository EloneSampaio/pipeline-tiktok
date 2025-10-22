import ollama
from TTS.api import TTS
from diffusers import StableDiffusionPipeline
import torch
from moviepy.editor import *
import os
import json
import math
import re

# --- 1. CONFIGURAÇÕES DO PROJETO ---

# -- Modelos --
MODELO_LLM = "deepseek-r1"             # Modelo do Ollama para gerar histórias
MODELO_T2I = "runwayml/stable-diffusion-v1-5" # Modelo de Imagem (rápido, 6GB VRAM)
MODELO_TTS = "tts_models/multilingual/multi-dataset/xtts_v2" # Modelo de Voz

# -- História --
TEMA_HISTORIA = "Uma história folclórica africana curta sobre Anansi, a aranha."
IDIOMA = "pt" # pt = Português, en = Inglês, fr = Francês, etc.
NUM_CENAS = 6 # Número de imagens/cenas que queremos

# -- Vídeo Final --
ARQUIVO_AUDIO = "saida/historia.wav"
PASTA_IMAGENS = "saida/imagens"
ARQUIVO_VIDEO = "saida/video_final.mp4"
FORMATO_VIDEO = (1080, 1920) # Vertical (TikTok)

# --- 2. FUNÇÕES DO PIPELINE ---

def parte_1_gerar_roteiro(tema, num_cenas):
    """Gera a história e os prompts de imagem usando o Ollama."""
    
    print(f"[PARTE 1] Gerando roteiro com {MODELO_LLM}...")
    
    # Este prompt é otimizado para pedir uma resposta em JSON.
    prompt_sistema = f"""
    Você é um roteirista de TikTok. Sua tarefa é criar uma história curta (máximo de 150 palavras)
    baseada no tema fornecido.
    
    Você DEVE responder APENAS com um objeto JSON válido.
    O JSON deve ter duas chaves:
    1. "historia_completa": O texto completo da narração.
    2. "cenas": Uma lista de {num_cenas} strings, onde cada string é um prompt de imagem 
       para o Stable Diffusion, descrevendo visualmente cada parte da história.
       Os prompts devem ser em inglês (para melhor resultado do T2I) e detalhados.
       
    Exemplo de formato de saída:
    {{
      "historia_completa": "Era uma vez...",
      "cenas": [
        "cinematic photo of a small spider...",
        "a big elephant walking in the savanna...",
        ...
      ]
    }}
    """
    
    client = ollama.Client()
    try:
        response = client.chat(
            model=MODELO_LLM,
            messages=[
                {'role': 'system', 'content': prompt_sistema},
                {'role': 'user', 'content': f"Tema: {tema}"}
            ],
            # --- CORREÇÃO APLICADA AQUI ---
            options={'temperature': 0.8, 'num_predict': 1024} 
        )
        
        # --- CÓDIGO DE DEBUG (DEIXE ELE AQUI) ---
        
        raw_response = response['message']['content']
        print(f"--- Resposta crua do LLM (Debug): ---\n{raw_response}\n---------------------------------")
        
        # Procura pelo JSON na resposta
        match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        
        if match:
            json_response = match.group(0)
            
            # --- TENTATIVA DE CORRIGIR JSON MAL FORMADO ---
            try:
                dados_historia = json.loads(json_response)
            except json.JSONDecodeError:
                print("--- Aviso: JSON mal formado. Tentando limpar...")
                # Remove lixo antes do primeiro { e depois do último }
                json_response = "{" + json_response.split('{', 1)[-1]
                json_response = json_response.rsplit('}', 1)[0] + "}"
                try:
                    dados_historia = json.loads(json_response)
                except Exception as e:
                    print(f"!!! ERRO CRÍTICO: Não foi possível decodificar o JSON. Erro: {e}")
                    return None
            
            print(f"--- Narração: {dados_historia['historia_completa']}")
            print(f"--- Prompts de Imagem: {len(dados_historia['cenas'])} gerados.")
            return dados_historia
        else:
            print("!!! ERRO CRÍTICO: O LLM NÃO RETORNOU UM JSON VÁLIDO. !!!")
            print("Verifique o prompt ou tente um modelo LLM diferente.")
            return None
        # --- FIM DO CÓDIGO DE DEBUG ---
        
    except Exception as e:
        print(f"Erro ao conectar com o Ollama: {e}")
        print("Verifique se o seu contêiner 'ollama' do Docker está rodando.")
        return None

def parte_2_gerar_audio(texto_narracao, idioma, arquivo_saida):
    """Gera o arquivo de áudio da narração usando o TTS."""
    
    print(f"\n[PARTE 2] Gerando áudio com {MODELO_TTS}...")
    
    # Verifica se a GPU está disponível
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"--- Usando dispositivo: {device}")
    
    tts = TTS(MODELO_TTS)
    tts.to(device)
    
    try:
        tts.tts_to_file(
            text=texto_narracao,
            speaker="Ana Florence", # Uma boa voz em português
            language=idioma,
            file_path=arquivo_saida
        )
        print(f"--- Áudio salvo em: {arquivo_saida}")
        return arquivo_saida
        
    except Exception as e:
        print(f"Erro ao gerar áudio: {e}")
        return None

def parte_3_gerar_imagens(prompts_cenas, pasta_saida):
    """Gera as imagens de cada cena usando Stable Diffusion."""
    
    print(f"\n[PARTE 3] Gerando {len(prompts_cenas)} imagens com {MODELO_T2I}...")
    
    # Otimizado para sua VRAM de 6GB (usando float16)
    pipe = StableDiffusionPipeline.from_pretrained(
        MODELO_T2I,
        torch_dtype=torch.float16
    )
    pipe = pipe.to("cuda") # Envia o modelo para a GPU
    
    # Um prompt negativo ajuda a melhorar a qualidade
    prompt_negativo = "blurry, low quality, deformed, disfigured, text, watermark"
    
    paths_imagens = []
    for i, prompt in enumerate(prompts_cenas):
        print(f"--- Gerando cena {i+1}/{len(prompts_cenas)}: '{prompt[:50]}...'")
        
        # Gera a imagem
        imagem = pipe(
            prompt, 
            negative_prompt=prompt_negativo,
            num_inference_steps=25,
            guidance_scale=7.5
        ).images[0]
        
        # Salva a imagem
        caminho_img = os.path.join(pasta_saida, f"cena_{i+1:02d}.png")
        imagem.save(caminho_img)
        paths_imagens.append(caminho_img)
        
    print(f"--- Imagens salvas em: {pasta_saida}")
    return paths_imagens

def parte_4_montar_video(paths_imagens, path_audio, arquivo_saida, formato_vertical):
    """Monta o vídeo final com MoviePy."""
    
    print(f"\n[PARTE 4] Montando o vídeo final...")
    
    try:
        # Carrega o áudio
        audio_clip = AudioFileClip(path_audio)
        duracao_total = audio_clip.duration
        
        # Calcula a duração de cada "slide" (imagem)
        num_imagens = len(paths_imagens)
        duracao_por_imagem = math.ceil(duracao_total / num_imagens * 10) / 10 # Arredonda para cima
        
        print(f"--- Duração total do áudio: {duracao_total}s")
        print(f"--- Duração por imagem: {duracao_por_imagem}s")

        clips_video = []
        for path_img in paths_imagens:
            # Cria um clipe de imagem
            clip = ImageClip(path_img).set_duration(duracao_por_imagem)
            
            # --- EFEITO KEN BURNS (Zoom In) Simples ---
            # Redimensiona a imagem para ser um pouco maior que o vídeo
            clip_zoom = clip.resize(1.2) 
            
            # Pega o tamanho do vídeo final (vertical)
            w_video, h_video = formato_vertical
            
            # Define o tamanho final do clipe e anima o zoom
            clip_final = clip_zoom.resize(
                lambda t: 1 + 0.1 * t  # Zoom in (de 1.0x para 1.1x ao longo do clipe)
            ).set_pos(('center', 'center'))

            # Corta para o formato vertical
clip_cortado = vfx.crop(clip_animado, width=w_video, height=h_video, x_center=clip_animado.w/2, y_center=clip_animado.h/2)            
            clips_video.append(clip_cortado)

        # Concatena todos os clipes de imagem
        video_final = concatenate_videoclips(clips_video, method="compose")
        
        # Define o áudio do vídeo
        video_final = video_final.set_audio(audio_clip)
        
        # Garante que a duração do vídeo bate com a do áudio
        video_final.duration = duracao_total
        
        # Escreve o arquivo final
        video_final.write_videofile(
            arquivo_saida,
            codec="libx264",
            audio_codec="aac",
            fps=24
        )
        print(f"\n[SUCESSO] Vídeo salvo em: {arquivo_saida}")

    except Exception as e:
        print(f"Erro ao montar o vídeo: {e}")

# --- 3. FUNÇÃO PRINCIPAL (MAIN) ---

def main():
    # Cria a pasta 'saida' se ela não existir
    os.makedirs(os.path.dirname(ARQUIVO_AUDIO), exist_ok=True)
    os.makedirs(PASTA_IMAGENS, exist_ok=True)

    # Executa o Pipeline
    dados_historia = parte_1_gerar_roteiro(TEMA_HISTORIA, NUM_CENAS)
    
    if dados_historia:
        path_audio = parte_2_gerar_audio(
            dados_historia["historia_completa"],
            IDIOMA,
            ARQUIVO_AUDIO
        )
        
        paths_imagens = parte_3_gerar_imagens(
            dados_historia["cenas"],
            PASTA_IMAGENS
        )
        
        if path_audio and paths_imagens:
            parte_4_montar_video(
                paths_imagens,
                path_audio,
                ARQUIVO_VIDEO,
                FORMATO_VIDEO
            )

if __name__ == "__main__":
    main()