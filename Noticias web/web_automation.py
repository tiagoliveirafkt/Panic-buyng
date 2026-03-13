from playwright.sync_api import sync_playwright
import time
import csv

time_initial_load = 25000 #milisegundos
time_click = 3500 #milisegundos
time_scroll = 2000 #milisegundos
cliques = 1000
i=0

#Filtragem
locais = ["supermercado", "mercado", "atacarejo", "comércio"] 
problemas = ["falta", "vazia", "esgotado", "esgotadas", "pânico", "limite", "alta", "desabastecimento"]

def interceptar_media(route):
    """Bloqueia o carregamento de imagens e CSS para ganhar velocidade."""
    if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
        route.abort()
    else:
        route.continue_()

def salvar_csv(dados, nome_arquivo):
    if dados:
        with open(nome_arquivo, mode='w', newline='', encoding='utf-8') as f:
            colunas = ["Local", "Problema", "Título", "Data", "Link"]
            writer = csv.DictWriter(f, fieldnames=colunas)
            writer.writeheader()
            writer.writerows(dados)
        print(f"✅ Backup salvo em: {nome_arquivo}")

inicio = time.time()

with sync_playwright() as playwright:

    browser = playwright.chromium.launch(headless=True) 
    page = browser.new_page()

    page.route("**/*", interceptar_media)

    print("Acessando o site...")
    page.goto("https://g1.globo.com/sc/santa-catarina/", wait_until="domcontentloaded")

    try:
        print(f"Aguardando o feed inicial (Limite: {time_initial_load/1000}s)...")
        page.wait_for_selector(".feed-post-body", timeout=time_initial_load)
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
        qtd_anterior = -1
        blocos_na_tela = page.query_selector_all(".feed-post-body") #coleta ponteiros dos blocos de notícias
        while len(blocos_na_tela) > qtd_anterior:
            qtd_anterior = len(blocos_na_tela)
            i += 1
            print(f"Tentativa {i}: Encontrados {len(blocos_na_tela)} blocos até agora.")

            if blocos_na_tela:
                ultimo_bloco = blocos_na_tela[-1]
                posicao = ultimo_bloco.bounding_box()
                if posicao:
                    page.mouse.wheel(0, posicao["y"] + 700)
                    page.wait_for_timeout(time_scroll)  # Espera p que o conteúdo carregue
                    blocos_na_tela = page.query_selector_all(".feed-post-body")

        # Extração em massa
        dados_extraidos = page.evaluate("""
            () => {
                const blocos = document.querySelectorAll('.feed-post-body');
                return Array.from(blocos).map(b => {
                    const linkEl = b.querySelector('.feed-post-link');
                    const dataEl = b.querySelector('.feed-post-datetime');
                    return {
                        titulo: linkEl ? linkEl.innerText.trim() : null,
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
            '''print(f"[{bloco['data']}] {bloco['titulo'][:60]}...")'''

            # Filtro AND (Local E Problema)
            if any(l in titulo_low for l in locais) and any(p in titulo_low for p in problemas):
                if bloco['link'] not in links_vistos:
                    print(">>> 🚨 Noticia encontrada! Salvando...")
                    noticias.append({
                        "Local": next((l for l in locais if l in titulo_low), "N/A"),
                        "Problema": next((p for p in problemas if p in titulo_low), "N/A"),
                        "Título": bloco['titulo'],
                        "Data": bloco['data'],
                        "Link": bloco['link']
                    })
                    links_vistos.add(bloco['link'])

        ultimo_indice_processado = len(dados_extraidos)

        # Lógica de backup a cada 25% de cliques
        passo_backup = max(1, cliques // 4)
        if clique > 0 and clique % passo_backup == 0:
            porcentagem = (clique / cliques) * 100
            print(f"\n--- 💾 Realizando backup de {porcentagem:.0f}%... ---")
            nome_backup = f"backup_noticias_{cliques}cliks_{int(porcentagem)}pct.csv"
            salvar_csv(noticias, nome_backup)

        # Lógica de clique para carregar mais notícias
        if clique < cliques:
            # Usamos um seletor de texto para achar o botão "Veja mais"
            botao_veja_mais = page.query_selector("text=/(Veja mais|Mostrar mais|Carregar mais)/i")
            if botao_veja_mais and botao_veja_mais.is_visible():
                print("Clicando...")
                botao_veja_mais.click()
                page.wait_for_timeout(time_click) # Espera para o G1 "abrir" a nova seção de notícias
            else:
                print("Botão 'Veja mais' não apareceu. Fim absoluto.")
                break

    fim = time.time()
    tempo = fim - inicio

    nome_csv = f"noticias_g1_{cliques}cliks_{len(noticias)}news.csv"
    salvar_csv(noticias, nome_csv)

    print("\n" + "="*40)
    print(f"🏆 SUCESSO! Coleta finalizada.")
    print(f"⏱️ Tempo total: {tempo:.2f} segundos")
    print(f"📦 Total de blocos lidos: {ultimo_indice_processado}")
    print(f"📊 Notícias de interesse salvas: {len(noticias)}")
    print(f"📄 Arquivo: {nome_csv}")
    print("="*40)


    browser.close()