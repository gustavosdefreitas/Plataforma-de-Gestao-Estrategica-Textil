import sqlite3

conn = sqlite3.connect('estoque.db')
c = conn.cursor()

# Adiciona coluna perfil (ignora se já existe)
try:
    c.execute('ALTER TABLE usuarios ADD COLUMN perfil TEXT DEFAULT "user"')
    print('✅ Coluna perfil criada!')
except:
    print('ℹ️ Coluna perfil já existe')

# Define admin como ADMIN
c.execute('UPDATE usuarios SET perfil = "admin" WHERE username = "admin"')
conn.commit()
conn.close()

print('🎉 USUÁRIO admin = ADMIN!')
print('👤 Login: admin')
print('🔑 Senha: 123456')
