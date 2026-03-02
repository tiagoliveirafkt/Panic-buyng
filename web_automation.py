from playwright.sync_api import sync_playwright
import time
import csv

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto("https://g1.globo.com/sc/santa-catarina/", wait_until="domcontentloaded")

    links_vistos = set()
    cliques = 5
    arquivo_csv = "noticias_g1.csv"


    keywords = ["neymar","carro","morte"]

    for clique in range(cliques + 1):
        i=0
        print(f"\n--- 'página' {clique + 1} ---")

        qtd_anterior = -1
        blocos = page.query_selector_all(".feed-post-body")

        try:
            print("Aguardando os blocos de notícias aparecerem...")
            page.wait_for_selector(".feed-post-body", timeout=15000)
        except Exception as e:
            print("Erro: O feed de notícias demorou demais para carregar ou mudou de nome.")
            browser.close()
            exit()


        while len(blocos) > qtd_anterior:
            qtd_anterior = len(blocos)
            print(f"Tentativa {i+1}: Encontrados {len(blocos)} blocos até agora.")

            if blocos:
                ultimo_bloco = blocos[-1]
                posicao = ultimo_bloco.bounding_box()
                #print(f"Posição do último bloco: {posicao}")

                if posicao:
                    page.mouse.wheel(0, posicao["y"] + 650)
                    page.wait_for_timeout(1500)  # Espera um pouco para garantir que o conteúdo carregue
                    blocos = page.query_selector_all(".feed-post-body")
            i += 1
        
        
        if clique < cliques:
            # Usamos um seletor de texto para achar o botão "Veja mais"
            botao_veja_mais = page.query_selector("text=Veja mais")
            
            if botao_veja_mais and botao_veja_mais.is_visible():
                print("Clicando...")
                botao_veja_mais.click()
                
                # Espera essencial para o G1 "abrir" a nova seção de notícias
                page.wait_for_timeout(4000) 
            else:
                print("Botão 'Veja mais' não apareceu. Talvez chegamos ao fim absoluto.")
                break
            
    noticias = []
    links_vistos = set()

    for bloco in blocos:
        elemento_titulo = bloco.query_selector(".feed-post-link")

        #pular links de publicidade ou blocos sem título
        if not elemento_titulo:
            continue
            
        if elemento_titulo:
            if any(key.lower() in elemento_titulo.inner_text().lower() for key in keywords):
                titulo = elemento_titulo.inner_text().strip()
                link = elemento_titulo.get_attribute("href")
                data = bloco.query_selector(".feed-post-datetime").inner_text().strip() if bloco.query_selector(".feed-post-datetime") else "Data não disponível"
                palavra_chave = next((key for key in keywords if key.lower() in elemento_titulo.inner_text().lower()), "N/A")

                if link not in links_vistos:
                    noticias.append({"Palavra-chave": palavra_chave, "Título": titulo, "Link": link, "Data": data})
                    links_vistos.add(link)

    if noticias:
        with open(arquivo_csv, mode='w', newline='', encoding='utf-8') as f:
            colunas = (["Palavra-chave", "Título", "Data", "Link"])
            writer = csv.DictWriter(f, fieldnames=colunas)
            writer.writeheader()
            writer.writerows(noticias)

        print(f"\n{len(noticias)} notícias salvas em '{arquivo_csv}' com as palavras-chave: {', '.join(keywords)}")

    browser.close()