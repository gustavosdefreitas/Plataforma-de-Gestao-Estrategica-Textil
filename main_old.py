from fastapi import FastAPI, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from decimal import Decimal
import os
import hashlib
import uuid
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- POSTGRES RENDER ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pgtextil_user:pGKStz5lUcirN9iF8pBPiF275w2FDuSX@dpg-d77t0tvkijhs73frr13g-a/pgtextil").replace("postgres://", "postgresql://")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Auxiliar para verificar login em todas as rotas
def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None
    with engine.connect() as conn:
        user = conn.execute(text("SELECT * FROM usuarios WHERE session_id = :sid"), {"sid": session_id}).fetchone()
        conn.close()
    return user

# ✅ CRIAR TODAS TABELAS no startup
@app.lifespan("startup")
async def startup():
    with engine.connect() as conn:
        conn.execute(text("""
        -- USUARIOS
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE,
            password VARCHAR(64),
            perfil VARCHAR(20) DEFAULT 'user',
            session_id VARCHAR(36)
        );
        
        -- PRODUTOS
        CREATE TABLE IF NOT EXISTS produtos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100),
            quantidade NUMERIC(10,2),
            preco NUMERIC(10,2),
            empresa_id INTEGER,
            fornecedor_id INTEGER
        );
        
        -- VENDAS
        CREATE TABLE IF NOT EXISTS vendas (
            id SERIAL PRIMARY KEY,
            produto_id INTEGER,
            quantidade NUMERIC(10,2),
            preco_unitario NUMERIC(10,2),
            total NUMERIC(10,2),
            data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- EMPRESAS
        CREATE TABLE IF NOT EXISTS empresas (
            id SERIAL PRIMARY KEY,
            nome_fantasia VARCHAR(100),
            razao_social VARCHAR(100),
            cnpj VARCHAR(20),
            telefone VARCHAR(20),
            email VARCHAR(100)
        );
        
        -- FORNECEDORES
        CREATE TABLE IF NOT EXISTS fornecedores (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100),
            cnpj VARCHAR(20),
            telefone VARCHAR(20),
            email VARCHAR(100)
        );
        """))
        
        # USUARIO ADMIN PADRÃO
        conn.execute(text("""
            INSERT INTO usuarios (username, password, perfil) 
            VALUES ('admin', :hash, 'admin')
            ON CONFLICT (username) DO NOTHING
        """), {"hash": hash_password("123456")})
        
        conn.commit()

# --- ROTAS DE AUTENTICAÇÃO ---
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    with engine.connect() as conn:  # ← PostgreSQL
        user = conn.execute(text("SELECT * FROM usuarios WHERE username = :user"), 
                           {"user": username}).fetchone()
    
    if user and user.password == hash_password(password):  # ← user.password
        session_id = str(uuid.uuid4())
        
        with engine.connect() as conn:
            conn.execute(text("UPDATE usuarios SET session_id = :sid WHERE id = :id"), 
                        {"sid": session_id, "id": user.id})
            conn.commit()
        
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        return response
    
    return templates.TemplateResponse("login.html", {"request": request, "error": "Credenciais Inválidas"})

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session_id")
    return response

# --- DASHBOARD ---
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = get_current_user(request)
    if not user: return RedirectResponse(url="/login", status_code=303)

    with engine.connect() as conn:
        total_produtos = conn.execute(text("SELECT COALESCE(SUM(quantidade), 0) FROM produtos")).fetchone()[0]
        total_vendas = conn.execute(text("SELECT COUNT(*) FROM vendas")).fetchone()[0]
        total_empresas = conn.execute(text("SELECT COUNT(*) FROM empresas")).fetchone()[0]
        total_fornecedores = conn.execute(text("SELECT COUNT(*) FROM fornecedores")).fetchone()[0]
        conn.close()
    
    # ANÁLISE DE DADOS: Busca quantidade de produtos por empresa para o GRÁFICO
    # (Assume que você já vinculou a coluna empresa_id em produtos)
    dados_grafico = conn.execute("""
        SELECT e.nome_fantasia, COALESCE(SUM(p.quantidade), 0) AS total
        FROM produtos p
        JOIN empresas e ON p.empresa_id = e.id
        GROUP BY e.id, e.nome_fantasia
    """).fetchall()

    dados_fornecedores = conn.execute("""
        SELECT f.nome, COUNT(p.id)
        FROM produtos p
        JOIN fornecedores f ON p.fornecedor_id = f.id
        GROUP BY f.nome
    """).fetchall()

    vendas_recentes = conn.execute("""
        SELECT v.*, p.nome FROM vendas v 
        JOIN produtos p ON v.produto_id = p.id 
        ORDER BY v.data_venda DESC 
        LIMIT 5
    """).fetchall()
    conn.close()

    # Prepara listas para o JavaScript ler
    labels = [d.nome_fantasia for d in dados_grafico]
    valores = [float(d.total) for d in dados_grafico]

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "total_produtos": total_produtos,
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
    if not user: return RedirectResponse(url="/login", status_code=303)
    
    conn = get_db()
    
    # 1. Busca produtos com os nomes de Empresa e Fornecedor para a TABELA
    produtos = conn.execute("""
        SELECT p.*, e.nome_fantasia AS empresa_nome, f.nome AS fornecedor_nome
        FROM produtos p
        LEFT JOIN empresas e ON p.empresa_id = e.id
        LEFT JOIN fornecedores f ON p.fornecedor_id = f.id
    """).fetchall()
    
    # 2. Busca empresas para o SELECT do Modal
    empresas = conn.execute("SELECT id, nome_fantasia FROM empresas").fetchall()
    
    # 3. ADICIONE ESTA LINHA: Busca fornecedores para o SELECT do Modal
    fornecedores = conn.execute("SELECT id, nome FROM fornecedores").fetchall()
    
    conn.close()
    
    return templates.TemplateResponse("produtos.html", {
        "request": request, 
        "user": user, 
        "produtos": produtos, 
        "empresas": empresas,
        "fornecedores": fornecedores  # NÃO ESQUEÇA DE ADICIONAR AQUI TAMBÉM
    })

#NOVO PRODUTO
@app.post("/produtos/novo")
async def novo_produto(
    nome: str = Form(...), 
    quantidade: float = Form(...), # Mudado para float para aceitar metros/decimais
    preco: float = Form(...), 
    empresa_id: int = Form(...),
    fornecedor_id: int = Form(...) # Adicionado conforme o novo formulário
):
    conn = get_db()
    # Adicionamos o campo fornecedor_id na query SQL também
    conn.execute(text("""
        INSERT INTO produtos (nome, quantidade, preco, empresa_id, fornecedor_id)
        VALUES (:nome, :quantidade, :preco, :empresa_id, :fornecedor_id)
    """), {
        "nome": nome,
        "quantidade": quantidade,
        "preco": preco,
        "empresa_id": empresa_id,
        "fornecedor_id": fornecedor_id
    })
    conn.commit()
    conn.close()
    return RedirectResponse(url="/produtos", status_code=303)

@app.get("/produtos/novo")
async def exibir_formulario_cadastro(request: Request):
    conn = get_db()
    # Buscamos os dados para preencher os menus de seleção (Dropdowns)
    empresas = conn.execute("SELECT id, nome_fantasia FROM empresas").fetchall()
    fornecedores = conn.execute("SELECT id, nome FROM fornecedores").fetchall()
    conn.close()
    
    return templates.TemplateResponse("cadastrar_produto.html", {
        "request": request,
        "empresas": empresas,
        "fornecedores": fornecedores
    })

#EDITAR PRODUTO
@app.get("/produtos/editar/{id}", response_class=HTMLResponse)
async def editar_produto_page(request: Request, id: int):
    user = get_current_user(request)
    if not user: return RedirectResponse(url="/login", status_code=303)
    
    conn = get_db()
    # Busca o produto
    produto = conn.execute(text("SELECT * FROM produtos WHERE id = :id"), {"id": id}).fetchone()
    # Busca todas as empresas para o SELECT
    empresas = conn.execute("SELECT id, nome_fantasia FROM empresas").fetchall()
    # Busca todos os fornecedores para o SELECT
    fornecedores = conn.execute("SELECT id, nome FROM fornecedores").fetchall()
    conn.close()
    
    return templates.TemplateResponse("editar_produto.html", {
       "request": request, "user": user, "produto": produto,
        "empresas": empresas, "fornecedores": fornecedores
    })

@app.post("/editar_produto/{id}")
async def atualizar_produto(
    id: int,
    nome: str = Form(...), 
    quantidade: float = Form(...), # Mudamos de int para float aqui!
    preco: float = Form(...), 
    empresa_id: int = Form(...),
    fornecedor_id: int = Form(...) # Adicionamos o fornecedor
):
    conn = get_db() # Usando o seu nome de função correto
    conn.execute("""
        UPDATE produtos 
        SET nome = ?, quantidade = ?, preco = ?, empresa_id = ?, fornecedor_id = ? 
        WHERE id = ?
    """, (nome, quantidade, preco, empresa_id, fornecedor_id, id))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/produtos", status_code=303)

#DELETAR PRODUTO
@app.get("/produtos/deletar/{id}")
async def deletar_produto(id: int):
    conn = get_db()
    conn.execute("DELETE FROM produtos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/produtos", status_code=303)

# --- GESTÃO DE USUÁRIOS ---

@app.get("/usuarios", response_class=HTMLResponse)
async def listar_usuarios(request: Request):
    user = get_current_user(request)
    # Proteção: Se não estiver logado ou não for admin, volta para o dashboard ou login
    if not user: return RedirectResponse(url="/login", status_code=303)
    
    conn = get_db()
    # Pega os usuários e converte para uma lista de dicionários real
    cursor = conn.execute("SELECT id, username, perfil FROM usuarios")
    lista_limpa = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return templates.TemplateResponse("usuarios.html", {
    "request": request,
    "user": dict(user),
    "usuarios": lista_limpa
    })

@app.post("/usuarios/novo")
async def novo_usuario(request: Request, username: str = Form(...), password: str = Form(...), perfil: str = Form(...)):
    user = get_current_user(request)
    if not user or user['perfil'] != 'admin':
        return RedirectResponse(url="/", status_code=303)

    conn = get_db()
    try:
        conn.execute("INSERT INTO usuarios (username, password, perfil) VALUES (?, ?, ?)",
                     (username, hash_password(password), perfil))
        conn.commit()
    except IntegrityError:
        # Caso o nome de utilizador já exista
        pass 
    finally:
        conn.close()
    
    return RedirectResponse(url="/usuarios", status_code=303)

@app.get("/usuarios/deletar/{id}")
async def deletar_usuario(request: Request, id: int):
    user = get_current_user(request)
    # Impede que um admin se apague a si próprio (importante!)
    if user and user['perfil'] == 'admin' and user['id'] != id:
        conn = get_db()
        conn.execute("DELETE FROM usuarios WHERE id = ?", (id,))
        conn.commit()
        conn.close()
    
    return RedirectResponse(url="/usuarios", status_code=303)

# ROTA PARA EXIBIR O FORMULÁRIO DE EDIÇÃO DE USUÁRIO
@app.post("/usuarios/editar/{user_id}")
async def editar_usuario(user_id: int, request: Request, username: str = Form(...), perfil: str = Form(...), password: str = Form(None)):
    user = get_current_user(request)
    if not user or user['perfil'] != 'admin':
        return RedirectResponse(url="/", status_code=303)

    conn = get_db()
    # Se a senha for fornecida, atualiza ela também
    if password:
        conn.execute("""
            UPDATE usuarios 
            SET username = ?, perfil = ?, password = ? 
            WHERE id = ?
        """, (username, perfil, hash_password(password), user_id))
    else:
        conn.execute("""
            UPDATE usuarios 
            SET username = ?, perfil = ? 
            WHERE id = ?
        """, (username, perfil, user_id))
    
    conn.commit()
    conn.close()
    
    return RedirectResponse(url="/usuarios", status_code=303)

#FORNECEDORES 
@app.get("/fornecedores", response_class=HTMLResponse)
async def listar_fornecedores(request: Request):
    user = get_current_user(request)
    if not user: return RedirectResponse(url="/login", status_code=303)
    
    conn = get_db()
    fornecedores = conn.execute("SELECT * FROM fornecedores").fetchall()
    conn.close()
    return templates.TemplateResponse("fornecedores.html", {"request": request, "user": user, "fornecedores": fornecedores})

#EDITAR FORNECEDOR
@app.post("/fornecedores/editar/{id}")
async def editar_fornecedor(
    id: int, 
    nome: str = Form(...), 
    cnpj: str = Form(None), 
    telefone: str = Form(None), 
    email: str = Form(None)
):
    conn = get_db()
    conn.execute("""
        UPDATE fornecedores 
        SET nome = ?, cnpj = ?, telefone = ?, email = ? 
        WHERE id = ?
    """, (nome, cnpj, telefone, email, id))
    
    conn.commit()
    conn.close()
    
    return RedirectResponse(url="/fornecedores", status_code=303)

# ROTA PARA ABRIR A PÁGINA DE VENDAS (O que o botão do menu chama)
@app.get("/vendas", response_class=HTMLResponse)
async def pagina_vendas(request: Request):
    user = get_current_user(request)
    if not user: 
        return RedirectResponse(url="/login", status_code=303)
    
    conn = get_db()
    # Pega produtos que tenham estoque para vender
    produtos = conn.execute("SELECT * FROM produtos WHERE quantidade > 0").fetchall()
    # Pega o histórico de vendas unindo com a tabela de produtos para saber o nome
    vendas = conn.execute("""
        SELECT v.*, p.nome 
        FROM vendas v 
        JOIN produtos p ON v.produto_id = p.id 
        ORDER BY v.data DESC
    """).fetchall()
    conn.close()
    
    return templates.TemplateResponse("vendas.html", {
        "request": request, 
        "user": user, 
        "produtos": produtos, 
        "vendas": vendas
    })

# ROTA PARA PROCESSAR O FORMULÁRIO (O que o botão "Finalizar Venda" chama)
@app.post("/vendas/nova")
async def registrar_venda(produto_id: int = Form(...), qtd_venda: float = Form(...)):
    with engine.connect() as conn:
        prod = conn.execute(text("SELECT quantidade, preco FROM produtos WHERE id = :id"), {"id": produto_id}).fetchone()
        
        if prod and prod[0] >= qtd_venda:  # PostgreSQL usa índices
            total = qtd_venda * prod[1]
            data_venda = datetime.now()
            conn.execute(text("""
                INSERT INTO vendas (produto_id, quantidade, preco_unitario, total, data_venda) 
                VALUES (:pid, :qtd, :preco, :total, :data)
            """), {"pid": produto_id, "qtd": qtd_venda, "preco": prod[1], "total": total, "data": data_venda})
            
            conn.execute(text("UPDATE produtos SET quantidade = quantidade - :qtd WHERE id = :id"), 
                        {"qtd": qtd_venda, "id": produto_id})
            conn.commit()
    return RedirectResponse(url="/vendas", status_code=303)

#GERENCIAR EMPRESAS
@app.get("/empresas", response_class=HTMLResponse)
async def listar_empresas(request: Request):
    user = get_current_user(request)
    if not user or user['perfil'] != 'admin':
        return RedirectResponse(url="/", status_code=303)
    
    conn = get_db()
    empresas = conn.execute("SELECT * FROM empresas ORDER BY nome_fantasia").fetchall()
    conn.close()
    return templates.TemplateResponse("empresas.html", {"request": request, "user": user, "empresas": empresas})

@app.post("/empresas/nova")
async def nova_empresa(
    nome: str = Form(...), 
    razao_social: str = Form(...), # Novo campo adicionado aqui
    cnpj: str = Form(...), 
    tel: str = Form(...), 
    email: str = Form(...)
):
    conn = get_db()
    # Adicione a razao_social no INSERT
    conn.execute("""
        INSERT INTO empresas (nome_fantasia, razao_social, cnpj, telefone, email) 
        VALUES (?, ?, ?, ?, ?)
    """, (nome, razao_social, cnpj, tel, email))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/empresas", status_code=303)

@app.get("/empresas/deletar/{id}")
async def deletar_empresa(id: int):
    conn = get_db()
    conn.execute("DELETE FROM empresas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/empresas", status_code=303)

@app.get("/empresas/editar/{id}", response_class=HTMLResponse)
async def editar_empresa_page(request: Request, id: int):
    user = get_current_user(request)
    if not user or user['perfil'] != 'admin':
        return RedirectResponse(url="/", status_code=303)
    
    conn = get_db()
    empresa = conn.execute("SELECT * FROM empresas WHERE id = ?", (id,)).fetchone()
    conn.close()
    
    if not empresa:
        return RedirectResponse(url="/empresas", status_code=303)
        
    return templates.TemplateResponse("editar_empresa.html", {
        "request": request, 
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
    conn = get_db()
    conn.execute("""
        UPDATE empresas 
        SET nome_fantasia = ?, cnpj = ?, telefone = ?, email = ? 
        WHERE id = ?
    """, (nome, cnpj, tel, email, id))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/empresas", status_code=303)

# Endpoint de API (Uso e Fornecimento de API)
@app.get("/api/produtos/{empresa_id}")
async def api_listar_produtos(empresa_id: int):
    conn = get_db()
    produtos = conn.execute("SELECT nome, quantidade, preco FROM produtos WHERE empresa_id = ?", (empresa_id,)).fetchall()
    conn.close()
    # Retorna um JSON puro, o que caracteriza uma API
    return {"empresa_id": empresa_id, "estoque": [dict(p) for p in produtos]}

if __name__ == "__main__":
    import uvicorn
    # host="0.0.0.0" permite que dispositivos externos acessem
    # port=8000 é a porta padrão, você pode mudar se desejar
    uvicorn.run(app, host="0.0.0.0", port=8000)