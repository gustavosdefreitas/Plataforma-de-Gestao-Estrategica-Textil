import sqlite3

conn = sqlite3.connect('estoque.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    quantidade INTEGER DEFAULT 0,
    preco REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id INTEGER,
    quantidade INTEGER,
    preco_unitario REAL,
    total REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.executemany("INSERT OR REPLACE INTO produtos (id, nome, quantidade, preco) VALUES (?, ?, ?, ?)", [
    (1, "Arroz 5kg", 50, 12.50),
    (2, "Feijao 1kg", 30, 8.50),
    (3, "Macarrao", 25, 5.00),
    (4, "Leite 1L", 40, 4.50),
    (5, "Pao", 100, 0.50)
])

conn.commit()
conn.close()
print("Banco OK! 5 produtos!")
