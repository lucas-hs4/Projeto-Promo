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
    
    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS menor_preco NUMERIC(10, 2) DEFAULT 0.0;
    """)
    
    cursor.execute("""
        UPDATE produtos p
        SET menor_preco = sub.min_p
        FROM (
            SELECT produto_id, MIN(preco_atual) AS min_p
            FROM historico_precos
            WHERE preco_atual > 0
            GROUP BY produto_id
        ) sub
        WHERE p.id = sub.produto_id AND (p.menor_preco IS NULL OR p.menor_preco <= 0);
    """)
    
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
    
def salvar_leitura(dados, conexao=None, comitar=True):
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
        RETURNING id, (alerta_enviado AND ultimo_alerta IS NOT NULL AND ultimo_alerta > NOW() - INTERVAL '3 days'), favorito, COALESCE(preco_alvo, 0.0), titulo_editado, categoria, COALESCE(menor_preco, 0.0);
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
    menor_salvo = float(resultado_produto[6])
    
    cursor.execute("""
        SELECT preco_atual, disponivel, status_estoque
        FROM historico_precos
        WHERE produto_id = %s
        ORDER BY data_consulta DESC
        LIMIT 1;
    """, (produto_id,))
    
    ultima_leitura = cursor.fetchone()
    
    
    if float(dados["preco_atual"]) <= 0.0 and ultima_leitura is not None:
        dados["preco_atual"] = float(ultima_leitura[0])
        if float(dados["preco_original"]) < dados["preco_atual"]:
            dados["preco_original"] = dados["preco_atual"]
        dados["desconto_pct"] = round(((dados["preco_original"] - dados["preco_atual"]) / dados["preco_original"]) * 100) if dados["preco_original"] > dados["preco_atual"] else 0
    
    preco_lido = float(dados["preco_atual"])
    if preco_lido > 0 and (menor_salvo <= 0 or preco_lido < menor_salvo):
        menor_historico = preco_lido
        cursor.execute("UPDATE produtos SET menor_preco = %s WHERE id = %s;", (preco_lido, produto_id))
    else:
        menor_historico = menor_salvo if menor_salvo > 0 else preco_lido
    
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
    
    if fechar_ao_final or comitar:
        conexao.commit()
    cursor.close()
    if fechar_ao_final:
        conexao.close()
    
    return produto_id, alerta_ja_enviado, eh_favorito, preco_alvo, menor_historico

def atualizar_status_alerta(produto_id, status_booleano, conexao=None, comitar=True):
    """Liga (True) ou desliga (False) a trava de notificação de um produto."""
    fechar_ao_final = conexao is None
    if fechar_ao_final:
        conexao = conectar()
    cursor = conexao.cursor()
    
    cursor.execute("""
        UPDATE produtos
        SET alerta_enviado = %s,
            ultimo_alerta = CASE WHEN %s = TRUE THEN CURRENT_TIMESTAMP ELSE ultimo_alerta END
        WHERE id = %s;
    """, (status_booleano, status_booleano, produto_id))
    
    if fechar_ao_final or comitar:
        conexao.commit()
    cursor.close()
    if fechar_ao_final:
        conexao.close()
    
def listar_ofertas(desconto_min=0, preco_min=0.0, preco_max=0.0, busca="", loja="", categoria="", apenas_disp=False, apenas_favoritos=False, ordem="desconto", pagina=1, por_pagina=48, plataforma="Editoras"):
    """
    Busca todos os produtos com sua leitura mais recente,
    aplicando filtros de desconto, nome e estoque.
    """
    conexao = conectar()
    cursor = conexao.cursor(cursor_factory=RealDictCursor)
    
    filtros_prod = ["unaccent(COALESCE(NULLIF(p.titulo_editado, ''), p.nome)) ILIKE unaccent(%s)"]
    parametros = [f"%{busca}%"]
    
    if loja:
        filtros_prod.append("p.loja = %s")
        parametros.append(loja)
    
    if plataforma == "Wishlist":
        filtros_prod.append("p.favorito = TRUE")
    elif plataforma and plataforma != "Todas":
        filtros_prod.append("p.plataforma = %s")
        parametros.append(plataforma)
    
    if categoria:
        filtros_prod.append("p.categoria = %s")
        parametros.append(categoria)
    else:
        filtros_prod.append("p.categoria != 'Excluídos'")
    
    if apenas_favoritos:
        filtros_prod.append("p.favorito = TRUE")
        
    where_prod = " AND ".join(filtros_prod)
    
    sql = f"""
        SELECT COUNT(*) OVER() AS total_geral, * FROM (
            SELECT DISTINCT ON (p.id)
                p.id, COALESCE(NULLIF(p.titulo_editado, ''), p.nome) AS nome, p.nome AS nome_original, COALESCE(p.titulo_editado, '') AS titulo_editado, p.url, p.loja, p.plataforma, p.imagem_url, p.categoria, p.favorito,
                COALESCE(p.preco_alvo, 0.0) AS preco_alvo,
                h.preco_original, h.preco_atual, h.desconto_pct,
                h.status_estoque, h.disponivel, h.data_consulta,
                CASE WHEN p.menor_preco > 0 THEN p.menor_preco ELSE h.preco_atual END AS menor_preco
            FROM produtos p
            JOIN historico_precos h ON p.id = h.produto_id
            WHERE {where_prod}
            ORDER BY p.id, h.data_consulta DESC
        ) AS ultimas_leituras
        WHERE desconto_pct >= %s
    """
    parametros.append(desconto_min)
    
    if preco_min > 0:
        sql += " AND preco_atual >= %s"
        parametros.append(preco_min)
    
    if preco_max > 0:
        sql += " AND preco_atual <= %s"
        parametros.append(preco_max)
        
    if apenas_disp:
        sql += " AND disponivel = TRUE"
        
        
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
    return linha[0] if linha else padrao

def obter_configs():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT chave, valor FROM configuracoes;")
    configs = dict(cursor.fetchall())
    cursor.close()
    conexao.close()
    return configs

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