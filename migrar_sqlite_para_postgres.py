import sqlite3
import os
from sqlalchemy import create_engine, text

sqlite_conn = sqlite3.connect("estoque.db")
sqlite_conn.row_factory = sqlite3.Row

DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

engine = create_engine(DATABASE_URL)

with engine.connect() as pg:
    # CRIAR TABELAS PRIMEIRO
    pg.execute(text("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(64) NOT NULL,
            session_id VARCHAR(100),
            perfil VARCHAR(20) DEFAULT 'user'
        );
    """))

    pg.execute(text("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY,
            cnpj VARCHAR(20) NOT NULL,
            razao_social VARCHAR(100) NOT NULL,
            nome_fantasia VARCHAR(100),
            email VARCHAR(100),
            telefone VARCHAR(20),
            ativo INTEGER DEFAULT 1,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """))

    pg.execute(text("""
        CREATE TABLE IF NOT EXISTS fornecedores (
            id INTEGER PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            cnpj VARCHAR(20),
            telefone VARCHAR(20),
            email VARCHAR(100)
        );
    """))

    pg.execute(text("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY,
            nome VARCHAR(100),
            quantidade NUMERIC(10,2),
            preco NUMERIC(10,2),
            fornecedor_id INTEGER,
            empresa_id INTEGER
        );
    """))

    pg.execute(text("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY,
            produto_id INTEGER,
            quantidade NUMERIC(10,2),
            preco_unitario NUMERIC(10,2),
            total NUMERIC(10,2),
            data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """))

    pg.commit()

    # USUARIOS
    usuarios = sqlite_conn.execute("SELECT * FROM usuarios").fetchall()
    for u in usuarios:
        pg.execute(text("""
            INSERT INTO usuarios (id, username, password, session_id, perfil)
            VALUES (:id, :username, :password, :session_id, :perfil)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": u["id"],
            "username": u["username"],
            "password": u["password"],
            "session_id": u["session_id"],
            "perfil": u["perfil"]
        })

    # EMPRESAS
    empresas = sqlite_conn.execute("SELECT * FROM empresas").fetchall()
    for e in empresas:
        pg.execute(text("""
            INSERT INTO empresas (
                id, cnpj, razao_social, nome_fantasia, email, telefone, ativo, data_cadastro
            )
            VALUES (
                :id, :cnpj, :razao_social, :nome_fantasia, :email, :telefone, :ativo, :data_cadastro
            )
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": e["id"],
            "cnpj": e["cnpj"],
            "razao_social": e["razao_social"],
            "nome_fantasia": e["nome_fantasia"],
            "email": e["email"],
            "telefone": e["telefone"],
            "ativo": e["ativo"],
            "data_cadastro": e["data_cadastro"]
        })

    # FORNECEDORES
    fornecedores = sqlite_conn.execute("SELECT * FROM fornecedores").fetchall()
    for f in fornecedores:
        pg.execute(text("""
            INSERT INTO fornecedores (id, nome, cnpj, telefone, email)
            VALUES (:id, :nome, :cnpj, :telefone, :email)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": f["id"],
            "nome": f["nome"],
            "cnpj": f["cnpj"],
            "telefone": f["telefone"],
            "email": f["email"]
        })

    # PRODUTOS
    produtos = sqlite_conn.execute("SELECT * FROM produtos").fetchall()
    for p in produtos:
        pg.execute(text("""
            INSERT INTO produtos (id, nome, quantidade, preco, fornecedor_id, empresa_id)
            VALUES (:id, :nome, :quantidade, :preco, :fornecedor_id, :empresa_id)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": p["id"],
            "nome": p["nome"],
            "quantidade": p["quantidade"],
            "preco": p["preco"],
            "fornecedor_id": p["fornecedor_id"],
            "empresa_id": p["empresa_id"]
        })

    # VENDAS
    vendas = sqlite_conn.execute("SELECT * FROM vendas").fetchall()
    for v in vendas:
        pg.execute(text("""
            INSERT INTO vendas (id, produto_id, quantidade, preco_unitario, total, data_venda)
            VALUES (:id, :produto_id, :quantidade, :preco_unitario, :total, :data_venda)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": v["id"],
            "produto_id": v["produto_id"],
            "quantidade": v["quantidade"],
            "preco_unitario": v["preco_unitario"],
            "total": v["total"],
            "data_venda": v["data"]
        })

    pg.commit()

sqlite_conn.close()
print("Migração concluída com sucesso.")