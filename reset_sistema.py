import sqlite3
import hashlib

# APAGA TUDO e recria BANCO LIMPO
conn = sqlite3.connect('estoque.db')
c = conn.cursor()
c.execute('DROP TABLE IF EXISTS usuarios')
c.execute('DROP TABLE IF EXISTS produtos')
c.execute('DROP TABLE IF EXISTS vendas')

# CRIA TABELAS
c.execute('''CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    session_id TEXT,
    perfil TEXT DEFAULT "user"
)''')

c.execute('''CREATE TABLE produtos (
    id INTEGER PRIMARY KEY,
    nome TEXT,
    quantidade INTEGER,
    preco REAL
)''')

c.execute('''CREATE TABLE vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id INTEGER,
    quantidade INTEGER,
    preco_unitario REAL,
    total REAL
)''')

# ADMIN com SENHA 123456 (hash correto)
hash_admin = hashlib.sha256('123456'.encode()).hexdigest()
c.execute('INSERT INTO usuarios (username, password, perfil) VALUES (?, ?, ?)', 
          ('admin', hash_admin, 'admin'))

# PRODUTOS DE TESTE
c.executemany('INSERT OR REPLACE INTO produtos VALUES(?, ?, ?, ?)', [
    (1, 'Arroz 5kg', 50, 12.5),
    (2, 'Feijão 1kg', 30, 8.5),
    (3, 'Macarrão 500g', 25, 5.0)
])

conn.commit()
conn.close()
print('✅ SISTEMA RECRIADO!')
print('👤 Login: admin')
print('🔑 Senha: 123456')
print('🎉 http://localhost:8000')
