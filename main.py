from contextlib import asynccontextmanager
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from decimal import Decimal
import os
import hashlib
import uuid
import uvicorn


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não configurada.")
    
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/test_db")
DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None

    with engine.connect() as conn:
        user = conn.execute(
            text("SELECT * FROM usuarios WHERE session_id = :sid"),
            {"sid": session_id}
        ).fetchone()

    return user

def registrar_log(usuario_id, username, acao, detalhes=None):
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO logs_sistema (usuario_id, username, acao, detalhes)
            VALUES (:usuario_id, :username, :acao, :detalhes)
        """), {
            "usuario_id": usuario_id,
            "username": username,
            "acao": acao,
            "detalhes": detalhes
        })
        conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS logs_sistema (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER,
                username VARCHAR(50),
                acao VARCHAR(100) NOT NULL,
                detalhes TEXT,
                data_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(64) NOT NULL,
                perfil VARCHAR(20) DEFAULT 'user',
                session_id VARCHAR(36)
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS empresas (
                id SERIAL PRIMARY KEY,
                cnpj VARCHAR(20) NOT NULL,
                razao_social VARCHAR(100) NOT NULL,
                nome_fantasia VARCHAR(100),
                email VARCHAR(100),
                telefone VARCHAR(20),
                ativo INTEGER DEFAULT 1,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fornecedores (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                cnpj VARCHAR(20),
                telefone VARCHAR(20),
                email VARCHAR(100)
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS produtos (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100),
                quantidade NUMERIC(10,2) DEFAULT 0,
                preco NUMERIC(10,2),
                empresa_id INTEGER,
                fornecedor_id INTEGER,
                cor VARCHAR(50),
                tamanho VARCHAR(50)
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vendas (
                id SERIAL PRIMARY KEY,
                produto_id INTEGER REFERENCES produtos(id) ON DELETE CASCADE,
                quantidade NUMERIC(10,2) NOT NULL,
                preco_unitario NUMERIC(10,2) NOT NULL,
                total NUMERIC(10,2) NOT NULL,
                data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        conn.execute(text("""
            INSERT INTO usuarios (username, password, perfil)
            VALUES ('admin', :senha, 'admin')
            ON CONFLICT (username) DO NOTHING
        """), {"senha": hash_password("123456")})

        conn.commit()
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# --- ROTAS DE AUTENTICAÇÃO ---
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    with engine.connect() as conn:
        user = conn.execute(
            text("SELECT * FROM usuarios WHERE username = :username"),
            {"username": username}
        ).fetchone()

    if user and user.password == hash_password(password):
        session_id = str(uuid.uuid4())

        with engine.connect() as conn:
            conn.execute(
                text("UPDATE usuarios SET session_id = :sid WHERE id = :id"),
                {"sid": session_id, "id": user.id}
            )
            conn.commit()

        registrar_log(user.id, user.username, "LOGIN", "Usuário entrou no sistema")

        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        return response

    return templates.TemplateResponse(request, "login.html", {
        "error": "Credenciais Inválidas"
    })

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session_id")
    return response


# --- DASHBOARD ---
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    with engine.connect() as conn:
        total_produtos = conn.execute(
            text("SELECT COALESCE(SUM(quantidade), 0) FROM produtos")
        ).fetchone()[0]

        total_vendas = conn.execute(
            text("SELECT COUNT(*) FROM vendas")
        ).fetchone()[0]

        total_empresas = conn.execute(
            text("SELECT COUNT(*) FROM empresas")
        ).fetchone()[0]

        total_fornecedores = conn.execute(
            text("SELECT COUNT(*) FROM fornecedores")
        ).fetchone()[0]

        dados_grafico = conn.execute(text("""
            SELECT e.nome_fantasia, COALESCE(SUM(p.quantidade), 0) AS total
            FROM empresas e
            LEFT JOIN produtos p ON p.empresa_id = e.id
            GROUP BY e.id, e.nome_fantasia
            ORDER BY e.nome_fantasia
        """)).fetchall()

        labels = [d.nome_fantasia for d in dados_grafico]
        valores = [float(d.total) for d in dados_grafico]

        vendas_recentes = conn.execute(text("""
            SELECT v.data_venda, v.quantidade, v.total, p.nome, p.cor, p.tamanho
            FROM vendas v
            JOIN produtos p ON v.produto_id = p.id
            ORDER BY v.data_venda DESC
            LIMIT 5
        """)).fetchall()

   # labels = [d.nome_fantasia for d in dados_grafico]
   # valores = [float(d.total) for d in dados_grafico]

    return templates.TemplateResponse(request, "dashboard.html", {
        "user": user,
        "total_produtos": float(total_produtos or 0),
        "total_vendas": total_vendas,
        "total_empresas": total_empresas,
        "total_fornecedores": total_fornecedores,
        "labels": labels,
        "valores": valores,
        "vendas_recentes": vendas_recentes
    })


# --- PRODUTOS ---
@app.get("/produtos", response_class=HTMLResponse)
async def listar_produtos(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    with engine.connect() as conn:
        produtos = conn.execute(text("""
            SELECT p.*, e.nome_fantasia AS empresa_nome, f.nome AS fornecedor_nome
            FROM produtos p
            LEFT JOIN empresas e ON p.empresa_id = e.id
            LEFT JOIN fornecedores f ON p.fornecedor_id = f.id
            ORDER BY p.id DESC
        """)).fetchall()

        empresas = conn.execute(
            text("SELECT id, nome_fantasia FROM empresas ORDER BY nome_fantasia")
        ).fetchall()

        fornecedores = conn.execute(
            text("SELECT id, nome FROM fornecedores ORDER BY nome")
        ).fetchall()

    return templates.TemplateResponse(request, "produtos.html", {
        "user": user,
        "produtos": produtos,
        "empresas": empresas,
        "fornecedores": fornecedores
    })

@app.post("/produtos/novo")
async def novo_produto(
    request: Request,
    nome: str = Form(...),
    quantidade: float = Form(...),
    preco: float = Form(...),
    empresa_id: int = Form(...),
    fornecedor_id: int = Form(...),
    cor: str = Form(None),
    tamanho: str = Form(None),
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO produtos (nome, quantidade, preco, empresa_id, fornecedor_id, cor, tamanho)
            VALUES (:nome, :quantidade, :preco, :empresa_id, :fornecedor_id, :cor, :tamanho)
        """), {
            "nome": nome,
            "quantidade": quantidade,
            "preco": preco,
            "empresa_id": empresa_id,
            "fornecedor_id": fornecedor_id,
            "cor": cor,
            "tamanho": tamanho,
        })
        conn.commit()

    registrar_log(user.id, user.username, "CADASTRO_PRODUTO", f"Produto: {nome}, cor: {cor}, tamanho: {tamanho}")

    return RedirectResponse(url="/produtos", status_code=303)

@app.get("/produtos/novo")
async def exibir_formulario_cadastro(request: Request):
    with engine.connect() as conn:
        empresas = conn.execute(
            text("SELECT id, nome_fantasia FROM empresas ORDER BY nome_fantasia")
        ).fetchall()

        fornecedores = conn.execute(
            text("SELECT id, nome FROM fornecedores ORDER BY nome")
        ).fetchall()

    return templates.TemplateResponse(request, "cadastrar_produto.html", {
        "empresas": empresas,
        "fornecedores": fornecedores
    })

@app.get("/produtos/editar/{id}", response_class=HTMLResponse)
async def editar_produto_page(request: Request, id: int):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    with engine.connect() as conn:
        produto = conn.execute(
            text("SELECT * FROM produtos WHERE id = :id"),
            {"id": id}
        ).fetchone()

        empresas = conn.execute(
            text("SELECT id, nome_fantasia FROM empresas ORDER BY nome_fantasia")
        ).fetchall()

        fornecedores = conn.execute(
            text("SELECT id, nome FROM fornecedores ORDER BY nome")
        ).fetchall()

    return templates.TemplateResponse(request, "editar_produto.html", {
        "user": user,
        "produto": produto,
        "empresas": empresas,
        "fornecedores": fornecedores
    })

@app.post("/produtos/editar/{id}")
async def editar_produto(
    id: int,
    nome: str = Form(...),
    quantidade: float = Form(...),
    preco: float = Form(...),
    empresa_id: int = Form(...),
    fornecedor_id: int = Form(...),
    cor: str = Form(None),
    tamanho: str = Form(None),
):
    with engine.connect() as conn:
        conn.execute(text("""
            UPDATE produtos
            SET nome = :nome,
                quantidade = :quantidade,
                preco = :preco,
                empresa_id = :empresa_id,
                fornecedor_id = :fornecedor_id,
                cor = :cor,
                tamanho = :tamanho
            WHERE id = :id
        """), {
            "id": id,
            "nome": nome,
            "quantidade": quantidade,
            "preco": preco,
            "empresa_id": empresa_id,
            "fornecedor_id": fornecedor_id,
            "cor": cor,
            "tamanho": tamanho,
        })
        conn.commit()

    return RedirectResponse(url="/produtos", status_code=303)

@app.get("/produtos/deletar/{id}")
async def deletar_produto(id: int):
    with engine.connect() as conn:
        conn.execute(
            text("DELETE FROM produtos WHERE id = :id"),
            {"id": id}
        )
        conn.commit()

    return RedirectResponse(url="/produtos", status_code=303)


# --- GESTÃO DE USUÁRIOS ---
@app.get("/usuarios", response_class=HTMLResponse)
async def listar_usuarios(request: Request):
    user = get_current_user(request)
    if not user or user.perfil != "admin":
        return RedirectResponse(url="/login", status_code=303)

    with engine.connect() as conn:
        usuarios = conn.execute(
            text("SELECT id, username, perfil FROM usuarios ORDER BY id")
        ).fetchall()

    return templates.TemplateResponse(request, "usuarios.html", {
        "user": user,
        "usuarios": usuarios
    })

@app.post("/usuarios/novo")
async def novo_usuario(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    perfil: str = Form(...)
):
    user = get_current_user(request)
    if not user or user.perfil != "admin":
        return RedirectResponse(url="/", status_code=303)

    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO usuarios (username, password, perfil)
                VALUES (:username, :password, :perfil)
            """), {
                "username": username,
                "password": hash_password(password),
                "perfil": perfil
            })
            conn.commit()
    except IntegrityError:
        pass

    return RedirectResponse(url="/usuarios", status_code=303)

@app.get("/usuarios/deletar/{id}")
async def deletar_usuario(request: Request, id: int):
    user = get_current_user(request)
    if user and user.perfil == "admin" and user.id != id:
        with engine.connect() as conn:
            conn.execute(
                text("DELETE FROM usuarios WHERE id = :id"),
                {"id": id}
            )
            conn.commit()

    return RedirectResponse(url="/usuarios", status_code=303)

@app.post("/usuarios/editar/{user_id}")
async def editar_usuario(
    user_id: int,
    request: Request,
    username: str = Form(...),
    perfil: str = Form(...),
    password: str = Form(None)
):
    user = get_current_user(request)
    if not user or user.perfil != "admin":
        return RedirectResponse(url="/", status_code=303)

    with engine.connect() as conn:
        if password:
            conn.execute(text("""
                UPDATE usuarios
                SET username = :username,
                    perfil = :perfil,
                    password = :password
                WHERE id = :id
            """), {
                "username": username,
                "perfil": perfil,
                "password": hash_password(password),
                "id": user_id
            })
        else:
            conn.execute(text("""
                UPDATE usuarios
                SET username = :username,
                    perfil = :perfil
                WHERE id = :id
            """), {
                "username": username,
                "perfil": perfil,
                "id": user_id
            })
        conn.commit()

    return RedirectResponse(url="/usuarios", status_code=303)


# --- FORNECEDORES ---
@app.get("/fornecedores", response_class=HTMLResponse)
async def listar_fornecedores(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    with engine.connect() as conn:
        fornecedores = conn.execute(
            text("SELECT * FROM fornecedores ORDER BY nome")
        ).fetchall()

    return templates.TemplateResponse(request, "fornecedores.html", {
        "user": user,
        "fornecedores": fornecedores
    })

@app.post("/fornecedores/editar/{id}")
async def editar_fornecedor(
    id: int,
    nome: str = Form(...),
    cnpj: str = Form(None),
    telefone: str = Form(None),
    email: str = Form(None)
):
    with engine.connect() as conn:
        conn.execute(text("""
            UPDATE fornecedores
            SET nome = :nome,
                cnpj = :cnpj,
                telefone = :telefone,
                email = :email
            WHERE id = :id
        """), {
            "nome": nome,
            "cnpj": cnpj,
            "telefone": telefone,
            "email": email,
            "id": id
        })
        conn.commit()

    return RedirectResponse(url="/fornecedores", status_code=303)

@app.post("/fornecedores/novo")
async def novo_fornecedor(
    nome: str = Form(...),
    cnpj: str = Form(None),
    telefone: str = Form(None),
    email: str = Form(None),
):
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO fornecedores (nome, cnpj, telefone, email)
            VALUES (:nome, :cnpj, :telefone, :email)
        """), {
            "nome": nome,
            "cnpj": cnpj,
            "telefone": telefone,
            "email": email,
        })
        conn.commit()

    return RedirectResponse(url="/fornecedores", status_code=303)


# --- VENDAS ---
@app.get("/vendas", response_class=HTMLResponse)
async def pagina_vendas(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    with engine.connect() as conn:
        produtos = conn.execute(text("""
            SELECT id, nome, cor, tamanho, quantidade, preco
            FROM produtos
            WHERE quantidade > 0
            ORDER BY nome, cor, tamanho
        """)).fetchall()

        vendas = conn.execute(text("""
            SELECT v.*, p.nome, p.cor, p.tamanho
            FROM vendas v
            JOIN produtos p ON v.produto_id = p.id
            ORDER BY v.data_venda DESC
        """)).fetchall()

    return templates.TemplateResponse(request, "vendas.html", {
        "user": user,
        "produtos": produtos,
        "vendas": vendas
    })

@app.post("/vendas/nova")
async def registrar_venda(request: Request, produto_id: int = Form(...), qtd_venda: float = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    with engine.connect() as conn:
        prod = conn.execute(
            text("SELECT quantidade, preco FROM produtos WHERE id = :id"),
            {"id": produto_id}
        ).fetchone()

        if prod and float(prod.quantidade) >= qtd_venda:
            preco_unitario = float(prod.preco)
            total = qtd_venda * preco_unitario
            data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            conn.execute(text("""
                INSERT INTO vendas (produto_id, quantidade, preco_unitario, total, data_venda)
                VALUES (:produto_id, :quantidade, :preco_unitario, :total, :data_venda)
            """), {
                "produto_id": produto_id,
                "quantidade": qtd_venda,
                "preco_unitario": preco_unitario,
                "total": total,
                "data_venda": data_venda
            })

            conn.execute(text("""
                UPDATE produtos
                SET quantidade = quantidade - :qtd
                WHERE id = :id
            """), {
                "qtd": qtd_venda,
                "id": produto_id
            })

            conn.commit()

            registrar_log(
                user.id,
                user.username,
                "VENDA",
                f"Produto: {prod.nome}, cor: {prod.cor}, tamanho: {prod.tamanho}, qtd: {qtd_venda}, total: {total}"
            )

    return RedirectResponse(url="/vendas", status_code=303)


# --- EMPRESAS ---
@app.get("/empresas", response_class=HTMLResponse)
async def listar_empresas(request: Request):
    user = get_current_user(request)
    if not user or user.perfil != "admin":
        return RedirectResponse(url="/", status_code=303)

    with engine.connect() as conn:
        empresas = conn.execute(
            text("SELECT * FROM empresas ORDER BY nome_fantasia")
        ).fetchall()

    return templates.TemplateResponse(request, "empresas.html", {
        "user": user,
        "empresas": empresas
    })

@app.post("/empresas/nova")
async def nova_empresa(
    nome: str = Form(...),
    razao_social: str = Form(...),
    cnpj: str = Form(...),
    tel: str = Form(...),
    email: str = Form(...)
):
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO empresas (nome_fantasia, razao_social, cnpj, telefone, email)
            VALUES (:nome, :razao_social, :cnpj, :telefone, :email)
        """), {
            "nome": nome,
            "razao_social": razao_social,
            "cnpj": cnpj,
            "telefone": tel,
            "email": email
        })
        conn.commit()

    return RedirectResponse(url="/empresas", status_code=303)

@app.get("/empresas/deletar/{id}")
async def deletar_empresa(id: int):
    with engine.connect() as conn:
        conn.execute(
            text("DELETE FROM empresas WHERE id = :id"),
            {"id": id}
        )
        conn.commit()

    return RedirectResponse(url="/empresas", status_code=303)

@app.get("/empresas/editar/{id}", response_class=HTMLResponse)
async def editar_empresa_page(request: Request, id: int):
    user = get_current_user(request)
    if not user or user.perfil != "admin":
        return RedirectResponse(url="/", status_code=303)

    with engine.connect() as conn:
        empresa = conn.execute(
            text("SELECT * FROM empresas WHERE id = :id"),
            {"id": id}
        ).fetchone()

    if not empresa:
        return RedirectResponse(url="/empresas", status_code=303)

    return templates.TemplateResponse(request, "editar_empresa.html", {
        "user": user,
        "empresa": empresa
    })

@app.post("/empresas/editar/{id}")
async def atualizar_empresa(
    id: int,
    nome: str = Form(...),
    cnpj: str = Form(...),
    tel: str = Form(...),
    email: str = Form(...)
):
    with engine.connect() as conn:
        conn.execute(text("""
            UPDATE empresas
            SET nome_fantasia = :nome,
                cnpj = :cnpj,
                telefone = :telefone,
                email = :email
            WHERE id = :id
        """), {
            "nome": nome,
            "cnpj": cnpj,
            "telefone": tel,
            "email": email,
            "id": id
        })
        conn.commit()

    return RedirectResponse(url="/empresas", status_code=303)


# --- LOGS SOMENTE ADMIN ---
@app.get("/logs", response_class=HTMLResponse)
async def listar_logs(request: Request):
    user = get_current_user(request)
    if not user or user.perfil != "admin":
        return RedirectResponse(url="/", status_code=303)

    with engine.connect() as conn:
        logs = conn.execute(text("""
            SELECT *
            FROM logs_sistema
            ORDER BY data_evento DESC
            LIMIT 200
        """)).fetchall()

    return templates.TemplateResponse(request, "logs.html", {
        "user": user,
        "logs": logs
    })


# --- API ---
@app.get("/api/produtos/{empresa_id}")
async def api_listar_produtos(empresa_id: int):
    with engine.connect() as conn:
        produtos = conn.execute(text("""
            SELECT nome, quantidade, preco
            FROM produtos
            WHERE empresa_id = :empresa_id
            ORDER BY nome
        """), {"empresa_id": empresa_id}).fetchall()

    estoque = []
    for p in produtos:
        estoque.append({
            "nome": p.nome,
            "quantidade": float(p.quantidade) if isinstance(p.quantidade, Decimal) else p.quantidade,
            "preco": float(p.preco) if isinstance(p.preco, Decimal) else p.preco
        })

    return {"empresa_id": empresa_id, "estoque": estoque}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)