import os
import httpx
from dotenv import load_dotenv

load_dotenv()

def enviar_alerta_ntfy(dados, desconto_minimo, eh_favorito=False):
    """Envia uma notificação Push para o celular via ntfy.sh."""
    topico = os.getenv("NTFY_TOPICO")
    
    if not topico:
        print("[Aviso] NTFY_TOPICO não configurado no arquivo .env.")
        return
    
    linha_recorde = "🔥 Menor preço histórico já visto!\n" if dados.get("eh_menor_historico") else ""
    
    mensagem = (
        f"Por: R$ {dados['preco_atual']:.2f} ({dados['desconto_pct']}% OFF)\n"
        f"Preço original: R$ {dados['preco_original']:.2f}\n" 
        f"{linha_recorde}"
        f"Status: {dados['status']}"
    )
    loja = dados.get("loja", "Panini")
    plataforma = dados.get("plataforma", "Editoras")
    origem = f"{plataforma} • {loja}" if plataforma != "Editoras" else loja
    botao_nome = plataforma if plataforma != "Editoras" else loja
    
    titulo_alerta = f"⭐ [WISHLIST | {origem}] {dados['nome']}" if eh_favorito else f"[{origem}] Oferta: {dados['nome']}"
    
    payload = {
        "topic": topico,
        "title": titulo_alerta,
        "message": mensagem,
        "priority": 5 if eh_favorito else 4,
        "tags": ["star", "books"] if eh_favorito else ["books", "money_with_wings"],
        "click": dados["url"],
        "actions": [
            {"action": "view", "label": f"Abrir na {botao_nome}", "url": dados["url"]}
        ]
    }
    
    if dados.get("imagem_url"):
        payload["attach"] = dados["imagem_url"]
    
    try:
        resposta = httpx.post("https://ntfy.sh", json=payload, timeout=15.0)
        if resposta.status_code == 200:
            print("   [Ntfy] Notificação enviada para o celular com sucesso!")
        else:
            print(f"   [Ntfy] Erro ao enviar notificação. Status {resposta.status_code}")
    except Exception as erro:
        print(f"   [Ntfy] Falha de conexão ao enviar alerta: {erro}")