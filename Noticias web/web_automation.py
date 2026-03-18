from playwright.sync_api import sync_playwright
import time
import re
import csv
import os
import pandas as pd
from datetime import datetime, timedelta

#Funcoes
def gerar_intervalos_g1(data_inicio_str, data_fim_str, intervalo_dias, termo_busca):
    formato_entrada = "%d/%m/%Y"
    formato_g1 = "%Y-%m-%dT03:00:00.000Z" # O G1 usa o formato ISO 8601 com Z (UTC)
    
    data_inicio = datetime.strptime(data_inicio_str, formato_entrada)
    data_fim = datetime.strptime(data_fim_str, formato_entrada)
    
    resultado = {'Data inicio': [], 'urls': []}
    data_atual = data_inicio
    
    while data_atual < data_fim:
        resultado['Data inicio'].append(data_atual.strftime(formato_entrada))
        proxima_data = data_atual + timedelta(days=intervalo_dias)
        
        # Garante que a data final do intervalo não ultrapasse a data limite
        if proxima_data > data_fim:
            proxima_data = data_fim
            
        # Formata as datas para a URL
        de_str = data_atual.strftime(formato_g1)
        ate_str = proxima_data.strftime(formato_g1)
        
        # Substitui os caracteres especiais para ficarem prontos para URL (%3A para o :)
        de_url = de_str.replace(":", "%3A")
        ate_url = ate_str.replace(":", "%3A")
        
        url = (f"https://g1.globo.com/busca/?q={termo_busca}&species=noticias&order=relevant"
               f"&from={de_url}&to={ate_url}")
        
        resultado['urls'].append(url)
        data_atual = proxima_data + timedelta(days=1) # Pula para o dia seguinte para não sobrepor
    return resultado

def interceptar_media(route):
    """Bloqueia o carregamento de imagens e CSS para ganhar velocidade."""
    if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
        route.abort()
    else:
        route.continue_()

def salvar_csv(dados, nome_arquivo):
    if dados:
        os.makedirs(pasta, exist_ok=True)
        caminho_completo = os.path.join(pasta, nome_arquivo)
        
        with open(caminho_completo, mode='w', newline='', encoding='utf-8') as f:
            colunas = ["Periodo", "Problema", "Título", "Data", "Link"]
            writer = csv.DictWriter(f, fieldnames=colunas)
            writer.writeheader()
            writer.writerows(dados)
        print(f"✅ Arquivo salvo em: {caminho_completo}")

def montar_nome_backup_porcentagem(porcentagem):
    return f"backup_analise_{int(porcentagem)}%.csv"

def montar_nome_final_periodo(periodo):
    periodo_normalizado = periodo.replace("/", "-")
    return f"arquivo_final_ate_{periodo_normalizado}.csv"

def renomear_backup_se_progresso_mudar(nome_atual, nome_novo):
    if not nome_atual or nome_atual == nome_novo:
        return nome_novo

    origem = os.path.join(pasta, nome_atual)
    destino = os.path.join(pasta, nome_novo)

    if os.path.exists(origem):
        if os.path.exists(destino):
            os.remove(destino)
        os.replace(origem, destino)

    return nome_novo

infos = {'periodo':[], 'total de blocos':[], 'noticias do periodo':[], 'noticias acumuladas':[], 'tempo iteracao':[], 'arquivo':[]}

#Config busca
time_initial_load = 25000 #milisegundos
time_click = 3500 #milisegundos
time_scroll = 2000 #milisegundos
cliques = 15

#Config periodos
termo_busca = "supermercado"
data_incio = '25/03/2024'
data_fim = '31/12/2025'
intervalo = 90

intervalos = gerar_intervalos_g1(data_incio, data_fim, intervalo, termo_busca)
periodos = intervalos['Data inicio']
urls = intervalos['urls']

problemas = ["abastecimento", "abastecem", "abastecido", "abastecer", "reabastecer", "reabastecem", "reabastecido", "desabastecimento", "desabastecem", "desabastecido", 
"racionamento", "racionam", "restrição", "restringem", "restringir", "limitam", "limite", "limitando", "limitar", 
"quantidade", "volume", "repor", "reposição", "repõe", "logística", "distribuição",
"escassez", "escasso", "ruptura", "esvaziamento", "vazio", "vazia", "esvazia", "falta", "faltando", "acaba", "acabou", "termina", "terminou", "indisponível", "esgotado", "esgotada", "esgotar", "zerar", "zerados", "zeram", "interrupção", "interrompem",
"estoque", "estocar", "estocagem", "estocando", 
"busca", "corrida", "disparada", "dispara", "demanda", "aumento", "aumentar", "aumentam", "preço", 
"crise", "pânico", "compra", "fila", "lotado", "lotam", "tumulto", "multidão", "multidões", "aglomeração", "aglomerações", "correria", 
"produto", "alimento", "comida", "item", "itens", "essencial", "essenciais", "prateleira", "gôndola", 
"incerteza", "medo", "rumor", "aviso", "orientação", "alerta",
"greve", "paralisação", "bloqueio", "isolada", "isolado", "interdição", "interditado", "interditada", 
"pandemia", "epidemia", "covid-19", "coronavírus", 
"mau tempo", "alagamento", "chuva", "temporal", "enxurrada", "inundação", "deslizamento", "defesa civil"]

# Configuração de Salvamento
base_dir = os.path.dirname(os.path.abspath(__file__))
pasta = os.path.join(base_dir, "Dados gerados")
os.makedirs(pasta, exist_ok=True)

inicio_total = time.time()

noticias_totais = []
nome_final = montar_nome_final_periodo(periodos[-1])
nome_backup_atual = None

print(f"Iniciando coleta em {len(periodos)} períodos:")
for periodo, url_buca in zip(periodos, urls):
    inicio_iteracao = time.time()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.route("**/*", interceptar_media)

        print(f"🔍 Inicio busca no período: {periodo}")
        page.goto(url_buca, wait_until="domcontentloaded")

        try:
            print(f"Aguardando o feed inicial (Limite: {time_initial_load/1000}s)...")
            page.wait_for_selector(".widget--info__text-container", timeout=time_initial_load)
        except Exception:
            print("!X ERRO CRÍTICO X!")
            print("O site não abriu.")
            browser.close()
            exit()

        noticias = []
        links_vistos = set()
        ultimo_indice_processado = 0

        for clique in range(cliques + 1):
            print(f"\n--- 'página' {clique + 1} ---")

            #Scroll logics
            blocos_na_tela = page.query_selector_all(".widget--info__text-container") #coleta ponteiros dos blocos de notícias

            if blocos_na_tela:
                posicao = blocos_na_tela[-1].bounding_box()
                if posicao:
                    page.mouse.wheel(0, posicao["y"] + 700)
                    page.wait_for_timeout(time_scroll)  # Espera p que o conteúdo carregue

            # Extração em massa
            dados_extraidos = page.evaluate("""
                        () => {
                            const blocos = document.querySelectorAll('.widget--info__text-container');
                            return Array.from(blocos).map(b => {
                                const linkEl = b.querySelector('a'); // Na busca, o <a> envolve o conteúdo
                                const tituloEl = b.querySelector('.widget--info__title');
                                const dataEl = b.querySelector('.widget--info__meta span'); // A data costuma estar num span dentro do meta

                                return {
                                    titulo: tituloEl ? tituloEl.innerText.trim() : null,
                                    link: linkEl ? linkEl.getAttribute('href') : null,
                                    data: dataEl ? dataEl.innerText.trim() : 'N/D'
                                };
                            });
                        }
                    """)

            #Processamento local (slicing)
            novos_blocos = dados_extraidos[ultimo_indice_processado:]

            #Analise dos blocos de notícias
            for bloco in novos_blocos:
                if not bloco["titulo"]:
                    continue

                titulo_low = bloco["titulo"].lower()
                match_problema = next((p for p in problemas if p in titulo_low), None)

                # Filtro AND (Local E Problema)
                if match_problema and bloco['link'] not in links_vistos:
                    print(f"🚨 MATCH: [{bloco['data']}] - {bloco['titulo'][:70]}...")
                    noticias.append({
                        "Periodo": periodo,
                        "Problema": match_problema,
                        "Título": bloco['titulo'],
                        "Data": bloco['data'],
                        "Link": bloco['link']
                    })
                    links_vistos.add(bloco['link'])
                else:
                    # Limpa a linha antes de imprimir o log de leitura para evitar sobreposição
                    print(f"(Lendo) {bloco['data']}", end="\r")

            ultimo_indice_processado = len(dados_extraidos)

            # Lógica de backup a cada 25% de cliques
            passo_backup = max(1, cliques // 4)
            if clique > 0 and clique % passo_backup == 0:
                porcentagem = (clique / cliques) * 100
                print(f"\n--- 💾 Atualizando backup ---")
                dados_parciais = noticias_totais + noticias

                novo_nome_backup = montar_nome_backup_porcentagem(porcentagem)
                nome_backup_atual = renomear_backup_se_progresso_mudar(nome_backup_atual, novo_nome_backup)
                salvar_csv(dados_parciais, nome_backup_atual)

                if porcentagem == 100:
                    salvar_csv(dados_parciais, nome_final)

            # Lógica de clique para carregar mais notícias
            if clique < cliques:
                # Usamos um seletor de texto para achar o botão "Veja mais"
                botao_veja_mais = page.locator(".pagination__load-more a, button").filter(has_text=re.compile(r"Veja mais|Mostrar mais|Carregar mais", re.IGNORECASE)).first

                if botao_veja_mais:
                    print("\nClicando...")
                    botao_veja_mais.click(timeout=6000)
                    page.wait_for_timeout(time_click) # Espera para o G1 "abrir" a nova seção de notícias
                else:
                    print("Botão 'Veja mais' não apareceu. Fim absoluto.")
                    break

        browser.close()

    noticias_totais.extend(noticias)
    if nome_backup_atual:
        salvar_csv(noticias_totais, nome_backup_atual)

    fim_iteracao = time.time()
    tempo_iteracao = fim_iteracao - inicio_iteracao

    infos['periodo'].append(periodo)
    infos['total de blocos'].append(ultimo_indice_processado)
    infos['noticias do periodo'].append(len(noticias))
    infos['noticias acumuladas'].append(len(noticias_totais))
    infos['tempo iteracao'].append(tempo_iteracao)
    infos['arquivo'].append(nome_backup_atual)

    print("\n" + "="*40)
    print(f"🏆 SUCESSO! Coleta finalizada.")
    print(f"📅 Período: {periodo}")
    print(f"⏱️ Tempo total: {tempo_iteracao:.2f} segundos")
    print(f"📦 Total de blocos lidos: {ultimo_indice_processado}")
    print(f"📊 Notícias de interesse salvas no período: {len(noticias)}")
    print(f"📚 Notícias acumuladas: {len(noticias_totais)}")
    print(f"📄 Arquivo: {nome_backup_atual}")
    print("="*40)

fim_total = time.time()
tempo_total = fim_total - inicio_total
salvar_csv(noticias_totais, 'arquivo_final_completo.csv')

#salva infos em csv
os.makedirs(pasta, exist_ok=True)

caminho_completo = os.path.join(pasta, f'resumo_coleta_{cliques}cliks.csv')
with open(caminho_completo, mode='w', newline='', encoding='utf-8') as f:
    colunas = ['periodo', 'total de blocos', 'noticias do periodo', 'noticias acumuladas', 'tempo iteracao', 'arquivo']
    writer = csv.DictWriter(f, fieldnames=colunas)
    writer.writeheader()
    for i in range(len(infos['periodo'])):
        writer.writerow({
            'periodo': infos['periodo'][i],
            'total de blocos': infos['total de blocos'][i],
            'noticias do periodo': infos['noticias do periodo'][i],
            'noticias acumuladas': infos['noticias acumuladas'][i],
            'tempo iteracao': infos['tempo iteracao'][i],
            'arquivo': infos['arquivo'][i]
        })

print(f"✅ Arquivo informativo salvo em: {caminho_completo}")


print(f"\n⏱️ Tempo total de execução: {tempo_total:.2f} segundos")
print(f"🧾 Total final de notícias: {len(noticias_totais)}")