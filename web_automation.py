from playwright.sync_api import sync_playwright
import time
import csv

inicio = time.time()

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto("https://g1.globo.com/sc/santa-catarina/", wait_until="domcontentloaded")

    time_load = 25000 #milisegundos
    time_click = 5000 #milisegundos
    links_vi57stos = set()
    cliques = 200

    locais = ["supermercado", "mercado", "atacarejo", "comércio"]
    problemas = ["falta", "vazia", "esgotado", "pânico", "limite", "alta", "desabastecimento"]

    try:
        print(f"Aguardando o feed inicial (Limite: {time_load/1000}s)...")
        page.wait_for_selector(".feed-post-body", timeout=time_load)
    except Exception:
        print("ERRO CRÍTICO: O site não abriu. Abortando...")
        browser.close()
        exit() 

    for clique in range(cliques + 1):
        i=0
        print(f"\n--- 'página' {clique + 1} ---")
        qtd_anterior = -1
        blocos = page.query_selector_all(".feed-post-body")

        while len(blocos) > qtd_anterior:
            qtd_anterior = len(blocos)
            print(f"Tentativa {i+1}: Encontrados {len(blocos)} blocos até agora.")

            if blocos:
                ultimo_bloco = blocos[-1]
                posicao = ultimo_bloco.bounding_box()
                #print(f"Posição do último bloco: {posicao}")
                if posicao:
                    page.mouse.wheel(0, posicao["y"] + 650)
                    page.wait_for_timeout(time_click*0.7)  # Espera p que o conteúdo carregue
                    blocos = page.query_selector_all(".feed-post-body")
            i += 1
        
        
        if clique < cliques:
            # Usamos um seletor de texto para achar o botão "Veja mais"
            botao_veja_mais = page.query_selector("text=/(Veja mais|Mostrar mais|Carregar mais)/i")
            
            if botao_veja_mais and botao_veja_mais.is_visible():
                print("Clicando...")
                botao_veja_mais.click()
                page.wait_for_timeout(time_click) # Espera para o G1 "abrir" a nova seção de notícias
            else:
                print("Botão 'Veja mais' não apareceu. Talvez chegamos ao fim absoluto.")
                break
      
    noticias = []
    links_vistos = set()

    for bloco in blocos:
        elemento_titulo = bloco.query_selector(".feed-post-link")

        if elemento_titulo:
            titulo_texto = elemento_titulo.inner_text().lower()
            tem_local = any(l.lower() in titulo_texto for l in locais)
            tem_problema = any(p.lower() in titulo_texto for p in problemas)

            if tem_local and tem_problema:
                titulo = elemento_titulo.inner_text().strip()
                link = elemento_titulo.get_attribute("href")
                data = bloco.query_selector(".feed-post-datetime").inner_text().strip() if bloco.query_selector(".feed-post-datetime") else "Data não disponível"
                local = next((l for l in locais if l.lower() in titulo_texto), "N/A")
                problema = next((p for p in problemas if p.lower() in titulo_texto), "N/A")

                if link not in links_vistos:
                    print(f"Notícia encontrada!")
                    noticias.append({
                        "Local": local, 
                        "Problema": problema, 
                        "Título": titulo, 
                        "Data": data,
                        "Link": link})
                    links_vistos.add(link)

            if not elemento_titulo: #pular links de publicidade ou blocos sem título
                continue
    fim = time.time()
    tempo = fim - inicio

    arquivo_csv = f"noticias_g1_{cliques}cliks_{len(blocos)}b.csv"
    if noticias:
        with open(arquivo_csv, mode='w', newline='', encoding='utf-8') as f:
            colunas = (["Local", "Problema", "Título", "Data", "Link"])
            writer = csv.DictWriter(f, fieldnames=colunas)
            writer.writeheader()
            writer.writerows(noticias)

        print(f"\n{len(noticias)} notícias salvas em '{arquivo_csv}' com os locais e problemas: {', '.join(locais + problemas)}")

    
    print(f"Tempo {tempo:.2f} s")
    browser.close()