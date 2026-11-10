from playwright.sync_api import sync_playwright
from scraper import (
    extrair_panini, extrair_vitrine_panini,
    extrair_newpop, extrair_vitrine_newpop, 
    extrair_vitrine_pipoca, extrair_jbc, extrair_vitrine_jbc,
    extrair_amazon, extrair_vitrine_amazon,
    extrair_mercadolivre, extrair_vitrine_mercadolivre
)
from database import inicializar_banco, salvar_leitura, atualizar_status_alerta, conectar, listar_urls_favoritos, registrar_inicio_log, finalizar_log
from notificador import enviar_alerta_ntfy
import ctypes

DESCONTO_MINIMO_WISHLIST = 25
DESCONTO_MINIMO_PCT = 70

VITRINES_MONITORADAS = [
    ("Marvel", f"https://panini.com.br/marvel?product_list_limit=36"),
    ("Mangás", f"https://panini.com.br/planet-manga?product_list_limit=36"),
    ("DC", f"https://panini.com.br/dc-comics?product_list_limit=36"),
    ("Livros/Novels",f"https://panini.com.br/panini-books?product_list_limit=36"),
    ("Outras HQs", f"https://panini.com.br/panini-comics?product_list_limit=36"),
    ("Turma da Mônica", f"https://panini.com.br/mauricio-de-sousa-catalogo?product_list_limit=36"),
    #"https://panini.com.br/novidades/pre-vendas?product_list_limit=36", #Pré-venda
    #"https://panini.com.br/novidades/reimpressao?product_list_limit=36", #Reimpressão
    #"https://panini.com.br/desconto-saldao?product_list_limit=36", #Saldão
    #"https://panini.com.br/promos?product_list_limit=36", #Promos
    #"https://panini.com.br/desconto-manga?product_list_limit=36", #Desconto-Mangás
    #"https://panini.com.br/planet-manga/box-mangas?product_list_limit=36", #Box Mangás
    #"https://panini.com.br/catalogsearch/result/?q=tokyo+ghoul&product_list_limit=36", #Tokyo Ghoul
]

VITRINES_NEWPOP = [
    "https://www.lojanewpop.com.br/",
    "https://www.lojanewpop.com.br/mangas",
    "https://www.lojanewpop.com.br/one-shots",
    "https://www.lojanewpop.com.br/livrosnovels-",
    "https://www.lojanewpop.com.br/nacionais",
    "https://www.lojanewpop.com.br/pre-venda",
    #"https://www.lojanewpop.com.br/pacotes",
    #"https://www.lojanewpop.com.br/marca/aca.html",
    #"https://www.lojanewpop.com.br/marca/aventura.html",
    #"https://www.lojanewpop.com.br/marca/classicos.html",
    #"https://www.lojanewpop.com.br/marca/comedia.html",
    #"https://www.lojanewpop.com.br/marca/drama.html",
    #"https://www.lojanewpop.com.br/marca/novels.html",
    #"https://www.lojanewpop.com.br/marca/shoujo.html",
    #"https://www.lojanewpop.com.br/marca/suspense.html",
]

VITRINES_PIPOCA = [
    "https://pipocaenanquim.com.br/mangas.html",
    "https://pipocaenanquim.com.br/quadrinhos.html",
    "https://pipocaenanquim.com.br/livros.html",
    "https://pipocaenanquim.com.br/colec-o.html",
    #"https://pipocaenanquim.com.br/promoc-o.html",
    #"https://pipocaenanquim.com.br/pre-vendas.html",
]

VITRINES_MPEG = [
    "https://mpeg.com.br/mangas?product_list_limit=36",
    "https://mpeg.com.br/novels?product_list_limit=36",
    "https://mpeg.com.br/prevendas?product_list_limit=36",
]

VITRINES_JBC = [
    "https://www.companhiadasletras.com.br/JBC?brand=jbc&fuzzy=0&operator=and&facets=brand%2Cfuzzy%2Coperator&sort=score_desc&page=0",
]

FILTRO_AMZ_CAT = "i=stripbooks&rh=n%3A7842710011%2Cp_n_feature_nine_browse-bin%3A8529758011%2Cp_n_condition-type%3A13862762011"

BUSCAS_AMAZON = [
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842726011%2Cn%3A7842740011%2Cp_n_feature_browse-bin%3A8561251011&s=relevancerank&dc&ds=v1%3AewLDUuNgqaqAQtmYTu%2BvMOUY31DxTvzKUNnDtqn1P1w&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793302350&rnid=7842726011&unfiltered=1&ref=sr_nr_n_13"), #Todas - Relevância : Graphic Novels - Super Herois - Capa Comum
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842726011%2Cn%3A7842740011%2Cp_n_feature_browse-bin%3A8561250011&s=relevancerank&dc&ds=v1%3AbGtMokZ%2Fq2%2BGH8nHUK%2Bzc6Yz1ynoZ%2FcE9SycixyjEDU&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793302417&rnid=7842726011&unfiltered=1&ref=sr_nr_n_13"), #Todas - Relevância : Graphic Novels - Super Herois - Capa Dura
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842726011%2Cn%3A16312026011&s=relevancerank&dc&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793302510&unfiltered=1&ref=sr_ex_p_n_feature_browse-b_0&ds=v1%3AuwRPDkDDtcpAoNvznf7xKnPAMWeaSI5vi9i6r7ocbx4"), #Todas - Relevância : Graphic Novels - Adaptações
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842726011%2Cn%3A7842727011&s=relevancerank&dc&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793302629&unfiltered=1&ref=sr_ex_p_n_feature_browse-b_0&ds=v1%3AuBihrKCmW%2BDQSlbjWqk%2FDSQyua%2FZR%2FdUEnNlLAEcGNg"), #Todas - Relevância : Graphic Novels - Antologias
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842726011%2Cn%3A7842729011&s=relevancerank&dc&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793302694&unfiltered=1&ref=sr_ex_p_n_feature_browse-b_0&ds=v1%3AvEgAtcCpcdMonN15xCbetnOHgpk8FwCNFE3dxhVlWsM"), #Todas - Relevância : Graphic Novels - Fantasia
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842726011%2Cn%3A7842728011&s=relevancerank&dc&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793302786&unfiltered=1&ref=sr_ex_p_n_feature_browse-b_0&ds=v1%3ATUttPPMXUl%2BmDvUoKfSiWv9%2BD%2BxXT4JDdr%2BsZ7aBPj4"), #Todas - Relevância : Graphic Novels - Ficção Científica
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842726011%2Cn%3A7842730011&s=relevancerank&dc&ds=v1%3A1bVTzc0TxsbDXMfbhnzTcAaIoRKHjwC8O2Ds8IG58fA&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793302308&rnid=7842726011&unfiltered=1&ref=sr_nr_n_5"), #Todas - Relevância : Graphic Novels - Ficção Histórica
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842726011%2Cn%3A7842733011&s=relevancerank&dc&ds=v1%3AMvtMZHLVninaag3d%2Bshjdh3o9DwUucXFBP91xntrYzA&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793302308&rnid=7842726011&unfiltered=1&ref=sr_nr_n_6"), #Todas - Relevância : Graphic Novels - Horror
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842726011%2Cn%3A7842734011&s=relevancerank&dc&ds=v1%3ArzRziUIXFc%2BJ0meEXth8W7kO52gLkCkbXRHKV9V4sqg&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793302308&rnid=7842726011&unfiltered=1&ref=sr_nr_n_7"), #Todas - Relevância : Graphic Novels - Literária
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842726011%2Cn%3A7842736011&s=relevancerank&dc&ds=v1%3AcnRhXqtBWORpJ5IqPbf4eZc9vjEuT0wgq%2FETWbRK0zE&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793302308&rnid=7842726011&unfiltered=1&ref=sr_nr_n_8"), #Todas - Relevância : Graphic Novels - Mistério
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842726011%2Cn%3A7842735011&s=relevancerank&dc&ds=v1%3Aqe4P3CVsxyMHuVpVBe4HKVLCHOZ3ylr4NOJ2Umt4fCI&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793302308&rnid=7842726011&unfiltered=1&ref=sr_nr_n_9"), #Todas - Relevância : Graphic Novels - Média Tie-in
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842726011%2Cn%3A7842738011&s=relevancerank&dc&ds=v1%3ArUbZGs8I7ZjoYzFjGNBS5kOoEYUidqzPfI%2FdS%2FjGLD4&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793302308&rnid=7842726011&unfiltered=1&ref=sr_nr_n_10"), #Todas - Relevância : Graphic Novels - Não-Ficção
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842726011%2Cn%3A16312032011&s=relevancerank&dc&ds=v1%3Ac2vO8mMFl%2BPRDPSXA5f9I3USfhfGdjw1Yh%2FwVC99wa8&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793302308&rnid=7842726011&unfiltered=1&ref=sr_nr_n_11"), #Todas - Relevância : Graphic Novels - Religião e Espiritualidade
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842726011%2Cn%3A7842739011&s=relevancerank&dc&ds=v1%3Avq%2F5uKite0ef2xGdlnqa%2BoPZXPUDqm7EYlNNQmqgMww&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793302308&rnid=7842726011&unfiltered=1&ref=sr_nr_n_12"), #Todas - Relevância : Graphic Novels - Romance
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842714011%2Cn%3A7842716011&s=relevancerank&dc&ds=v1%3A5rnN7m57V1blU1z4OKeTGJXgHj%2F1FoZB7I9cGcOrcoE&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793303227&rnid=7842714011&unfiltered=1&ref=sr_nr_n_1"), #Todas - Relevância : Mangá - Esportes
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842714011%2Cn%3A7842717011&s=relevancerank&dc&ds=v1%3A9pmqZ%2F1CAPeclXIJ5g69LQN6DJl%2B7GwR%2BdGRtsV2fCc&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793303227&rnid=7842714011&unfiltered=1&ref=sr_nr_n_2"), #Todas - Relevância : Mangá - Fantasia
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842714011%2Cn%3A7842715011&s=relevancerank&dc&ds=v1%3AWwW3gRfVEJrWGuwuG76VoOh3HDTNTtged4VWh17kUsM&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793303227&rnid=7842714011&unfiltered=1&ref=sr_nr_n_3"), #Todas - Relevância : Mangá - Ficção Científica
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842714011%2Cn%3A7842723011&s=relevancerank&dc&ds=v1%3AwjnJXjG6%2FW66VrLLpVF5ypYtJwulC64v3KxwazI%2F8b8&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793303239&rnid=7842714011&unfiltered=1&ref=sr_nr_n_4"), #Todas - Relevância : Mangá - Mistério, Suspense e Crime
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842714011%2Cn%3A7842722011&s=relevancerank&dc&ds=v1%3AQ%2BQLFA9%2BPK8OJ%2BatkhyY1dXllC9xjRPWoj8q7VibkfQ&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793303239&rnid=7842714011&unfiltered=1&ref=sr_nr_n_5"), #Todas - Relevância : Mangá - Mídia Tie-in
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842714011%2Cn%3A23723368011&s=relevancerank&dc&ds=v1%3AnP8dNGHHdkY944fJfncHwFSm2pgfiwNLgPtBZ5yGQjM&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793303239&rnid=7842714011&unfiltered=1&ref=sr_nr_n_6"), #Todas - Relevância : Mangá - Josei
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842714011%2Cn%3A23723369011&s=relevancerank&dc&ds=v1%3AhEV5BsKRy3IE3EM7ChjE6uH2YEfA%2Bc7nHLD3TUSlsWc&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793303239&rnid=7842714011&unfiltered=1&ref=sr_nr_n_7"), #Todas - Relevância : Mangá - Seinen
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842714011%2Cn%3A23723367011&s=relevancerank&dc&ds=v1%3AxbW2b16COM1LO7aYCwrhYacMkU9rfpM6b5rS7i7LZwU&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793303239&rnid=7842714011&unfiltered=1&ref=sr_nr_n_8"), #Todas - Relevância : Mangá - Shoujo
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842714011%2Cn%3A23723370011&s=relevancerank&dc&ds=v1%3AZsn7rcEzdTTySs54Fk3hAmBF6ZKDvImabIoF%2BVF6BcY&Adv-Srch-Books-Submit.x=69&Adv-Srch-Books-Submit.y=11&qid=1793303239&rnid=7842714011&unfiltered=1&ref=sr_nr_n_9"), #Todas - Relevância : Mangá - Shonen
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842726011%2Cp_n_feature_browse-bin%3A8561251011&s=date-desc-rank&dc&ds=v1%3A6c%2FA1GwMC81bbK7nR7brx6NVRegbekaJ4Q2MCJdJgoI&Adv-Srch-Books-Submit.x=66&Adv-Srch-Books-Submit.y=6&qid=1793303709&rnid=7842710011&unfiltered=1&ref=sr_nr_n_1"), #Todas: Lançamentos - Graphic Novels - Capa Comum
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842726011%2Cp_n_feature_browse-bin%3A8561250011&s=date-desc-rank&dc&ds=v1%3ADVEcJbVT68ZQ0ew0gBVfo1GnVJV9U0k0wrOq44mo6zI&Adv-Srch-Books-Submit.x=66&Adv-Srch-Books-Submit.y=6&qid=1793303711&rnid=7842710011&unfiltered=1&ref=sr_nr_n_1"), #Todas: Lançamentos - Graphic Novels - Capa Dura
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842714011%2Cp_n_feature_browse-bin%3A8561251011&s=date-desc-rank&dc&ds=v1%3AkEDdOQqnRRrWYHcIsnpEy%2BP0yJv0HP2RIwDygv7xCM0&Adv-Srch-Books-Submit.x=66&Adv-Srch-Books-Submit.y=6&qid=1793303699&rnid=7842710011&unfiltered=1&ref=sr_nr_n_2"), #Todas: Lançamentos - Mangá - Capa Comum
    ("Outras", f"https://www.amazon.com.br/s?i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842714011%2Cp_n_feature_browse-bin%3A8561250011&s=date-desc-rank&dc&ds=v1%3APjrKy4poHWoSCLaJ0rhoPbmrgOPCDc3BDa297n5JzFs&Adv-Srch-Books-Submit.x=66&Adv-Srch-Books-Submit.y=6&qid=1793303701&rnid=7842710011&unfiltered=1&ref=sr_nr_n_2"), #Todas: Lançamentos - Mangá - Capa Dura 
    ("Panini", f"https://www.amazon.com.br/s?k=panini&i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842726011%2Cp_n_feature_browse-bin%3A8561251011&s=relevancerank&dc&ds=v1%3AWvS%2BqYg5VwhinrzPTcO0IINMqZwscWQC9d39DT0mYpg&Adv-Srch-Books-Submit.x=54&Adv-Srch-Books-Submit.y=9&qid=1793305445&rnid=7842710011&unfiltered=1&ref=sr_nr_n_1"), #Panini - Graphic Novels - Capa Comum 
    ("Panini", f"https://www.amazon.com.br/s?k=panini&i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842726011%2Cp_n_feature_browse-bin%3A8561250011&s=relevancerank&dc&ds=v1%3AMz%2BvdvfjMJ9YJ3cX46YpuCGvtTPLXp1DVBqTFKewHyA&Adv-Srch-Books-Submit.x=54&Adv-Srch-Books-Submit.y=9&qid=1793305476&rnid=7842710011&unfiltered=1&ref=sr_nr_n_1"),  #Panini - Graphic Novels - Capa Dura
    ("Panini", f"https://www.amazon.com.br/s?k=panini&i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842714011%2Cp_n_feature_browse-bin%3A8561251011&s=relevancerank&dc&ds=v1%3ArAU4d%2BXeDRN5YOsEpb5FflTWVyUhrY1cX2vv9WEStsE&Adv-Srch-Books-Submit.x=54&Adv-Srch-Books-Submit.y=9&qid=1793305685&rnid=7842710011&unfiltered=1&ref=sr_nr_n_2"), #Panini - Mangá - Capa Comum 
    ("Panini", f"https://www.amazon.com.br/s?k=panini&i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842714011%2Cp_n_feature_browse-bin%3A8561250011&s=relevancerank&dc&ds=v1%3AUY8Lddbc60X5mwgax%2FyVnpuZx91XJ8YhzEJhePKTKH8&Adv-Srch-Books-Submit.x=54&Adv-Srch-Books-Submit.y=9&qid=1793305599&rnid=7842710011&unfiltered=1&ref=sr_nr_n_2"), #Panini - Mangá - Capa Dura
    ("NewPOP", f"https://www.amazon.com.br/s?k=newpop&i=stripbooks&rh=n%3A7842710011&s=relevancerank&Adv-Srch-Books-Submit.x=0&Adv-Srch-Books-Submit.y=0&unfiltered=1&ref=sr_adv_b"),
    ("JBC", f"https://www.amazon.com.br/s?k=jbc&i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842714011&s=relevancerank&dc&ds=v1%3AUeaYXyiNBLDXQGPKuWRm%2FhdgIYxm0pPryBFjYH%2B57rE&Adv-Srch-Books-Submit.x=61&Adv-Srch-Books-Submit.y=11&qid=1793305864&rnid=7842710011&unfiltered=1&ref=sr_nr_n_2"), #JBC - Mangá
    ("JBC", f"https://www.amazon.com.br/s?k=jbc&i=stripbooks&rh=n%3A6740748011%2Cn%3A7842710011%2Cn%3A7842726011&s=relevancerank&dc&ds=v1%3AOwyQaxpI%2BV8goUkjvkbIZkA2uhyC%2FRZSKD4H%2Fany3yw&Adv-Srch-Books-Submit.x=61&Adv-Srch-Books-Submit.y=11&qid=1793305864&rnid=7842710011&unfiltered=1&ref=sr_nr_n_1"), #JBC - Graphic Novel
    ("Pipoca & Nanquim", f"https://www.amazon.com.br/s?k=pipoca+%26+nanquim&i=stripbooks&rh=n%3A7842710011&s=relevancerank&Adv-Srch-Books-Submit.x=27&Adv-Srch-Books-Submit.y=5&unfiltered=1&ref=sr_adv_b"),
    ("MPEG", f"https://www.amazon.com.br/s?k=mpeg&i=stripbooks&rh=n%3A7842710011&s=relevancerank&Adv-Srch-Books-Submit.x=0&Adv-Srch-Books-Submit.y=0&unfiltered=1&ref=sr_adv_b"),
    ("Outras", f"https://www.amazon.com.br/s?k=darkside&i=stripbooks&rh=n%3A7842710011&s=relevancerank&Adv-Srch-Books-Submit.x=37&Adv-Srch-Books-Submit.y=6&unfiltered=1&ref=sr_adv_b"), #DarkSide
    ("Outras", f"https://www.amazon.com.br/s?k=comix+zone&i=stripbooks&rh=n%3A7842710011&s=relevancerank&Adv-Srch-Books-Submit.x=57&Adv-Srch-Books-Submit.y=5&unfiltered=1&ref=sr_adv_b"), #Comix Zone
]

BUSCAS_MERCADOLIVRE = [
    ("Outras", "https://lista.mercadolivre.com.br/_Container_lpml-hqs-e-mangas-set26"),
    ("Panini", "https://lista.mercadolivre.com.br/livros-revistas-comics/hqs-mangas/novo/panini"),
    ("JBC", "https://lista.mercadolivre.com.br/livros-revistas-comics/hqs-mangas/novo/jbc"),
    ("NewPOP", "https://lista.mercadolivre.com.br/livros-revistas-comics/hqs-mangas/novo/newpop"),
]

URLS_INDIVIDUAIS = [
    #"https://panini.com.br/surfista-prateado-escuridao-marvel-essenciais",
    #"https://panini.com.br/demolidor-a-queda-de-murdock-adequ001r2",
    #"https://panini.com.br/marvel-boy-marvel-essenciais",
    #"https://panini.com.br/a-essencia-do-medo-marvel-essenciais",
]

def processar_produto(dados, conexao=None):
    """Salva o quadrinho no PostgreSQL e gerencia a trava de notificação."""
    if dados.get("plataforma", "Editoras") != "Editoras" and dados.get("categoria") == "Excluídos":
        return 
    prod_id, alerta_ja_enviada, eh_favorito, preco_alvo, menor_historico = salvar_leitura(dados, conexao)
    dados["eh_menor_historico"] = dados["preco_atual"] <= menor_historico and dados["desconto_pct"] > 0
    estrela = "⭐ " if eh_favorito else ""
    alvo_txt = f" [🎯 Alvo: R$ {preco_alvo:.2f}]" if preco_alvo > 0 else ""
    print(f"[DB] [{dados.get('loja', 'Panini')}] | ID #{prod_id} | {estrela}{dados['nome']}{alvo_txt} | R$ {dados['preco_atual']:.2f} | ({dados['desconto_pct']}% OFF) | {dados['status']}")
    
    meta_desconto = DESCONTO_MINIMO_WISHLIST if eh_favorito else DESCONTO_MINIMO_PCT
    bateu_desconto = dados["desconto_pct"] >= meta_desconto
    bateu_alvo_reais = preco_alvo > 0 and 0 < dados["preco_atual"] <= preco_alvo
    
    em_promocao_valida = (
        dados["disponivel"] 
        and (bateu_desconto or bateu_alvo_reais)
        and dados.get("categoria") != "Excluídos"
    )
    
    if em_promocao_valida:
        if not alerta_ja_enviada:
            recorde_txt = " 🔥 (MENOR PREÇO HISTÓRICO!)" if dados["eh_menor_historico"] else ""
            print(f" >>> NOVA PROMOÇÂO ({dados['desconto_pct']}% OFF){recorde_txt}! Disparando Alerta...")
            enviar_alerta_ntfy(dados, meta_desconto, eh_favorito)
            atualizar_status_alerta(prod_id, True)
        else:
            print(" === Promoção já notificada anteriormente.")
    else:
        if alerta_ja_enviada:
            print(" --- Promoção encerrada ou esgotou. Resetando trava de alerta!")
            atualizar_status_alerta(prod_id, False)

import os
import scraper
from datetime import datetime

def executar_robo(modo="completo"):
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🚀 Iniciando varredura ({modo})...")
    if hasattr(ctypes, "windll"):
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
    scraper.cancelar_varredura = False
    
    ua_padrao = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    arquivo_sessao = "sessao_ml.json" if os.path.exists("sessao_ml.json") else None
    
    with sync_playwright() as p:
        if modo == "login_ml":
            nav_login = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
            ctx_login = nav_login.new_context(
                locale="pt-BR", 
                viewport={"width": 1366, "height":768},
                user_agent=ua_padrao,
                storage_state=arquivo_sessao
            )
            ctx_login.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
            pag_login = ctx_login.new_page()
            pag_login.goto("https://www.mercadolivre.com.br/livros-revistas-comics/hqs-mangas/novo/panini")
            pag_login.wait_for_timeout(60000)
            ctx_login.storage_state(path="sessao_ml.json")
            nav_login.close()
            print("[Login ML] ✅ Sessão salva em 'sessao_ml.json' com sucesso!")
            return
        
        conexao_db = conectar()
        log_id = registrar_inicio_log(modo)
            
        navegador = p.chromium.launch(
            headless=True,
            args=[
                "--headless=new",
                "--disable-blink-features=AutomationControlled",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--no-zygote"
            ]
        )
        contexto = navegador.new_context(
            locale="pt-BR",
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            storage_state=arquivo_sessao
        )
        contexto.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
        
        pagina = contexto.new_page()
        pagina.route("**/*", lambda route: route.abort() if (route.request.resource_type in ["image", "media"] and "mercadolivre" not in route.request.url) else route.continue_())
        
        urls_ja_varridas = set()
        
        if modo =="rapido":
            urls_diretas = listar_urls_favoritos() + URLS_INDIVIDUAIS
            for url in urls_diretas:
                if scraper.cancelar_varredura:
                    break
                if url in urls_ja_varridas:
                    continue
                urls_ja_varridas.add(url)
                if "lojanewpop.com.br" in url:
                    dados = extrair_newpop(pagina, url)
                elif "companhiadasletras.com.br" in url:
                    dados = extrair_jbc(pagina, url)
                elif "amazon.com.br" in url:
                    dados = extrair_amazon(pagina, url)
                elif "mercadolivre.com.br" in url:
                    dados = extrair_mercadolivre(pagina, url)
                else:
                    dados = extrair_panini(pagina, url)
                if dados:
                    processar_produto(dados, conexao_db)
        
        if modo in ("completo", "Editoras", "Panini") and not scraper.cancelar_varredura:
            for item_vitrine in VITRINES_MONITORADAS:
                if scraper.cancelar_varredura: break
                url_vitrine = item_vitrine[1] if isinstance(item_vitrine, tuple) else item_vitrine
                lista_produtos = extrair_vitrine_panini(pagina, url_vitrine ,max_paginas=100, urls_vistas=urls_ja_varridas)
                for dados in lista_produtos:
                    processar_produto(dados, conexao_db)

        if modo in ("completo", "Editoras", "NewPOP") and not scraper.cancelar_varredura:
            for url_newpop in VITRINES_NEWPOP:
                if scraper.cancelar_varredura: break
                lista_newpop = extrair_vitrine_newpop(pagina, url_newpop, max_paginas=100, urls_vistas=urls_ja_varridas)
                for dados in lista_newpop:
                    processar_produto(dados, conexao_db)
                
        if modo in ("completo", "Editoras", "Pipoca") and not scraper.cancelar_varredura:
            for url_pipoca in VITRINES_PIPOCA:
                if scraper.cancelar_varredura: break
                lista_pipoca = extrair_vitrine_pipoca(pagina, url_pipoca, max_paginas=100, urls_vistas=urls_ja_varridas)
                for dados in lista_pipoca:
                    processar_produto(dados,conexao_db)
                    
        if modo in ("completo", "Editoras", "MPEG") and not scraper.cancelar_varredura:
            for url_mpeg in VITRINES_MPEG:
                if scraper.cancelar_varredura: break
                lista_mpeg = extrair_vitrine_pipoca(pagina, url_mpeg, max_paginas=100, urls_vistas=urls_ja_varridas)
                for dados in lista_mpeg:
                    processar_produto(dados, conexao_db)
                    
        if modo in ("completo", "Editoras", "JBC") and not scraper.cancelar_varredura:
            for url_jbc in VITRINES_JBC:
                if scraper.cancelar_varredura: break
                lista_jbc = extrair_vitrine_jbc(pagina, url_jbc, max_cliques=100, urls_vistas=urls_ja_varridas)
                for dados in lista_jbc:
                    processar_produto(dados, conexao_db)
                    
        if modo in ("completo", "Amazon", "Marketplaces") and not scraper.cancelar_varredura:
            for editora_nome, url_amz in BUSCAS_AMAZON:
                if scraper.cancelar_varredura: break
                lista_amz = extrair_vitrine_amazon(pagina, url_amz, editora_padrao=editora_nome, max_paginas=100, urls_vistas=urls_ja_varridas)
                for dados in lista_amz:
                    processar_produto(dados, conexao_db)
                    
        if modo in ("completo", "Mercado Livre", "Marketplaces") and not scraper.cancelar_varredura:
            for editora_nome, url_ml in BUSCAS_MERCADOLIVRE:
                if scraper.cancelar_varredura: break
                lista_ml = extrair_vitrine_mercadolivre(pagina, url_ml, editora_padrao=editora_nome, max_paginas=100, urls_vistas=urls_ja_varridas)
                for dados in lista_ml:
                    processar_produto(dados, conexao_db)
        
        navegador.close()
        conexao_db.close()
        if scraper.cancelar_varredura:
            finalizar_log(log_id, len(urls_ja_varridas), "⏹️ Interrompida")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏹️ Varredura interrompida pelo usuário ({len(urls_ja_varridas)} itens lidos)!")
        else:
            finalizar_log(log_id, len(urls_ja_varridas), "✅ Concluída")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Varredura concluída com sucesso ({len(urls_ja_varridas)} itens lidos)!")
    
    if hasattr(ctypes, "windll"):
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)

if __name__ == "__main__":
    executar_robo()