from playwright.sync_api import sync_playwright

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto("https://g1.globo.com/sc/santa-catarina/", wait_until="domcontentloaded")

    links_vistos = set()
    keywords = ["carro", "assalto", "chuva"]

    try:
        print("Aguardando os blocos de notícias aparecerem...")
        page.wait_for_selector(".feed-post-body", timeout=15000)
    except Exception as e:
        print("Erro: O feed de notícias demorou demais para carregar ou mudou de nome.")
        browser.close()
        exit()

    # 3. Agora que sabemos que eles existem, fazemos a coleta
    page.mouse.wheel(0, 30000)
    page.wait_for_timeout(30000)

    blocos = page.query_selector_all(".feed-post-body")

    
    for bloco in blocos:
        elemento_titulo = bloco.query_selector(".feed-post-link")
        print(f"Analisando bloco: {elemento_titulo.inner_text().strip() if elemento_titulo else 'Sem título'}")
        if elemento_titulo:
            titulo = elemento_titulo.inner_text().strip().lower()
            link = elemento_titulo.get_attribute("href")
            
            if any(key in titulo for key in keywords):
                print(f"✅ Encontrada: {titulo}")
                print(f"🔗 Link: {link}\n")

    print(f"Encontrados {len(blocos)} blocos. Filtrando...")
    browser.close()