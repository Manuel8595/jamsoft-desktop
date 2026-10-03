import sqlite3

conn = sqlite3.connect('farmacia.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tentativas_login'")
r = cur.fetchone()
print('Tabela tentativas_login existe:', r is not None)
conn.close()