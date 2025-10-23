#!/usr/bin/env python3
"""
Teste rápido da classe LegendaGenerator
"""
from legenda_generator import LegendaGenerator

# Arquivos de teste
arquivo_entrada = "saida/anansi_parte1_introducao_base_sem_legenda.mp4"
arquivo_saida = "saida/teste_classe_legenda.mp4"

print("="*60)
print("TESTANDO CLASSE LegendaGenerator")
print("="*60)

# Cria o gerador
gerador = LegendaGenerator(modelo_whisper='small')

# Gera as legendas
sucesso = gerador.gerar_legendas(
    arquivo_video_entrada=arquivo_entrada,
    arquivo_video_saida=arquivo_saida,
    traduzir_para_ingles=True,
    max_palavras_por_linha=3,
    manter_arquivo_ass=False
)

if sucesso:
    print("\n✅ TESTE BEM-SUCEDIDO!")
    print(f"Vídeo com legendas salvo em: {arquivo_saida}")
    exit(0)
else:
    print("\n❌ TESTE FALHOU!")
    exit(1)

