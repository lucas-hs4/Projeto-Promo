import subprocess
import time
import threading
from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import (
    inicializar_banco, listar_ofertas, alternar_favorito,
    buscar_historico_produto, definir_preco_alvo, conectar,
    definir_titulo_editado, listar_logs, obter_config, salvar_config, ocultar_produto
)
from main import executar_robo

app = Flask(__name__)

robo_em_execucao = False
modo_atual = None
fila_varreduras = []
intervalo_auto_min = 0
lock_fila = threading.Lock()

REGRAS_AUTO = [
    ("rapido", "ult_wishlist", 3 * 3600, " Wishlist (3h)"),
    ("Amazon", "ult_amazon", 5 * 3600, " Amazon (5h)"),
    ("Mercado Livre", "ult_ml", 3 * 3600, " Mercado Livre (3h)"),
    ("Editoras", "ult_editoras", 72 * 3600, " Editoras (3 dias)")
]

def enfileirar_ou_rodar(modo):
    """Inicia a varredura imediatamente se estiver livre, ou coloca na fila de espera."""
    global robo_em_execucao
    with lock_fila:
        if not robo_em_execucao:
            robo_em_execucao = True
            threading.Thread(target=rodar_robo_background, args=(modo,), daemon=True).start()
        elif modo != modo_atual and modo not in fila_varreduras:
            fila_varreduras.append(modo)

def rodar_robo_background(modo="completo"):
    global robo_em_execucao, modo_atual
    with lock_fila:
        modo_atual = modo
    try:
        agora = int(time.time())
        for m_regra, chave_db, _, _ in REGRAS_AUTO:
            if modo == m_regra or (modo == "completo" and m_regra != "rapido"):
                salvar_config(chave_db, agora)
        executar_robo(modo)
    finally:
        with lock_fila:
            if fila_varreduras:
                proximo = fila_varreduras.pop(0)
                threading.Thread(target=rodar_robo_background, args=(proximo,), daemon=True).start()
            else:
                modo_atual = None
                robo_em_execucao = False
        
def loop_agendador():
    """Verifica a cada 30s se alguma aba atingiu seu horário (3h Marketplaces / 3d Editoras)."""
    while True:
        time.sleep(30)
        if intervalo_auto_min <= 0:
            continue
        agora = int(time.time())
        for modo_regra, chave_db, intervalo_seg, _ in REGRAS_AUTO:
            ult = obter_config(chave_db, 0)
            if ult == 0:
                salvar_config(chave_db, agora)
            elif (agora - ult) >= intervalo_seg:
                salvar_config(chave_db, agora)
                enfileirar_ou_rodar(modo_regra)
                
threading.Thread(target=loop_agendador, daemon=True).start()               

@app.route("/")
def index():
    desconto_min = request.args.get("desconto_min", default=0, type=int)
    preco_min = request.args.get("preco_min", default=0.0, type=float)
    preco_max = request.args.get("preco_max", default=0.0, type=float)
    busca = request.args.get("busca", default="", type=str)
    loja = request.args.get("loja", default="", type=str)
    plataforma = request.args.get("plataforma", default="Editoras", type=str)
    categoria = request.args.get("categoria", default="", type=str)
    ordem = request.args.get("ordem", default="desconto", type=str)
    apenas_disp = request.args.get("disponiveis") == "1"
    apenas_fav = request.args.get("favoritos") == "1"
    pagina = request.args.get("pagina", default=1, type=int)
    por_pagina = request.args.get("por_pagina", default=100, type=int)
    if pagina < 1:
        pagina = 1
        
    ofertas = listar_ofertas(desconto_min, preco_min, preco_max, busca, loja, categoria, apenas_disp, apenas_fav, ordem, pagina, por_pagina, plataforma)
    
    total_itens = ofertas[0]["total_geral"] if ofertas else 0
    total_paginas = (total_itens + por_pagina - 1) // por_pagina if total_itens > 0 else 1
    
    return render_template(
        "index.html",
        ofertas=ofertas,
        total_itens=total_itens,
        pagina=pagina,
        total_paginas=total_paginas,
        por_pagina=por_pagina,
        desconto_min=desconto_min,
        preco_min=preco_min if preco_min > 0 else "",
        preco_max= preco_max if preco_max > 0 else "",
        busca=busca,
        loja=loja,
        plataforma=plataforma,
        categoria=categoria,
        ordem=ordem,
        apenas_disp=apenas_disp,
        apenas_fav=apenas_fav,
        robo_rodando=robo_em_execucao,
        intervalo_auto=intervalo_auto_min
    )
    
@app.route("/varrer", methods=["POST"])
def acionar_varredura():
    modo = request.form.get("modo", "completo")
    enfileirar_ou_rodar(modo)
    return redirect(request.referrer or url_for("index"))

@app.route("/parar", methods=["POST"])
def parar_varredura():
    import scraper
    scraper.cancelar_varredura = True
    return redirect(request.referrer or url_for("index"))

@app.route("/favoritar/<int:produto_id>", methods=["POST"])
def favoritar(produto_id):
    novo_status = alternar_favorito(produto_id)
    return jsonify({"favorito": novo_status})

@app.route("/status_robo")
def status_robo():
    return jsonify({"rodando": robo_em_execucao})

@app.route("/historico/<int:produto_id>")
def historico_produto(produto_id):
    dados = buscar_historico_produto(produto_id)
    return jsonify (dados)

@app.route("/meta/<int:produto_id>", methods=["POST"])
def salvar_meta(produto_id):
    dados = request.get_json() or {}
    valor = float(dados.get("preco_alvo", 0.0))
    definir_preco_alvo(produto_id, valor)
    return jsonify({"preco_alvo": valor})

@app.route("/agendar", methods=["POST"])
def configurar_agendador():
    global intervalo_auto_min
    intervalo_auto_min = request.form.get("intervalo", default=0, type=int)
    salvar_config("intervalo_auto", intervalo_auto_min)
    if intervalo_auto_min > 0:
        agora = int(time.time())
        for _, chave_db, _, _ in REGRAS_AUTO:
            if obter_config(chave_db, 0) == 0:
                salvar_config(chave_db, agora)
    return redirect(request.referrer or url_for("index"))

@app.route("/adicionar_link", methods=["POST"])
def adicionar_link_wishlist():
    dados = request.get_json() or {}
    url = (dados.get("url") or "").strip()
    if not url.startswith("http"):
        return jsonify({"ok": False, "erro": "URL inválida"}), 400
    
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        INSERT INTO produtos (nome, url, loja, plataforma, categoria, favorito)
        VALUES ('⏳ Aguardando leitura...', %s, 'Outras', 'Editoras', 'Outros', TRUE)
        ON CONFLICT (url) DO UPDATE SET favorito = TRUE
        RETURNING id;
    """, (url,))
    
    conexao.commit()
    cursor.close()
    conexao.close()
    return jsonify({"ok": True})

@app.route("/editar_titulo/<int:produto_id>", methods=["POST"])
def editar_titulo(produto_id):
    dados = request.get.json() or {}
    novo_titulo = dados.get("titulo", "")
    nome_final = definir_titulo_editado(produto_id, novo_titulo)
    return jsonify({"ok": True, "nome": nome_final})

@app.route("/logs")
def ver_logs():
    return jsonify(listar_logs())

@app.route("/terminal_vivo")
def terminal_vivo():
    try:
        saida = subprocess.check_output(
            ["journalctl", "-u", "radarpromo", "-n", "120", "--no-pager", "-o", "cat"],
            text=True,
            stderr=subprocess.STDOUT
        )
        return jsonify({"ok": True, "log": saida})
    except Exception as e:
        return jsonify({"ok": False, "log": f"Erro ao ler journalctl: {e}"})
    
@app.route("/fila")
def status_fila():
    agora = int(time.time())
    proximos = []
    for modo_regra, chave_db, intervalo_seg, rotulo in REGRAS_AUTO:
        ult = obter_config(chave_db, 0)
        restante = max(0, (ult + intervalo_seg) - agora) if (intervalo_auto_min > 0 and ult > 0) else -1
        proximos.append({"rotulo": rotulo, "modo": modo_regra, "restante_seg": restante})
    return jsonify({
        "auto_ativo": intervalo_auto_min > 0,
        "rodando": robo_em_execucao,
        "modo_atual": modo_atual or "Nenhuma (Servidor Livre)",
        "fila": fila_varreduras,
        "agendamentos": proximos
    })

@app.route("/limpar_fila", methods=["POST"])
def limpar_fila():
    with lock_fila:
        fila_varreduras.clear()
    return jsonify({"ok": True})

@app.route("/ocultar/<int:produto_id>", methods=["POST"])
def ocultar_item(produto_id):
    ocultar_produto(produto_id)
    return jsonify({"ok": True})

@app.route("/manifest.json")
def pwa_manifest():
    icone_svg = "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='22' fill='%238257e5' /><text y='68' x='50' text-anchor='middle' font-size='55'>📚</text></svg>"
    return jsonify({
        "name": "Radar de Promoções HQs & Mangás",
        "short_name": "RadarPromo",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#09090b",
        "theme_color": "#13111c",
        "icons": [{"src": icone_svg, "sizes": "192x192 512x512", "type": "image/svg+xml", "purpose": "any maskable"}]
    })
    
@app.route("/sw.js")
def pwa_sw():
    return app.response_class("self.addEventListener('fetch', function(e) {});", mimetype="application/javascript")

if __name__ == "__main__":
    inicializar_banco()
    intervalo_auto_min = obter_config("intervalo_auto", 0)
    app.run(host="0.0.0.0", port=5000)