from playwright.sync_api import sync_playwright
import time
import re
import csv
import os

termo_busca = "supermercado"
url_buca = f"https://g1.globo.com/busca/?q={termo_busca}&species=noticias&order=relevant&from=2020-03-01T03%3A00%3A00.000Z&to=2020-03-31T02%3A59%3A59.999Z"
time_initial_load = 25000 #milisegundos
time_click = 3500 #milisegundos
time_scroll = 2000 #milisegundos
cliques = 25
i=0

# Configuração de Salvamento
pasta = r"C:\Users\tiago\UFSC (local)\Prologis\Panic buyng\Noticias web\Dados gerados"

#Filtragem
problemas = [
    "falta", "vazia", "esgotado", "esgotada", "pânico", "limite", 
    "desabastecimento", "escassez", "esvaziamento", "racionamento", 
    "racionam", "limitando", "limitam", "corrida", "aumento", "crise"
]

def interceptar_media(route):
    """Bloqueia o carregamento de imagens e CSS para ganhar velocidade."""
    if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
        route.abort()
    else:
        route.continue_()

def salvar_csv(dados, nome_arquivo):
    if dados:
        caminho_completo = os.path.join(pasta, nome_arquivo)
        
        with open(caminho_completo, mode='w', newline='', encoding='utf-8') as f:
            colunas = ["Problema", "Título", "Data", "Link"]
            writer = csv.DictWriter(f, fieldnames=colunas)
            writer.writeheader()
            writer.writerows(dados)
        print(f"✅ Arquivo salvo em: {caminho_completo}")

inicio = time.time()

with sync_playwright() as playwright:

    browser = playwright.chromium.launch(headless=True) 
    page = browser.new_page()
    page.route("**/*", interceptar_media)

    print("🔍 Direcionando busca para: 'supermercado'...")
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
            if not bloco["titulo"]: continue

            titulo_low = bloco["titulo"].lower()
            match_problema = next((p for p in problemas if p in titulo_low), None)

            # Filtro AND (Local E Problema)
            if match_problema and bloco['link'] not in links_vistos:
                print(f"🚨 MATCH: [{bloco['data']}] - {bloco['titulo'][:70]}...")
                noticias.append({
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
            print(f"\n--- 💾 Atualizando backup ({porcentagem:.0f}% concluído)... ---")
            if porcentagem != 100:
                nome_backup = f"backup_analise.csv"
                salvar_csv(noticias, nome_backup)
            else:   
                salvar_csv(noticias, 'arquivo_final.csv')

            

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

    fim = time.time()
    tempo = fim - inicio


    print("\n" + "="*40)
    print(f"🏆 SUCESSO! Coleta finalizada.")
    print(f"⏱️ Tempo total: {tempo:.2f} segundos")
    print(f"📦 Total de blocos lidos: {ultimo_indice_processado}")
    print(f"📊 Notícias de interesse salvas: {len(noticias)}")
    print(f"📄 Arquivo: {nome_backup}")
    print("="*40)


    browser.close()