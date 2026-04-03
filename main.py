from fastapi import FastAPI, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import hashlib
import uuid

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- BANCO DE DADOS ---
def get_db():
    conn = sqlite3.connect('estoque.db')
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Auxiliar para verificar login em todas as rotas
def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM usuarios WHERE session_id = ?", (session_id,)).fetchone()
    conn.close()
    return user

# --- ROTAS DE AUTENTICAÇÃO ---
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = get_db()
    user = conn.execute("SELECT * FROM usuarios WHERE username = ?", (username,)).fetchone()
    conn.close()

    if user and user['password'] == hash_password(password):
        session_id = str(uuid.uuid4())
        conn = get_db()
        conn.execute("UPDATE usuarios SET session_id = ? WHERE id = ?", (session_id, user['id']))
        conn.commit()
        conn.close()
        
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

    conn = get_db()
    # Dados para os cards
    total_produtos = conn.execute("SELECT SUM(quantidade) FROM produtos").fetchone()[0] or 0
    total_vendas = conn.execute("SELECT COUNT(*) FROM vendas").fetchone()[0]
    total_empresas = conn.execute("SELECT COUNT(*) FROM empresas").fetchone()[0]
    total_fornecedores = conn.execute("SELECT COUNT(*) FROM fornecedores").fetchone()[0]

    # ANÁLISE DE DADOS: Busca quantidade de produtos por empresa para o GRÁFICO
    # (Assume que você já vinculou a coluna empresa_id em produtos)
    dados_grafico = conn.execute("""
        SELECT e.nome_fantasia, SUM(p.quantidade) as total 
        FROM produtos p 
        JOIN empresas e ON p.empresa_id = e.id 
        GROUP BY e.id
    """).fetchall()

    dados_fornecedores = conn.execute("""
        SELECT f.nome, COUNT(p.id)
        FROM produtos p
        JOIN fornecedores f ON p.fornecedor_id = f.id
        GROUP BY f.nome
    """).fetchall()

    # Prepara listas para o JavaScript ler
    labels = [d['nome_fantasia'] for d in dados_grafico]
    valores = [d['total'] for d in dados_grafico]

    vendas_recentes = conn.execute("""
        SELECT v.*, p.nome FROM vendas v 
        JOIN produtos p ON v.produto_id = p.id 
        ORDER BY v.id DESC LIMIT 5
    """).fetchall()
    conn.close()

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
    conn.execute("""
        INSERT INTO produtos (nome, quantidade, preco, empresa_id, fornecedor_id) 
        VALUES (?, ?, ?, ?, ?)
    """, (nome, quantidade, preco, empresa_id, fornecedor_id))
    
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
    produto = conn.execute("SELECT * FROM produtos WHERE id = ?", (id,)).fetchone()
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
    except sqlite3.IntegrityError:
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
async def registrar_venda(produto_id: int = Form(...), qtd_venda: int = Form(...)):
    conn = get_db()
    prod = conn.execute("SELECT quantidade, preco FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    
    if prod and prod['quantidade'] >= qtd_venda:
        total = qtd_venda * prod['preco']
        conn.execute("INSERT INTO vendas (produto_id, quantidade, preco_unitario, total) VALUES (?, ?, ?, ?)",
                     (produto_id, qtd_venda, prod['preco'], total))
        conn.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?", (qtd_venda, produto_id))
        conn.commit()
    
    conn.close()
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