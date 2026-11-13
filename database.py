import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from scraper import identificar_categoria

load_dotenv()

def conectar():
    """Abre e retorna uma conexão com o banco de dados PostgreSQL."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS")
    )
    
def inicializar_banco():
    """Cria as tabelas caso elas ainda não existam no banco."""
    conexao = conectar()
    cursor = conexao.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            url TEXT UNIQUE NOT NULL,
            alerta_enviado BOOLEAN DEFAULT FALSE,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS alerta_enviado BOOLEAN DEFAULT FALSE;
    """)
    
    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS loja VARCHAR(50) DEFAULT 'Panini';
    """)
    
    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS imagem_url TEXT;
    """)
    
    cursor.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
    
    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS categoria VARCHAR(50) DEFAULT 'Geral';
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_precos (
            id SERIAL PRIMARY KEY,
            produto_id INTEGER REFERENCES produtos(id) ON DELETE CASCADE,
            preco_original NUMERIC(10, 2) NOT NULL,
            preco_atual NUMERIC(10, 2) NOT NULL,
            desconto_pct INTEGER NOT NULL,
            status_estoque VARCHAR(50) NOT NULL,
            disponivel BOOLEAN NOT NULL,
            data_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );    
    """)
    
    cursor.execute("""
        UPDATE produtos SET categoria = 'Outros'
        WHERE categoria IN ('Panini Comics / Outros', 'Geral');
    """)
    
    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS favorito BOOLEAN DEFAULT FALSE;
    """)
    
    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS ultimo_alerta TIMESTAMP;
    """)
    
    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS plataforma VARCHAR(50) DEFAULT 'Editoras';
    """)
    
    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS preco_alvo NUMERIC(10, 2) DEFAULT 0.0;
    """)
    
    cursor.execute("UPDATE produtos SET categoria = 'Mangás' WHERE loja = 'NewPOP' AND categoria = 'Excluídos';")
    #cursor.execute("DELETE FROM produtos WHERE plataforma = 'Amazon' AND favorito = FALSE;")
    cursor.execute("""
        DELETE FROM produtos
        WHERE plataforma = 'Amazon'
            AND favorito = FALSE
            AND (
                categoria = 'Excluídos'
                OR nome ILIKE ANY (ARRAY['%Portuguese Edition%', '%Chinese Edition%', '%para colorir%', '%MPEG-7%', '%MPEG-2%', '%DivX%', '%Supremo Tribunal%', 'Supremo Tibunal'])
                OR (loja = 'Outras' AND nome ILIKE ANY (ARRAY['%outra%', '%outro%']))
            );
    """)
    
    cursor.execute("DELETE FROM historico_precos WHERE preco_atual <= 0;")
    
    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS titulo_editado TEXT;
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs_varredura (
            id SERIAL PRIMARY KEY,
            modo VARCHAR(50) NOT NULL,
            inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fim TIMESTAMP,
            total_lidos INTEGER DEFAULT 0,
            status VARCHAR(50) DEFAULT 'Em andamento'
        );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave VARCHAR(50) PRIMARY KEY,
            valor INTEGER DEFAULT 0
        );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hist_prod_data ON historico_precos(produto_id, data_consulta DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prod_plat_cat ON produtos(plataforma, categoria);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prod_fav ON produtos(favorito) WHERE favorito = TRUE;")
    
    conexao.commit()
    cursor.close()
    conexao.close()
    print("Banco de dados conectado, tabelas e índices verificados/criados com sucesso.")

def reclassificar_catalogo_legado():
    """Rotina de manutenção opcional para reclassificar editoras e categorias antigas."""
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome, url, loja, plataforma, categoria FROM produtos;")
    from scraper import identificar_editora
    alterados = 0
    for pid, pnome, purl, ploja, pplataforma, pcat in cursor.fetchall():
        nova_ed = identificar_editora(pnome, ploja) if pplataforma != "Editoras" else ploja
        contexto_cat = purl if pplataforma == "Editoras" else nova_ed.lower()
        nova_cat = "Excluídos" if pcat == "Excluídos" else identificar_categoria(pnome, contexto_cat, 10.0)
        if nova_ed != ploja or nova_cat != pcat:
            cursor.execute("UPDATE produtos SET loja = %s, categoria = %s WHERE id = %s;", (nova_ed, nova_cat, pid))
            alterados += 1
    conexao.commit()
    cursor.close()
    conexao.close()
    print(f"[Manutenção] Reclassificação concluída: {alterados} produtos atualizados.")
    
def salvar_leitura(dados, conexao=None):
    """
    Cadastra ou atualiza o produto na tabela 'produtos' e 
    insere um novo registro temporal em 'historico_precos'.
    """
    fechar_ao_final = conexao is None
    if fechar_ao_final:
        conexao = conectar()
    cursor = conexao.cursor()
    
    loja = dados.get("loja", "Panini")
    plataforma = dados.get("plataforma", "Editoras")
    imagem_url = dados.get("imagem_url", "")
    categoria = dados.get("categoria", "Outros")
    
    sql_produto = """
        INSERT INTO produtos (nome, url, loja, plataforma, imagem_url, categoria)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (url) DO UPDATE
        SET nome = EXCLUDED.nome,
            loja = EXCLUDED.loja,
            plataforma = EXCLUDED.plataforma,
            imagem_url = CASE
                WHEN EXCLUDED.imagem_url != '' THEN EXCLUDED.imagem_url
                ELSE produtos.imagem_url
            END,
            categoria = CASE
                WHEN produtos.categoria = 'Excluídos' THEN 'Excluídos'
                WHEN EXCLUDED.categoria IN ('Geral', 'Outros')
                    AND produtos.categoria NOT IN ('Geral', 'Outros')
                THEN produtos.categoria
                ELSE EXCLUDED.categoria
            END
        RETURNING id, (alerta_enviado AND ultimo_alerta IS NOT NULL AND ultimo_alerta > NOW() - INTERVAL '3 days'), favorito, COALESCE(preco_alvo, 0.0), titulo_editado, categoria;
    """
    cursor.execute(sql_produto, (dados["nome"], dados["url"], loja, plataforma, imagem_url, categoria))
    
    resultado_produto = cursor.fetchone()
    produto_id = resultado_produto[0]
    alerta_ja_enviado = resultado_produto[1]
    eh_favorito = resultado_produto[2]
    preco_alvo = float(resultado_produto[3])
    if resultado_produto[4]:
        dados["nome"] = resultado_produto[4]
    dados["categoria"] = resultado_produto[5]
    
    cursor.execute("""
        SELECT preco_atual, disponivel, status_estoque
        FROM historico_precos
        WHERE produto_id = %s
        ORDER BY data_consulta DESC
        LIMIT 1;
    """, (produto_id,))
    
    ultima_leitura = cursor.fetchone()
    
    cursor.execute("""
        SELECT MIN(preco_atual)
        FROM historico_precos
        WHERE produto_id = %s AND preco_atual > 0;
    """, (produto_id,))
    res_menor = cursor.fetchone()
    menor_historico = float(res_menor[0]) if (res_menor and res_menor[0] is not None) else float(dados["preco_atual"])
    
    if float(dados["preco_atual"]) <= 0.0 and ultima_leitura is not None:
        dados["preco_atual"] = float(ultima_leitura[0])
        if float(dados["preco_original"]) < dados["preco_atual"]:
            dados["preco_original"] = dados["preco_atual"]
        dados["desconto_pct"] = round(((dados["preco_original"] - dados["preco_atual"]) / dados["preco_original"]) * 100) if dados["preco_original"] > dados["preco_atual"] else 0
    
    mudou_estado = (
        ultima_leitura is None
        or float(ultima_leitura[0]) != float(dados["preco_atual"])
        or ultima_leitura[1] != dados["disponivel"]
        or ultima_leitura[2] != dados["status"]
    )
    
    if mudou_estado:
    
        sql_historico = """
            INSERT INTO historico_precos (
                produto_id, preco_original, preco_atual,
                desconto_pct, status_estoque, disponivel
            )
            VALUES (%s, %s, %s, %s, %s, %s);    
        """
        cursor.execute(sql_historico, (
            produto_id,
            dados["preco_original"],
            dados ["preco_atual"],
            dados["desconto_pct"],
            dados["status"],
            dados["disponivel"]
        ))
    
    conexao.commit()
    cursor.close()
    if fechar_ao_final:
        conexao.close()
    
    return produto_id, alerta_ja_enviado, eh_favorito, preco_alvo, menor_historico

def atualizar_status_alerta(produto_id, status_booleano):
    """Liga (True) ou desliga (False) a trava de notificação de um produto."""
    conexao = conectar()
    cursor = conexao.cursor()
    
    cursor.execute("""
        UPDATE produtos
        SET alerta_enviado = %s,
            ultimo_alerta = CASE WHEN %s = TRUE THEN CURRENT_TIMESTAMP ELSE ultimo_alerta END
        WHERE id = %s;
    """, (status_booleano, status_booleano, produto_id))
    
    
    conexao.commit()
    cursor.close()
    conexao.close()
    
def listar_ofertas(desconto_min=0, preco_min=0.0, preco_max=0.0, busca="", loja="", categoria="", apenas_disponiveis=False, apenas_favoritos=False, ordem="desconto", pagina=1, por_pagina=48, plataforma="Editoras"):
    """
    Busca todos os produtos com sua leitura mais recente,
    aplicando filtros de desconto, nome e estoque.
    """
    conexao = conectar()
    cursor = conexao.cursor(cursor_factory=RealDictCursor)
    
    sql = """
        SELECT COUNT(*) OVER() AS total_geral, * FROM (
            SELECT DISTINCT ON (p.id)
                p.id, COALESCE(NULLIF(p.titulo_editado, ''), p.nome) AS nome, p.nome AS nome_original, COALESCE(p.titulo_editado, '') AS titulo_editado, p.url, p.loja, p.plataforma, p.imagem_url, p.categoria, p.favorito,
                COALESCE(p.preco_alvo, 0.0) AS preco_alvo,
                h.preco_original, h.preco_atual, h.desconto_pct,
                h.status_estoque, h.disponivel, h.data_consulta,
                COALESCE(MIN(h.preco_atual) FILTER (WHERE h.preco_atual > 0) OVER (PARTITION BY p.id), h.preco_atual) AS menor_preco
            FROM produtos p
            JOIN historico_precos h ON p.id = h.produto_id
            ORDER BY p.id, h.data_consulta DESC
        ) AS ultimas_leituras
        WHERE desconto_pct >= %s
          AND unaccent(nome) ILIKE unaccent(%s)
    """
    parametros = [desconto_min, f"%{busca}%"]
    
    if preco_min > 0:
        sql += " AND preco_atual >= %s"
        parametros.append(preco_min)
    
    if preco_max > 0:
        sql += " AND preco_atual <= %s"
        parametros.append(preco_max)
    
    if loja:
        sql += " AND loja = %s"
        parametros.append(loja)
    
    if plataforma == "Wishlist":
        sql += " AND favorito = TRUE"
    elif plataforma and plataforma != "Todas":
        sql += " AND plataforma = %s"
        parametros.append(plataforma)
    
    if categoria:
        sql += " AND categoria = %s"
        parametros.append(categoria)
    else:
        sql += " AND categoria != 'Excluídos'"
        
    if apenas_disponiveis:
        sql += " AND disponivel = TRUE"
        
    if apenas_favoritos:sql += " AND favorito = TRUE"
        
        #adicionar "LIMIT 200" depois de DESC e ASC para agilizar o site
    if ordem == "preco_menor":
        sql += " ORDER BY preco_atual ASC, disponivel DESC, desconto_pct DESC"
    elif ordem == "nome":
        sql += r""" 
            ORDER BY REGEXP_REPLACE(
                REGEXP_REPLACE(unaccent(LOWER(nome)), '([0-9]+)', '0000000000\1', 'g'),
                '0+([0-9]{10})', '\1', 'g'
                ) ASC, nome ASC
            """
    elif ordem == "recentes":
        sql += " ORDER BY data_consulta DESC, disponivel DESC, desconto_pct DESC"
    else:
        sql += " ORDER BY desconto_pct DESC, disponivel DESC, preco_atual ASC"
        
    offset = (pagina - 1) * por_pagina
    sql += " LIMIT %s OFFSET %s;"
    parametros.extend([por_pagina, offset])

    cursor.execute(sql,tuple(parametros))
    produtos = cursor.fetchall()
    
    cursor.close()
    conexao.close()
    return produtos

def alternar_favorito(produto_id):
    """Inverte o status de favorito (True <-> False) de um produto."""
    conexao = conectar()
    cursor = conexao.cursor()
    
    cursor.execute("""
        UPDATE produtos
        SET favorito = NOT COALESCE(favorito, FALSE)
        WHERE id = %s
        RETURNING favorito;
    """, (produto_id,))
    
    novo_status = cursor.fetchone()[0]
    conexao.commit()
    cursor.close()
    conexao.close()
    return novo_status

def listar_urls_favoritos():
    """Retorna a lista de URLs de todos os produtos marcados na Wishlist."""
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT url FROM produtos WHERE favorito = TRUE;")
    urls = [linha[0] for linha in cursor.fetchall()]
    cursor.close()
    conexao.close()
    return urls

def buscar_historico_produto(produto_id):
    """Retorna todas as leituras de preço de um produto em ordem cronológica."""
    conexao = conectar()
    cursor = conexao.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT
            TO_CHAR(data_consulta, 'DD/MM/YYYY HH24:MI') AS data_formatada,
            FLOAT8(preco_original) AS preco_original,
            FLOAT8(preco_atual) AS preco_atual,
            desconto_pct,
            status_estoque,
            disponivel
        FROM historico_precos
        WHERE produto_id = %s
        ORDER BY data_consulta ASC;
    """, (produto_id,))
    historico = cursor.fetchall()
    cursor.close()
    conexao.close()
    return historico

def definir_preco_alvo(produto_id, valor_alvo):
    """Define uma meta de preço (R$) para o produto e já o coloca na Wishlist."""
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        UPDATE produtos
        SET preco_alvo = %s,
            favorito = CASE WHEN %s > 0 THEN TRUE ELSE favorito END
        WHERE id = %s;
    """, (valor_alvo, valor_alvo, produto_id))
    conexao.commit()
    cursor.close()
    conexao.close()
    
def definir_titulo_editado(produto_id, novo_titulo):
    """Salva um título personalizado para a oferta (ou limpa se vier vazio)."""
    conexao = conectar()
    cursor = conexao.cursor()
    titulo_limpo = novo_titulo.strip() if novo_titulo else None
    cursor.execute("""
        UPDATE produtos
        SET titulo_editado = %s
        WHERE id = %s
        RETURNING COALESCE(NULLIF(titulo_editado, ''), nome);
    """, (titulo_limpo, produto_id))
    nome_final = cursor.fetchone()[0]
    conexao.commit()
    cursor.close()
    conexao.close()
    return nome_final

def registrar_inicio_log(modo):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO logs_varredura (modo, status) VALUES (%s, '🔄 Em andamento') RETURNING id;", (modo,))
    log_id = cursor.fetchone()[0]
    conexao.commit()
    cursor.close()
    conexao.close()
    return log_id

def finalizar_log(log_id, total_lidos, status):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        UPDATE logs_varredura
        SET fim = CURRENT_TIMESTAMP, total_lidos = %s, status = %s
        WHERE id = %s;
    """, (total_lidos, status, log_id))
    conexao.commit()
    cursor.close()
    conexao.close()
    
def listar_logs(limite=50):
    conexao = conectar()
    cursor = conexao.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT
            id, modo, total_lidos, status,
            TO_CHAR(inicio, 'DD/MM/YYYY HH24:MI:SS') AS inicio_fmt,
            COALESCE(TO_CHAR(fim, 'HH24:MI:SS'), '--:--:--') AS fim_fmt,
            COALESCE(EXTRACT(EPOCH FROM (COALESCE(fim, CURRENT_TIMESTAMP) - inicio))::INTEGER, 0) AS duracao_seg
        FROM logs_varredura
        ORDER BY id DESC
        LIMIT %s;
    """, (limite,))
    logs = cursor.fetchall()
    cursor.close()
    conexao.close()
    return logs

def obter_config(chave, padrao=0):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT valor FROM configuracoes WHERE chave = %s;", (chave,))
    linha = cursor.fetchone()
    cursor.close()
    conexao.close()
    return linha[0] if linha else 0

def salvar_config(chave, valor):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        INSERT INTO configuracoes (chave, valor) VALUES (%s, %s)
        ON CONFLICT (chave) DO UPDATE SET valor = EXCLUDED.valor;
    """, (chave, int(valor)))
    conexao.commit()
    cursor.close()
    conexao.close()
    
def ocultar_produto(produto_id):
    """Move um produto indesejado para a categoria Excluídos."""
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        UPDATE produtos
        SET categoria = 'Excluídos', favorito = FALSE
        WHERE id = %s;
    """, (produto_id,))
    conexao.commit()
    cursor.close()
    conexao.close()