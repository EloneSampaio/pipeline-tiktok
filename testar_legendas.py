#!/usr/bin/env python3
"""
Script de teste para a nova função de legendas usando Whisper + FFmpeg
"""
import sys
sys.path.insert(0, '/media/sam/Arquivos/pipeline-tiktok')

from gerar_lote_v3 import VideoPipeline

# Inicializa o pipeline
pipeline = VideoPipeline(config_path="config.json")

# Arquivos de teste
arquivo_base = "saida/anansi_parte1_introducao_base_sem_legenda.mp4"
arquivo_saida = "saida/teste_legendas_whisper.mp4"

# Testa a nova função
print("Testando nova função de legendas (Whisper + FFmpeg)...")
sucesso = pipeline._etapa_4_legendas_whisper_ffmpeg(
    arquivo_base, 
    arquivo_saida, 
    legendar_em_ingles=True
)

if sucesso:
    print(f"\n✅ Teste bem-sucedido! Arquivo gerado: {arquivo_saida}")
    exit(0)
else:
    print("\n❌ Teste falhou!")
    exit(1)

