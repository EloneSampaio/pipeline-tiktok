#!/usr/bin/env python3
"""
Teste rápido da fonte TikTok Sans oficial
"""
from legenda_generator import LegendaGenerator

print("="*60)
print("🎬 TESTANDO FONTE TIKTOK SANS OFICIAL")
print("="*60)
print()

# Arquivo de teste
arquivo_entrada = "saida/anansi_parte1_introducao_base_sem_legenda.mp4"
arquivo_saida = "saida/teste_tiktok_sans.mp4"

print(f"📥 Entrada: {arquivo_entrada}")
print(f"📤 Saída: {arquivo_saida}")
print()

# Criar gerador
gerador = LegendaGenerator(modelo_whisper='small')

# Testar com TikTok Sans Bold (recomendado)
print("🎨 Usando: TikTok Sans Bold (fonte oficial)")
print("🎯 Estilo: Destaque palavra por palavra (karaoke)")
print()

sucesso = gerador.gerar_legendas(
    arquivo_video_entrada=arquivo_entrada,
    arquivo_video_saida=arquivo_saida,
    traduzir_para_ingles=True,
    
    # Fonte TikTok Sans
    font="Fonts/TikTok_Sans/static/TikTokSans_18pt-Bold.ttf",
    font_size=70,
    font_color="#FFFFFF",  # Branco
    
    # Contorno e sombra
    stroke_width=4,
    stroke_color="#000000",  # Preto
    shadow_strength=2,
    
    # Destaque palavra atual (estilo karaoke)
    highlight_current_word=True,
    word_highlight_color="#FFFF00",  # Amarelo
    
    # Layout
    max_palavras_por_linha=3,
    padding=80
)

print()
if sucesso:
    print("✅ TESTE BEM-SUCEDIDO!")
    print()
    print(f"🎬 Vídeo com TikTok Sans salvo em:")
    print(f"   {arquivo_saida}")
    print()
    print("💡 Dicas:")
    print("   - Compare com outras fontes editando config.json")
    print("   - Veja GUIA_FONTES_TIKTOK.md para mais opções")
    exit(0)
else:
    print("❌ TESTE FALHOU!")
    print("   Verifique se o arquivo de entrada existe")
    exit(1)

