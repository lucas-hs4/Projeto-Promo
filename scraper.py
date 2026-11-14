import random
import json
import urllib.parse
from playwright.sync_api import sync_playwright

cancelar_varredura = False

TERMOS_IGNORADOS = [
    "figurinha", "álbum", "album","cromo", "envelope",
    "adrenalyn", "fifa", "libertadores", "brasileirão",
    "brasileirao", "copa do mundo", "seleção da copa", "starter pack",
    "chaveiro", "pn toys", "figure", "miniatura", "estatueta",
    "usado", "seminovo", "camiseta", "caneca", "funko", "ecobag",
    "english edition", "english comics", "spanish edition", "edição inglês", "[inglês]", "importado",
    "portuguese edition", "para colorir", "livro de colorir", "coloring book", "crie e pinte", "pinte o seu",
    "superpôster", "superposter","mpeg-", "divx"
]

EDITORAS_VALIDAS = [
    "Panini", "JBC", "NewPOP", "Pipoca & Nanquim", "MPEG",
    "Eaglemoss", "Devir", "DarkSide", "Mythos", "Comix Zone"
]

def identificar_editora(texto, padrao="Outras"):
    """Descobre a editora pelo título ou mantém a editora padrão da busca."""
    t = texto.lower()
    if any( p in t for p in [
        "eaglemoss", "dc graphic novels", "coleção oficial de graphic novels",
        "sagas definitivas", "lendas do cavaleiro das trevas", "dpgc"
    ]):
        return "Eaglemoss"
    elif any(p in t for p in [
        "devir", "lazarus", "bitch planet", "family tree", "lumberjanes", "carta 44",
        "skyward", "domínio público", "dead letters", "a marcha", "ancient magus",
        "ascender", "takemitsu zamurai", "chew", "paper girls", "black science",
        "seven to eternity", "east of west", "gideon falls", "sex criminals",
        "wicked + the divine", "descender", "monstress", "heartstopper", "sin city"
    ]):
        return "Devir"
    elif any(p in t for p in [
        "darkside", "dark side", "condado maldito", "insetos humanos", "lady killer",
        "green river killer", "o corvo", "joe hill", "menina submersa",
        "todas as faces da morte", "deathdisco", "fragmentos do horror", "sensor", "bela treva"
    ]):
        return "DarkSide"
    elif any(p in t for p in [
        "mythos", "tex ", "tex:", "tex -", "tex willer", "dylan dog", "zagor",
        "mágico vento", "ken parker", "martin mystère", "bonelli", "juiz dredd",
        "hellblazer - origens"
    ]):
        return "Mythos"
    elif any(p in t for p in [
        "comix zone", "o muro", "saturnália", "lon chaney", "czar acidental",
        "torpedo 1936", "paracuellos", "alack sinner", "breccia", "chabouté", "druuna"
    ]):
        return "Comix Zone"
    elif any(p in t for p in [
        "jbc", "hunter x hunter", "haikyu", "fullmetal alchemist", "soul eater", "akira", "death note",
        "cavaleiros do zodíaco", "saint seiya", "inuyasha", "cardcaptor sakura", "card captor sakura", "sailor moon",
        "tokyo revengers", "my hero academia", "boku no hero", "yona", "alice in borderland",
        "fire punch", "blame!", "hellsing", "shaman king", "boa noite punpun", "yomi no tsugai",
        "xxxholic", "rayearth", "nausicaä", "blade - a lâmina", "astro boy", "bakuman", "zom 100",
        "nana vol", "the fable", "parasyte", "skip & loafer", "medalist", "reincarnated as a slime",
        "edens zero", "final fantasy lost stranger", "dead dead demons", "fruits basket", "buda - vol",
        "kamen rider", "shimanami tasogare", "boys run the riot", "sem saída", "yu yu hakusho",
        "akane banashi", "bendaora", "sanctuary vol", "ghost in the shell", "dragon quest",
        "montanhas da loucura", "rurouni kenshin", "mujina"
    ]):
        return "JBC"
    elif any(p in t for p in [
        "newpop", "new pop", "re:zero", "re: zero", "solo leveling", "mo dao zu shi", "bênção do oficial",
        "sistema de autopreservação", "ashita no joe", "terra das gemas", "houseki no kuni",
        "given", "uma vida imortal", "to your eternity", "record of ragnarok", "shuumatsu",
        "a voz do silêncio", "semantic error", "um sinal de afeto", "mushishi", "toradora", "made in abyss",
        "beginning after the end", "melhor engenheiro do mundo", "greatest estate developer",
        "dangerous convenience store", "king's maker", "pink heart jam", "destino dos vilões",
        "classroom of the elite", "no game no life", "citrus", "fuja comigo, garota",
        "perfect world", "a casa do sol", "coelacanth", "girl crush", "love so pure", "kimba", "uq holder"
    ]):
        return "NewPOP"
    elif any(p in t for p in [
        "pipoca", "nanquim", "junji ito", "tomie", "uzumaki", "gyo", "shigurui", "incal",
        "tartarugas ninja", "último ronin", "lobo solitário", "chushingura", "city hunter", "cat's eye", "cão de caça",
        "the boys", "calafrios", "a lagarta", "ptsd radio", "harem end", "o vampiro que ri",
        "anamorfose", "kanikosen", "lady snowblood", "elric", "eternauta", "thorgal",
        "copra", "jack kirby", "estórias gerais", "mandala de fogo", "gon:", "gon -", "gon vol",
        "mundo sem fim", "fire! vol", "princesa do castelo sem fim", "o escultor", "watership down",
        "replay:", "stray toasters", "torradeiras desgarradas", "guardiões do louvre"
    ]):
        return "Pipoca & Nanquim"
    elif any(p in t for p in [
        "mpeg", "gash bell", "beck", "kaoru hana", "hajime no ippo", "sense life",
        "creamy mami", "nodame cantabile", "omori", "dusk maiden", "10 dance", "como conquistar um alfa",
        "casamento dos vaga-lumes", "tenkaichi", "gto -"
    ]):
        return "MPEG"
    elif any(p in t for p in [
        "panini", "marvel", "dc comics", "dc de bolso", "dc deluxe", "dc vintage", "dc black label",
        "grandes eventos dc", "turma da mônica", "mauricio de sousa", "cebolinha", "cascão", "magali",
        "chico bento", "saiba mais!", "saiba mais ", "graphic msp", "invencível", "star wars", "darth vader",
        "mandalorian", "homem-aranha", "homem de ferro", "capitão américa", "capitao america",
        "quarteto fantástico", "surfista prateado", "viúva negra", "viuva negra", "thor", "hulk",
        "venom", "doutor estranho", "batman", "superman", "x-men", "vingadores", "demolidor",
        "wolverine", "lanterna verde", "mulher-maravilha", "liga da justiça", "flash", "coringa",
        "sandman", "arlequina", "watchmen", "robin", "shazam", "esquadrão suicida", "deadpool",
        "spawn", "conan", "espada selvagem", "kull", "walking dead", "one piece", "chainsaw man",
        "jujutsu kaisen", "demon slayer", "kimetsu no yaiba", "berserk", "naruto", "dragon ball",
        "spy x family", "frieren", "dandadan", "blue lock", "vagabond", "tokyo ghoul", "jojo's",
        "jojos", "jojo´s", "bleach remix", "one-punch man", "one punch man", "sakamoto days", "kagurabachi",
        "kusuriya", "diários de uma apotecária", "hanako-kun", "vinland saga", "atelier of witch hat",
        "gachiakuta", "20th century boys", "pluto:", "monster kanzenban", "slam dunk", "mushoku tensei",
        "asa noturna", "detective comics", "ultimate collection", "caçador de marte", "cavaleiro da lua",
        "dc x sonic", "vilania", "arqueiro verde", "spidey", "bungo stray dogs", "dorohedoro",
        "undead unluck", "komi não consegue", "as quíntuplas", "granblue fantasy", "vampire knight",
        "nisekoi", "mao vol", "we never learn", "yuuna e a pensão", "honey lemon soda", "witch watch",
        "bug ego", "garota mágica dandelion", "black clover", "imperial vol", "claymore remix",
        "capitão tsubasa", "tower dungeon", "hirayasumi", "tamon's b-side", "drcl", "gantz", "beastars",
        "vampiro americano", "atos de maldade", "império secreto", "blade runner", "pássaros que cantam",
        "injustiça", "starman", "kingdom hearts", "kamandi", "razão e sensibilidade", "waller vs",
        "miracleman", "flintstones", "providence", "aquaman", "legião dos super-heróis", "my home hero"
    ]):
        return "Panini"
    return padrao if padrao in EDITORAS_VALIDAS else "Outras"

def extrair_panini(pagina, url_produto):
    print(f"Consultando:: {url_produto}...")
    
    try:
        resposta = pagina.goto(url_produto, wait_until="domcontentloaded")
        
        if resposta.status != 200:
            print(f"Erro ao acessar a página. Status: {resposta.status}")
            return None
            
        titulo = pagina.locator("h1.page-title").inner_text().strip()
        
        loc_img = pagina.locator('meta[property="og:image"]')
        imagem_url = loc_img.get_attribute("content") if loc_img.count() > 0 else ""
            
        bloco_principal = pagina.locator("div.product-info-main")
            
        loc_preco_final = bloco_principal.locator('[data-price-type="finalPrice"]')
        if loc_preco_final.count() > 0:
            preco_texto = loc_preco_final.get_attribute("data-price-amount")
            preco_atual = float(preco_texto)
        else:
            preco_atual = 0.0  
            
        loc_preco_antigo = bloco_principal.locator('[data-price-type="oldPrice"]')
        if loc_preco_antigo.count() > 0:
            preco_antigo_texto = loc_preco_antigo.get_attribute("data-price-amount")
            preco_original = float(preco_antigo_texto)
        else:
            preco_original = preco_atual
            
        desconto_pct = round(((preco_original - preco_atual) / preco_original) * 100) if preco_original > preco_atual else 0
            
        tem_botao_compra = bloco_principal.locator("#product-addtocart-button").count() > 0
        fora_de_estoque = bloco_principal.locator("div.stock.unavailable").count() > 0
        texto_bloco = bloco_principal.inner_text()
            
        if fora_de_estoque or not tem_botao_compra:
            status_estoque = "Indisponível"
            disponivel = False
        elif "Pré-venda" in texto_bloco or "previsão de envio" in texto_bloco:
            status_estoque = "Pré-venda"
            disponivel = True
        else:
            status_estoque = "Em estoque"
            disponivel = True
            
        if "pipocaenanquim.com.br" in url_produto:
            loja_nome = "Pipoca & Nanquim"
        elif "mpeg.com.br" in url_produto:
            loja_nome = "MPEG"
        else:
            loja_nome = "Panini"
            
        return {
            "loja": loja_nome,
            "categoria": identificar_categoria(titulo, url_produto, preco_atual),
            "nome": titulo,
            "url": url_produto,
            "imagem_url": imagem_url,
            "preco_original": preco_original,
            "preco_atual": preco_atual,
            "desconto_pct": desconto_pct,
            "status": status_estoque,
            "disponivel": disponivel
        }
    except Exception as erro:
        print(f"   [Erro] Falha ao ler produto {url_produto}: {erro}")
        return None
    
def ler_cards_magento(cards):
    """Lê todos os cards da página de uma só vez no navegador (Panini e Pipoca & Nanquim)."""
    return cards.evaluate_all("""els => els.map(el => {
        const link = el.querySelector('a.product-item-link');
        const img = el.querySelector('img.product-image-photo');
        const pFinal = el.querySelector('[data-price-type="finalPrice"]');
        const pOld = el.querySelector('[data-price-type="oldPrice"]');
        const texto = el.innerText || '';
        return {
            nome: link ? link.innerText.trim() : '',
            url: link ? link.href : '',
            img: img ? img.src : '',
            preco_atual: pFinal ? parseFloat(pFinal.getAttribute('data-price-amount') || 0) : 0,
            preco_antigo: pOld ? parseFloat(pOld.getAttribute('data-price-amount') || 0) : 0,
            disponivel: !!el.querySelector('button.tocart') && !el.querySelector('.stock.unavailable'),
            prevenda: !!el.querySelector('.infobase-label-presale') || texto.includes('Pré-venda') || texto.includes('Pré-Venda')
        };
    })""")

def extrair_vitrine_panini(pagina, url_inicial, max_paginas=100, urls_vistas=None):
    """
    Crawler de Categoria: entra na vitrine, extrai todos o cards da grade
    e avança para as próximas páginas sozinho até atingir 'max_paginas'.
    """
    
    url_atual = url_inicial
    pagina_num = 1
    produtos_extraidos = []
    if urls_vistas is None:
        urls_vistas = set()
    
    while url_atual and pagina_num <= max_paginas:
        if cancelar_varredura:
            print("   [Parada] Varredura interrompida pelo usuário.")
            break
        print(f"[Crawler] Varrendo Página {pagina_num}: {url_atual}...")
    
        try:
            resposta = pagina.goto(url_atual, wait_until="domcontentloaded", timeout=60000)
            if resposta.status != 200:
                print(f"Erro ao acessar a vitrine. Status: {resposta.status}")
                break
            pagina.wait_for_selector("div.products-grid", timeout=30000)
            pagina.wait_for_timeout(800)
        except Exception as erro:
            print(f"   [Erro de Rede] Pulo na Página {pagina_num} da Panini: {erro}")
            break
    
        cards = pagina.locator("div.products-grid div.product-item-info")
        lista_bruta = ler_cards_magento(cards)
        print(f"Encontrados {len (lista_bruta)} produtos nesta página.")
    
        for item in lista_bruta:
            if not item["url"] or item["url"] in urls_vistas:
                continue
            urls_vistas.add(item["url"])
            
            preco_atual = item["preco_atual"]
            preco_original = item["preco_antigo"] if item["preco_antigo"] > 0 else preco_atual
            desconto_pct = round(((preco_original - preco_atual) / preco_original) * 100) if preco_original > preco_atual else 0
            
            if not item["disponivel"]:
                status_estoque = "Indisponível"
            elif item["prevenda"]:
                status_estoque = "Pré-venda"
            else:
                status_estoque = "Em estoque"

            produtos_extraidos.append({
                "loja": "Panini",
                "categoria": identificar_categoria(item["nome"], url_atual, preco_atual),
                "nome": item["nome"],
                "url": item["url"],
                "imagem_url": item["img"],
                "preco_original": preco_original,
                "preco_atual": preco_atual,
                "desconto_pct": desconto_pct,
                "status": status_estoque,
                "disponivel": item["disponivel"]
            })
            
        botao_proxima = pagina.locator("li.pages-item-next a.action.next").first
        if botao_proxima.count() > 0 and pagina_num < max_paginas:
            url_atual = botao_proxima.get_attribute("href")
            pagina_num += 1
        else:
            url_atual = None
            
    return produtos_extraidos

def identificar_categoria(nome, url_contexto="", preco_atual=10.0):
    """Classifica automaticamente a HQ/Mangá por Universo ou Categoria."""
    texto = f"{nome} {url_contexto}".lower()
    
    if 0 < preco_atual < 1.0 or any(termo in texto for termo in TERMOS_IGNORADOS):
        return "Excluídos"
    
    if any(t in texto for t in [
        "tartarugas ninja", "ultimo ronin", "último ronin"
        ]):
        return "As Tartarugas Ninja"
    elif any(d in texto for d in [
        "/disney", "disney", "mickey", "pato donald", "donald", "ducktales", "duck tales", "mickey e pateta",
        "tio patinhas", "minnie", "pateta", "19.999 léguas submarinas", "histórias de esportes"
    ]):
        return "Disney"
    elif any(i in texto for i in [
        "/invencivel", "invencível", "invencivel" 
    ]):
        return "Invencível"
    elif any(s in texto for s in[
        "/spawn", "spawn"
    ]):
        return "Spawn"
    elif any(c in texto for c in [
        "/conan", "conan", "espada selvagem", "kull"
    ]):
        return "Conan"
    elif any(w in texto for w in [
        "/star-wars", "star wars", "mandalorian", "darth vader"
    ]):
        return "Star Wars"
    elif any(t in texto for t in [
        "/the-walking-dead", "walking dead"
    ]):
        return "The Walking Dead"
    elif any(h in texto for h in [
        "/marvel", "marvel", "homem-aranha","homem de ferro", "viúva negra", "viuva negra",
        "viúva-negra", "aranha", "vingadores", "x-men", "wolverine", "demolidor",
        "thor", "capitão américa", "capitao américa", "hulk", "deadpool", "quarteto fantástico",
        "surfista prateado", "venom", "doutor estranho"
    ]):
        return "Marvel"
    elif any(h in texto for h in [
        "/dc-comics", "dc+comics", "dc ", " dc", "(dc)", "batman", "superman", "mulher-maravilha", "liga da justiça", "flash", "lanterna verde",
        "asa noturna", "coringa", "sandman", "arlequina", "watchmen", "juízo final", "heróis em crise",
        "herois em crise", "robin", "shazam", "a saga dos superfilhos", "gordon: lei & ordem", "esquadrão suicida"
    ]):
        return "DC Comics"
    elif any(l in texto for l in [
        "/panini-books", "/novels", "novel", "livro", "livros.html", "livrosnovels"
    ]):
        return "Novels & Livros"
    elif any(m in texto for m in [
        "/planet-manga", "planet+manga", "lojanewpop", "mpeg", "mangas.html", "junji ito", "shigurui", "city hunter", "cat's eye", "cats eye", "chushingura", "battle royale", "one piece",
        "berserk", "naruto", "dragon ball", "demon slayer", "jujutsu", "tokyo ghoul", "chainsaw man", "mashle", "re:zero",
        "katana beast", "record of ragnarok", "one punch man", "hokuto no ken", "the ghost in the shell", "devil exstasy",
        "zero no tsukaima", "aku no hana", "ragna crimson", "tower of god"
    ]):
        return "Mangás"
    elif any(m in texto for m in [
        "/mauricio-de-sousa-catalogo", "mauricio", "mônica", "monica", "cebolinha", "cascão", "magali",
        "chico bento", "xaveco", "tina", "saiba mais"
    ]):
        return "Turma da Mônica"
    else:
        return "Outros"

def limpar_preco_br(texto):
    """Converte 'R$ 84,90' para o float 84.90."""
    if not texto:
        return 0.0
    limpo = texto.replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(limpo)
    except ValueError:
        return 0.0

def extrair_vitrine_newpop(pagina, url_inicial, max_paginas=2,urls_vistas=None):
    """
    Crawler para a NewPOP (Loja Integrada) com captura de capa e categoria.
    """
    url_atual = url_inicial
    pagina_num = 1
    produtos_extraidos = []
    if urls_vistas is None:
        urls_vistas = set()
        
    while url_atual and pagina_num <= max_paginas:
        print(f"\n[NewPOP] Varrendo Página {pagina_num}: {url_atual}...")

        try:
            resposta = pagina.goto(url_atual, wait_until="domcontentloaded")
            if resposta.status != 200:
                print(f"Erro ao acessar NewPOP. Status: {resposta.status}")
                break
        except Exception as erro:
            print(f"   [Erro de Rede] Falha na NewPOP: {erro}")
            break

        cards = pagina.locator("#listagemProdutos div.listagem-item")
        lista_bruta = cards.evaluate_all("""els => els.map(el => {
            const link = el.querySelector('a.nome-produto');
            const img = el.querySelector('img.imagem-principal');
            const pPromo = el.querySelector('strong.preco-promocional');
            const pNormal = el.querySelector('strong.preco-venda');
            const pAntigo = el.querySelector('s.preco-venda');
            const classes = el.className || '';
            return {
                nome: link ? link.innerText.trim() : '',
                url: link ? link.href : '',
                img: img ? img.src : '',
                preco_attr: pPromo ? pPromo.getAttribute('data-sell-price') : (pNormal ? pNormal.getAttribute('data-sell-price') : ''),
                preco_txt: pPromo ? pPromo.innerText : (pNormal ? pNormal.innerText : ''),
                antigo_txt: pAntigo ? pAntigo.innerText : '',
                classes: classes,
                esgotado: !! el.querySelector('.bandeira-indisponivel, .indisponivel') || classes.includes('indisponivel')
            };
        })""")
        print(f"Encontrados {len(lista_bruta)} produtos nesta página.")

        for item in lista_bruta:
            if not item["url"] or item["url"] in urls_vistas:
                continue
            urls_vistas.add(item["url"])
            
            preco_atual = float(item["preco_attr"]) if item["preco_attr"] else limpar_preco_br(item["preco_txt"])
            preco_original = limpar_preco_br(item["antigo_txt"]) if item["antigo_txt"] else preco_atual
            desconto_pct = round(((preco_original - preco_atual) / preco_original) * 100) if preco_original > preco_atual else 0

            if item["esgotado"] or preco_atual == 0.0:
                status_estoque = "Indisponível"
                disponivel = False
            elif "prod-cat-589867" in item["classes"]:
                status_estoque = "Pré-venda"
                disponivel = True
            else:
                status_estoque = "Em estoque"
                disponivel = True

            categoria = "Novels & Livros" if "prod-cat-500119" in item["classes"] else "Mangás"

            produtos_extraidos.append({
                "loja": "NewPOP",
                "categoria": categoria,
                "nome": item["nome"],
                "url": item["url"],
                "imagem_url": item["img"],
                "preco_original": preco_original,
                "preco_atual": preco_atual,
                "desconto_pct": desconto_pct,
                "status": status_estoque,
                "disponivel": disponivel
            })

        botao_prox = pagina.locator(".pagination li:not(.disabled) a[rel='next'], .pagination li a:has-text('›')").first
        if botao_prox.count() > 0 and pagina_num < max_paginas:
            prox_href = botao_prox.get_attribute("href")
            if prox_href and prox_href != "#" and not prox_href.startswith("javascript"):
                url_atual = prox_href if prox_href.startswith("http") else f"https://www.lojanewpop.com.br{prox_href}"
                pagina_num += 1
            else:
                url_atual = None
        else:
            url_atual = None

    return produtos_extraidos

def extrair_newpop (pagina, url_produto):
    """Extrai os dados de uma página individual de produto da NewPOP."""
    print(f"Consultando NewPOP: {url_produto}...")
    
    try:
        resposta = pagina.goto(url_produto, wait_until="domcontentloaded")
        if resposta.status != 200:
            print(f"Erro ao acessar produto NewPOP. Status: {resposta.status}")
            return None
        
        titulo = pagina.locator("h1.nome-produto").first.inner_text().strip()
        
        loc_img = pagina.locator('meta[property="og:image"]')
        imagem_url = loc_img.get_attribute("content") if loc_img.count() > 0 else ""
        
        bloco = pagina.locator("div.principal div.acoes-produto").first
        
        loc_promo = bloco.locator("strong.preco-promocional").first
        loc_normal = bloco.locator("strong.preco-venda").first
        
        if loc_promo.count() > 0:
            attr_preco = loc_promo.get_attribute("data-sell-price")
            preco_atual = float(attr_preco) if attr_preco else limpar_preco_br(loc_promo.inner_text())
        elif loc_normal.count() > 0:
            attr_preco = loc_normal.get_attribute("data-sell-price")
            preco_atual = float(attr_preco) if attr_preco else limpar_preco_br(loc_normal.inner_text())
        else:
            preco_atual = 0.0
        
        loc_antigo = bloco.locator("s.preco-venda").first
        if loc_antigo.count() > 0:
            preco_original = limpar_preco_br(loc_antigo.inner_text())
        else:
            preco_original = preco_atual
            
        desconto_pct = round(((preco_original - preco_atual) / preco_original) * 100) if preco_original > preco_atual else 0
        
        classes_bloco = bloco.get_attribute("class") or ""
        tem_botao = bloco.locator("a.botao-comprar").count() > 0
        texto_migalhas = pagina.locator("div.breadcrumbs").inner_text() if pagina.locator("div.breadcrumbs").count() > 0 else ""
        
        if "indisponivel" in classes_bloco or not tem_botao or preco_atual == 0.0:
            status_estoque = "Indisponível"
            disponivel = False
        elif "Pré-venda" in texto_migalhas or "Pré-venda" in titulo:
            status_estoque = "Pré-venda"
            disponivel = True
        else:
            status_estoque = "Em estoque"
            disponivel = True
            
        categoria = "Novels & Livros" if "Novels" in texto_migalhas or "Livros" in titulo else "Mangás"
        
        return {
            "loja": "NewPOP",
            "categoria": categoria,
            "nome": titulo,
            "url": url_produto,
            "imagem_url": imagem_url,
            "preco_original": preco_original,
            "preco_atual": preco_atual,
            "desconto_pct": desconto_pct,
            "status": status_estoque,
            "disponivel": disponivel
        }
    except Exception as erro:
        print(f"   [Erro] Falha ao ler produto NewPOP {url_produto}: {erro}")
        return None
    
def extrair_vitrine_pipoca(pagina, url_inicial, max_paginas=100, urls_vistas=None):
    """
    Crawler para Pipoca & Nanquim (Magento 2).
    Funciona tanto na Home (carrosséis) quanto nas páginas de categorias (.html).
    """
    url_atual = url_inicial
    pagina_num = 1
    produtos_extraidos = []
    if urls_vistas is None:
        urls_vistas = set()
        
    loja_nome = "MPEG" if "mpeg.com.br" in url_inicial else "Pipoca & Nanquim"
    
    while url_atual and pagina_num <= max_paginas:
        if cancelar_varredura:
            print("   [Parada] Varredura interrompida pelo usuário.")
            break
        print(f"\n[{loja_nome}] Varrendo Página {pagina_num}: {url_atual}...")
        
        try:
            resposta = pagina.goto(url_atual, wait_until="domcontentloaded", timeout=60000)
            if resposta.status != 200:
                print(f"Erro ao acessar Pipoca & Nanquim. Status: {resposta.status}")
                break
            pagina.wait_for_selector("div.products-grid, ol.widget-product-carousel", timeout=30000)
            pagina.wait_for_timeout(800)
        except Exception as erro:
            print(f"   [Erro de Rede] Falha em Pipoca & Nanquim: {erro}")
            break
        
        cards = pagina.locator("div.products-grid div.product-item-info, ol.widget-product-carousel div.product-item-info")
        lista_bruta = ler_cards_magento(cards)
        print(f"Encontrados {len(lista_bruta)} cards nessa página.")
        
        for item in lista_bruta:
            if not item["url"] or item["url"] in urls_vistas:
                continue
            urls_vistas.add(item["url"])

            preco_atual = item["preco_atual"]
            preco_original = item["preco_antigo"] if item["preco_antigo"] > 0 else preco_atual
            desconto_pct = round(((preco_original - preco_atual) / preco_original) * 100) if preco_original > preco_atual else 0

            if not item["disponivel"]:
                status_estoque = "Indisponível"
            elif item["prevenda"]:
                status_estoque = "Pré-venda"
            else:
                status_estoque = "Em estoque"

            produtos_extraidos.append({
                "loja": loja_nome,
                "categoria": identificar_categoria(item["nome"], url_atual, preco_atual),
                "nome": item["nome"],
                "url": item["url"],
                "imagem_url": item["img"],
                "preco_original": preco_original,
                "preco_atual": preco_atual,
                "desconto_pct": desconto_pct,
                "status": status_estoque,
                "disponivel": item["disponivel"]
            })

        botao_proxima = pagina.locator("li.pages-item-next a.action.next").first
        if botao_proxima.count() > 0 and pagina_num < max_paginas:
            url_atual = botao_proxima.get_attribute("href")
            pagina_num += 1
        else:
            url_atual = None

    return produtos_extraidos

def converter_no_jbc(no):
    """Converse o bloco JSON de um produto da JBC/Companhia das Letras para o formato do banco."""
    nome = no.get("name", "").strip()
    slug = no.get("slug") or no.get("seo", {}).get("canonical", "").strip("/")
    if not nome or not slug:
        return None
    
    url_produto = f"https://www.companhiadasletras.com.br/{slug}/p" if not slug.endswith("/p") else f"https://www.companhiadasletras.com.br/{slug}"
    
    imagens = no.get("image", [])
    imagem_url = imagens[0].get("url", "") if imagens else ""
    
    ofertas = no.get("offers", {}).get("offers", [])
    if ofertas:
        preco_atual = float(ofertas[0].get("price", 0.0))
        preco_original = float(ofertas[0].get("listPrice", preco_atual))
        em_estoque_vtex = "InStock" in ofertas[0].get("availability", "")
    else:
        preco_atual = 0.0
        preco_original = 0.0
        em_estoque_vtex = False
        
    desconto_pct = round(((preco_original - preco_atual) / preco_original) * 100) if preco_original > preco_atual else 0
    
    specs = {s.get("name"): s.get("value", "") for s in no.get("specifications", [])}
    status_disp = specs.get("Status de disponibilidade", "").lower()
    
    if not em_estoque_vtex or preco_atual == 0.0:
        status_estoque = "Indisponível"
        disponivel = False
    elif "pré-venda" in status_disp or "pre-venda" in status_disp:
        status_estoque = "Pré-venda"
        disponivel = True
    else:
        status_estoque = "Em estoque"
        disponivel = True
        
    categoria = "Novels & Livros" if ("novel" in nome.lower() or "livro" in nome.lower()) else "Mangás"
    
    return {
        "loja": "JBC",
        "categoria": categoria,
        "nome": nome,
        "url": url_produto,
        "imagem_url": imagem_url,
        "preco_original": preco_original,
        "preco_atual": preco_atual,
        "desconto_pct": desconto_pct,
        "status": status_estoque,
        "disponivel": disponivel
    }
    
def extrair_jbc(pagina, url_produto):
    """Extrai dados de um mangá individual da JBC (usado na Wishlist)."""
    print(f"Consultando JBC: {url_produto}...")
    try:
        resposta = pagina.goto(url_produto, wait_until="domcontentloaded", timeout=60000)
        if resposta.status != 200:
            return None
        texto_json = pagina.locator("script#__NEXT_DATA__").inner_text()
        dados_next = json.loads(texto_json)
        no_produto = dados_next.get("props", {}).get("pageProps", {}).get("data", {}).get("product", {})
        return converter_no_jbc(no_produto)
    except Exception as erro:
        print(f"   [Erro] Falhar ao ler produto JBC {url_produto}: {erro}")
        return None
    
def _consultar_graphql_jbc(pagina, op_name, op_hash, variaveis):
    """Executa uma consutla GraphQL direta na vitrine VTEX na Companhia das Letras."""
    v_str = urllib.parse.quote(json.dumps(variaveis, separators=(",", ":")))
    api_url = (
        f"https://www.companhiadasletras.com.br/api/graphql"
        f"?operationName={op_name}&operationHash={op_hash}&variables={v_str}"
    )
    resp = pagina.request.get(api_url, timeout=30000)
    if resp.status != 200:
        return {}
    return resp.json().get("data", {}).get("search", {})

def extrair_vitrine_jbc(pagina, url_inicial, max_cliques=90, urls_vistas=None):
    """
    Crawler para a vitrine da JBC na Companhia das Letras.
    Captura os hashes GraphQL e consulta em lotes de 100 particionados por ano
    para contornar o limite de 1.000 itens de VTEX Intelligent Search.
    """
    produtos_extraidos = []
    if urls_vistas is None:
        urls_vistas = set()
        
    hashes = {
        "ClientProductGalleryQuery": "bfc40da32b60f9404a4adb96b0856e3fbb04b076",
        "ClientManyProductsQuery": "cf1dd08606442e0d3dd14a288913d0cd636479c4",
    }

    def capturar_hashes(requisicao):
        if "/api/graphql" in requisicao.url and "operationName=" in requisicao.url:
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(requisicao.url).query)
            op = qs.get("operationName", [""])[0]
            h = qs.get("operationHash", [""])[0]
            if op in hashes and h:
                hashes[op] = h
            
    pagina.on("request", capturar_hashes)
    
    try:
        print(f"\n[JBC] Abrindo vitrine: {url_inicial}...")
        pagina.goto(url_inicial, wait_until="domcontentloaded", timeout=60000)
        pagina.evaluate("window.scrollTo(0, 900)")
        pagina.wait_for_timeout(2500)
        
        facetas_base = [
            {"key": "brand", "value": "jbc"},
            {"key": "fuzzy", "value": "0"},
            {"key": "operator", "value": "and"},
            {"key": "channel", "value": '{"salesChannel":"1","regionId":""}'},
            {"key": "locale", "value": "pt-BR"},
        ]
        
        dados_gal = _consultar_graphql_jbc(
            pagina,
            "ClientProductGalleryQuery",
            hashes["ClientProductGalleryQuery"],
            {
                "first": 1,
                "after": "0",
                "sort": "score_desc",
                "term": "",
                "selectedFacets": facetas_base,
                "sponsoredCount": 3,
            },
        )
        anos = []
        for faceta in dados_gal.get("facets", []):
            if faceta.get("key") == "ano-de-publicacao":
                anos = [v["value"] for v in faceta.get("values", []) if v.get("value")]
        
        consultas = [
            (f"Ano {ano}", "score_desc", facetas_base + [{"key": "ano-de-publicacao", "value": ano}])
            for ano in anos
        ]
        if not consultas:
            consultas = [
                ("Preço Crescente", "price_asc", facetas_base),
                ("Preço Descrecente", "price_desc", facetas_base),
            ]
        
        urls_jbc_sessao = set()
        for rotulo, sort_modo, facetas in consultas:
            if cancelar_varredura:
                print("   [Parada] Varredura interrompida pelo usuário.")
                break
            
            novos_bloco = 0
            offset = 0
            while offset < 1000:
                if cancelar_varredura:
                    break
                busca = _consultar_graphql_jbc(
                    pagina,
                    "ClientManyProductsQuery",
                    hashes["ClientManyProductsQuery"],
                    {
                        "first": 100,
                        "after": str(offset),
                        "sort": sort_modo,
                        "term": "",
                        "selectedFacets": facetas,
                        "sponsoredCount": 3,
                    },
                )
                edges = busca.get("products", {}).get("edges", [])
                if not edges:
                    break
                
                for edge in edges:
                    prod = converter_no_jbc(edge.get("node", {}))
                    if prod and prod["url"] not in urls_jbc_sessao:
                        urls_jbc_sessao.add(prod["url"])
                        novos_bloco += 1
                        if prod["url"] not in urls_vistas:
                            urls_vistas.add(prod["url"])
                            produtos_extraidos.append(prod)
                
                if len(edges) < 100:
                    break
                offset += 100
                
            print(f"[JBC] {rotulo}: +{novos_bloco} obras (Total JBC: {len(produtos_extraidos)}).")

            
    except Exception as erro:
        print(f"   [Erro de Rede] Falha na vitrine JBC: {erro}")
    finally:
        pagina.remove_listener("request", capturar_hashes)    
    
    return produtos_extraidos

def extrair_vitrine_amazon(pagina, url_inicial, editora_padrao="Outras", max_paginas=100, urls_vistas=None):
    """Crawler Turbo para buscar de Hqs/Mangás na Amazon Brasil."""
    url_atual = url_inicial
    url_anterior = "https://www.amazon.com.br/"
    pagina_num = 1
    produtos_extraidos = []
    if urls_vistas is None:
        urls_vistas = set()
        
    pagina.wait_for_timeout(random.randint(4000, 7000))
        
    while url_atual and pagina_num <= max_paginas:
        if cancelar_varredura:
            break
        print(f"\n[Amazon • {editora_padrao}] Varrendo Página {pagina_num}: {url_atual}...")
        
        try:
            resposta = None
            for tentativa_503 in range(3):
                resposta = pagina.goto(url_atual, wait_until="domcontentloaded", timeout=60000, referer=url_anterior)
                if resposta.status == 503:
                    espera_s = 30 + (tentativa_503 * 15)
                    print(f"   [Pausa Anti-503] Amazon pediu fôlego (tentativa {tentativa_503 + 1}/3). Renovando sessão e aguardando {espera_s}s...")
                    pagina.context.clear_cookies(domain=".amazon.com.br")
                    pagina.wait_for_timeout(espera_s * 1000)
                    try:
                        pagina.goto("https://www.amazon.com.br/", wait_until="domcontentloaded", timeout=30000)
                        pagina.wait_for_timeout(2000)
                    except Exception:
                        pass
                else:
                    break
            if not resposta or resposta.status != 200:
                print(f"   [Fim do Link] Erro ao acessar Amazon na Página {pagina_num}. Status: {resposta.status if resposta else 'Sem resposta'}")
                break
            pagina.wait_for_selector('div[data-component-type="s-search-result"]', timeout=25000)
            pagina.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            pagina.wait_for_timeout(random.randint(3500, 6000))
            url_anterior = url_atual
        except Exception as erro:
            print(f"   [Fim do Link] Página {pagina_num} não carregou cards (possível Captcha ou fim dos resultados): {erro}")
            break
        
        cards = pagina.locator('div[data-component-type="s-search-result"]')
        resultado_pag = cards.evaluate_all(r"""els => {
            let stats = { total: els.length, validos: 0, importados: 0, so_kindle: 0, sem_preco: 0 };
            let itens = [];
            const bloqueados = [
                'edição inglês', 'edição espanhol', 'edição italiano', 'edição francês',
                'edição alemão', 'edição japonês', 'english edition', 'italian edition',
                'spanish edition', 'compra internacional', 'importado'
            ];
            const formatosFisicos = [
                'capa comum', 'capa dura', 'brochura', 'livro cartonado',
                'livro de bolso', 'capa flexível', 'espiral', 'box'
            ];
            
            for (const el of els) {
                const h2 = el.querySelector('h2');
                const nome = h2 ? h2.innerText.trim() : '';
                if (!nome) continue;
                
                const cabecalhoTxt = (nome + ' ' + (el.querySelector('.a-row.a-size-base.a-color-secondary')?.innerText || '')).toLowerCase();
                if (bloqueados.some(b => cabecalhoTxt.includes(b))) {
                    stats.importados++;
                    continue;
                }
                
                const img = el.querySelector('img.s-image');
                const nos = Array.from(el.querySelectorAll('a, span.a-price, span.a-color-base'));
                let formatoAtual = '';
                let linkFisico = null;
                let precoTxt = '';
                let antigoTxt = '';
                let precoSecundarioTxt = '';
                
                for (const no of nos) {
                    if (no.tagName === 'A') {
                        const txt = no.innerText.trim().toLowerCase();
                        const href = (no.getAttribute('href') || '').toLowerCase();
                        if (formatosFisicos.includes(txt) && !href.includes('-ebook/')) {
                            formatoAtual = 'fisico';
                            if (!linkFisico) linkFisico = no;
                        } else if (
                            txt.includes('kindle') || txt.includes('audiolivro') ||
                            txt.includes('áudio') || txt.includes('audio') ||
                            href.includes('-ebook/')
                        ) {
                            formatoAtual = 'digital';
                        }
                    } else if (no.tagName === 'SPAN' && formatoAtual === 'fisico') {
                        if (no.classList.contains('a-price')) {
                            const off = no.querySelector('.a-offscreen');
                            if (!off) continue;
                            const val = off.textContent.trim();
                            if (no.getAttribute('data-a-strike') === 'true') {
                                if (!antigoTxt && val) antigoTxt = val;
                            } else {
                                if (!precoTxt && val) precoTxt = val;
                            }
                        } else if (!precoTxt && !precoSecundarioTxt && no.classList.contains('a-color-base')) {
                            const m = (no.innerText || '').match(/R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}/);
                            if (m) precoSecundarioTxt = m[0];
                        }
                    }
                }
                if (!precoTxt && precoSecundarioTxt) precoTxt = precoSecundarioTxt;
                
                if (!linkFisico) {
                    stats.so_kindle++;
                    continue;
                }
                if (!precoTxt) {
                    stats.sem_preco++;
                    continue;
                }
                
                stats.validos++;
                const texto = el.innerText || '';
                itens.push({
                    nome: nome,
                    url: linkFisico.href.split('/ref=')[0].split('?')[0],
                    img: img ? img.src : '',
                    preco_txt: precoTxt,
                    antigo_txt: antigoTxt,
                    prevenda: texto.includes('Pré-venda') || texto.includes('Será lançado')
                });
            }
            return { stats, itens };
        }""")
            
        st = resultado_pag["stats"]
        lista_bruta = resultado_pag["itens"]
        print(f"   [Raio-X Pág {pagina_num}] {st['total']} cards na tela -> {st['validos']} físicos válidos | Ignorados: {st['importados']} Importados, {st['so_kindle']} Só Kindle, {st['sem_preco']} Esgotados/Sem preço.")
        
        novos_na_pag = 0
        for item in lista_bruta:
            if not item["url"] or not item["nome"] or item["url"] in urls_vistas:
                continue
            urls_vistas.add(item["url"])
            
            preco_atual = limpar_preco_br(item["preco_txt"])
            if preco_atual <= 0.0:
                continue
            
            preco_original = limpar_preco_br(item["antigo_txt"]) if item["antigo_txt"] else preco_atual
            if preco_original < preco_atual:
                preco_original = preco_atual
                
            desconto_pct = round(((preco_original - preco_atual) / preco_original) * 100) if preco_original > preco_atual else 0
            status_estoque = "Pré-venda" if item["prevenda"] else "Em estoque"
            
            loja_final = identificar_editora(item["nome"], editora_padrao)
            produtos_extraidos.append({
                "plataforma": "Amazon",
                "loja": loja_final,
                "categoria": identificar_categoria(item["nome"], loja_final.lower(), preco_atual),
                "nome": item["nome"],
                "url": item["url"],
                "imagem_url": item["img"],
                "preco_original": preco_original,
                "preco_atual": preco_atual,
                "desconto_pct": desconto_pct,
                "status": status_estoque,
                "disponivel": True
            })
            novos_na_pag += 1
        
        if st["validos"] > novos_na_pag:
            print(f"   [Info] Dos {st['validos']} válidos, {st['validos'] - novos_na_pag} já tinham sido lidos em páginas/buscas anteriores.")
        
        botao_prox = pagina.locator("a.s-pagination-next:not(.s-pagination-disabled)").first
        if botao_prox.count() > 0 and pagina_num < max_paginas:
            prox_href = botao_prox.get_attribute("href")
            if prox_href:
                url_atual = f"https://www.amazon.com.br{prox_href}" if prox_href.startswith("/") else prox_href
                if "rh=" in url_inicial and "rh=" not in url_atual:
                    rh_original = [p for p in url_inicial.split("&") if p.startswith("rh=")][0]
                    url_atual += f"&i=stripbooks&{rh_original}"
                pagina_num += 1
            else:
                url_atual = None
        else:
            motivo = "Limite de páginas atingido" if pagina_num >= max_paginas else "Última página da categoria atingida (botão Próximo desativado)"
            print(f"   [Fim do Link] Paginação encerrada na Página: {pagina_num}: {motivo}.")
            url_atual = None
        
    return produtos_extraidos

def extrair_amazon(pagina, url_produto):
    """Extrai dados de um produto individual da Amazon (para a Wishlist)."""
    print(f"Consultando Amazon: {url_produto}...")
    try:
        pagina.goto(url_produto, wait_until="domcontentloaded", timeout=60000)
        pagina.wait_for_timeout(1500)
        
        if pagina.locator("#productTitle").count() == 0:
            print(f"   [Aviso Amazon] Página bloqueada (Captcha) ou titulo não carregou: {url_produto}")
            return None
        
        titulo = pagina.locator("#productTitle").first.inner_text().strip()
        img_el = pagina.locator("#landingImage, #imgBlkFront").first
        imagem_url = img_el.get_attribute("src") if img_el.count() > 0 else ""
        
        loc_atual = pagina.locator(
            '#corePriceDisplay_desktop_feature_div .priceToPay .a-offscreen, '
            '#corePriceDisplay_desktop_feature_div .apexPriceToPay .a-offscreen, '
            '#corePrice_feature_div .a-offscreen, '
            '#tmmSwatches .swatchElement.selected .slot-price span'
        ).first
        preco_atual = limpar_preco_br(loc_atual.text_content()) if loc_atual.count() > 0 else 0.0
        
        if preco_atual <= 0.0:
            inteiro = pagina.locator('#corePriceDisplay_desktop_feature_div .a-price-whole').first
            centavos = pagina.locator('#corePriceDisplay_desktop_feature_div .a-price-fraction').first
            if inteiro.count() > 0:
                txt_int = inteiro.inner_text().replace(".", "").replace(",", "").strip()
                txt_cent = centavos.inner_text().strip() if centavos.count() > 0 else "00"
                preco_atual = limpar_preco_br(f"{txt_int},{txt_cent}")
        
        loc_antigo = pagina.locator(
            '#corePriceDisplay_desktop_feature_div .basisPrice .a-offscreen, '
            'span[data-a-strike="true"] .a-offscreen'
        ).first
        preco_original = limpar_preco_br(loc_antigo.text_content()) if loc_antigo.count() > 0 else preco_atual
        if preco_original < preco_atual or preco_atual <= 0.0:
            preco_original = preco_atual
        
        desconto_pct = round(((preco_original - preco_atual) / preco_original) * 100) if (preco_atual > 0 and preco_original > preco_atual) else 0
        disponivel = preco_atual > 0.0 and pagina.locator("#add-to-cart-button, #buy-now-button").count() > 0
        status_estoque = "Em estoque" if disponivel else "Indisponível"
        
        texto_pag = pagina.locator("#bylineInfo, #detailBullets_feature_div, #rpi-attribute-book_details-publisher").all_inner_texts()
        texto_ed = " ".join(texto_pag).lower()
        editora = identificar_editora(f"{titulo} {texto_ed}", "Outras")
        
        return {
            "plataforma": "Amazon",
            "loja": editora,
            "categoria": identificar_categoria(titulo, editora.lower(), preco_atual if preco_atual > 0 else 10.0),
            "nome": titulo,
            "url": url_produto,
            "imagem_url": imagem_url,
            "preco_original": preco_original,
            "preco_atual": preco_atual,
            "desconto_pct": desconto_pct,
            "status": status_estoque,
            "disponivel": disponivel
        }
    except Exception as erro:
        print(f"   [Erro] Falha ao ler produto Amazon {url_produto}: {erro}")
        return None

def extrair_vitrine_mercadolivre(pagina, url_inicial, editora_padrao="Panini", max_paginas=100, urls_vistas=None):
    """Crawler Turbo para buscas de HQs/Mangás no Mercado Livre."""
    url_atual = url_inicial
    pagina_num = 1
    produtos_extraidos = []
    if urls_vistas is None:
        urls_vistas = set()
    urls_ml_sessao = set()
    
    print(f"\n[Mercado Livre • {editora_padrao}] Varrendo Página 1: {url_inicial}...")
    try:
        resposta = pagina.goto(url_inicial, wait_until="domcontentloaded", timeout=60000)
        if not resposta or resposta.status != 200:
            print(f"Erro ao acessar Mercado Livre. Status: {resposta.status if resposta else 'Sem resposta'}")
            return produtos_extraidos
    except Exception as erro:
        print(f"   [Aviso ML] Falha ao abrir link inicial: {erro}")
        return produtos_extraidos

    while pagina_num <= max_paginas:
        if cancelar_varredura:
            break

        try:
            pagina.wait_for_selector("div.poly-card, li.ui-search-layout__item, div.ui-search-result", state="attached", timeout=20000)
            pagina.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            pagina.wait_for_timeout(2000)
        except Exception as erro:
            print(f"   [Aviso ML] Bloqueio ou página vazia ({pagina.title()} -> {pagina.url})")
            break

        cards = pagina.locator("li.ui-search-layout__item, div.poly-card:not(li.ui-search-layout__item *)")
        lista_bruta = cards.evaluate_all("""els => els.map(el => {
            const link = el.querySelector('a.poly-component__title') || el.querySelector('h2 a') || el.querySelector('a.ui-search-link') || el.querySelector('a');
            const img = el.querySelector('img.poly-component__picture') || el.querySelector('img');
            const pBox = el.querySelector('.poly-price__current') || el.querySelector('.ui-search-price__second-line') || el;
            const pFrac = pBox ? pBox.querySelector('.andes-money-amount__fraction') : null;
            const pCent = pBox ? pBox.querySelector('.andes-money-amount__cents') : null;
            const oBox = el.querySelector('s.andes-money-amount');
            const oFrac = oBox ? oBox.querySelector('.andes-money-amount__fraction') : null;
            const oCent = oBox ? oBox.querySelector('.andes-money-amount__cents') : null;
            return {
                nome: link ? link.innerText.trim() : '',
                url: link ? link.href.split('#')[0].split('?')[0] : '',
                img: img ? (img.getAttribute('data-src') || img.src) : '',
                preco_txt: pFrac ? (pFrac.innerText + ',' + (pCent ? pCent.innerText : '00')) : '',
                antigo_txt: oFrac ? (oFrac.innerText + ',' + (oCent ? oCent.innerText : '00')) : ''
            };
        })""")
        print(f"Encontrados {len(lista_bruta)} itens nesta página do Mercado Livre.")

        novos_neste_lote = 0
        for item in lista_bruta:
            if not item["url"] or not item["nome"]:
                continue
            if item ["url"] not in urls_ml_sessao:
                urls_ml_sessao.add(item["url"])
                novos_neste_lote += 1
            if item["url"] in urls_vistas:
                continue
            urls_vistas.add(item["url"])

            preco_atual = limpar_preco_br(item["preco_txt"])
            preco_original = limpar_preco_br(item["antigo_txt"]) if item["antigo_txt"] else preco_atual
            if preco_original < preco_atual:
                preco_original = preco_atual

            desconto_pct = round(((preco_original - preco_atual) / preco_original) * 100) if preco_original > preco_atual else 0

            loja_final = identificar_editora(item["nome"], editora_padrao)
            produtos_extraidos.append({
                "plataforma": "Mercado Livre",
                "loja": loja_final,
                "categoria": identificar_categoria(item["nome"], loja_final.lower(), preco_atual),
                "nome": item["nome"],
                "url": item["url"],
                "imagem_url": item["img"],
                "preco_original": preco_original,
                "preco_atual": preco_atual,
                "desconto_pct": desconto_pct,
                "status": "Em estoque" if preco_atual > 0 else "Indisponível",
                "disponivel": preco_atual > 0
            })
            
        if pagina_num > 1 and novos_neste_lote == 0:
            print(f"   [Fim do Link ML] Nenhum anúncio inédito na Página {pagina_num}. Passando para o próximo link!")
            break
        
        if pagina_num >= max_paginas:
            print(f"   [Fim do Link ML] Limite de {max_paginas} páginas atingido.")
            break
        
        botao_prox = pagina.locator(
            "li.andes-pagination__button--next:not(.andes-pagination__button--disabled) a, "
            "li.andes-pagination__button--next:not(.andes-pagination__button--disabled) button, "
            "a.andes-pagination__link[title='Seguinte']:not([aria-disabled='true']), "
            "a.andes-pagination__link:has-text('Seguinte'):not([aria-disabled='true'])"
        ).first
        
        try:
            botao_prox.scroll_into_view_if_needed(timeout=5000)
            pagina.wait_for_timeout(500)
            prox_href = botao_prox.get_attribute("href")
            pagina_num += 1
            
            if prox_href and not prox_href.startswith("#") and not prox_href.startswith("javascript"):
                url_prox = prox_href if prox_href.startswith("http") else f"https://lista.mercadolivre.com.br{prox_href}"
                print(f"\n[Mercado Livre • {editora_padrao}] Varrendo Página {pagina_num}: {url_prox}...")
                pagina.goto(url_prox, wait_until="domcontentloaded", timeout=60000)
            else:
                primeiro_antes = lista_bruta[0]["url"] if lista_bruta else ""
                print(f"\n[Mercado Livre • {editora_padrao}] Varrendo Página {pagina_num} (clicando em 'Seguinte')...")
                botao_prox.click(force=True)
                for _ in range(20):
                    pagina.wait_for_timeout(500)
                    primeiro_agora = pagina.evaluate("""() => {
                        const el = document.querySelector('li.ui-search-layout__item a, div.poly-card a');
                        return el ? el.href.split('#')[0].split('?')[0] : '';
                    }""")
                    if primeiro_agora and primeiro_agora != primeiro_antes:
                        break
        except Exception as erro:
            print(f"   [Fim do Link ML] Paginação encerrada na Página {pagina_num}: {erro}")
            break

    return produtos_extraidos

def extrair_mercadolivre(pagina, url_produto):
    """Extrai dados de um anúncio individual do Mercado Livre (para a Wishlist)."""
    print(f"Consultando Mercado Livre: {url_produto}...")
    try:
        pagina.goto(url_produto, wait_until="domcontentloaded", timeout=60000)
        titulo = pagina.locator("h1.ui-pdp-title").first.inner_text().strip()
        img_el = pagina.locator("figure.ui-pdp-gallery__figure img").first
        imagem_url = img_el.get_attribute("src") if img_el.count() > 0 else ""

        p_frac = pagina.locator("div.ui-pdp-price__second-line .andes-money-amount__fraction").first
        p_cent = pagina.locator("div.ui-pdp-price__second-line .andes-money-amount__cents").first
        preco_txt = f"{p_frac.inner_text()},{p_cent.inner_text() if p_cent.count() > 0 else '00'}" if p_frac.count() > 0 else "0,00"
        preco_atual = limpar_preco_br(preco_txt)

        o_frac = pagina.locator("s.ui-pdp-price__original-value .andes-money-amount__fraction").first
        o_cent = pagina.locator("s.ui-pdp-price__original-value .andes-money-amount__cents").first
        antigo_txt = f"{o_frac.inner_text()},{o_cent.inner_text() if o_cent.count() > 0 else '00'}" if o_frac.count() > 0 else ""
        preco_original = limpar_preco_br(antigo_txt) if antigo_txt else preco_atual

        desconto_pct = round(((preco_original - preco_atual) / preco_original) * 100) if preco_original > preco_atual else 0
        disponivel = preco_atual > 0.0 and pagina.locator("button.ui-pdp-action--primary").count() > 0

        texto_t = titulo.lower()
        editora = identificar_editora(titulo, "Outras")

        return {
            "plataforma": "Mercado Livre",
            "loja": editora,
            "categoria": identificar_categoria(titulo, editora.lower(), preco_atual),
            "nome": titulo,
            "url": url_produto,
            "imagem_url": imagem_url,
            "preco_original": preco_original,
            "preco_atual": preco_atual,
            "desconto_pct": desconto_pct,
            "status": "Em estoque" if disponivel else "Indisponível",
            "disponivel": disponivel
        }
    except Exception as erro:
        print(f"   [Erro] Falha ao ler produto Mercado Livre {url_produto}: {erro}")
        return None