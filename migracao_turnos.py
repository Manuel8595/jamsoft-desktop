from database import conectar

c = conectar()
cur = c.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS turnos_caixa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        caixa_id INTEGER,
        data_abertura TEXT,
        data_fecho TEXT,
        utilizador_id INTEGER,
        utilizador_nome TEXT,
        valor_inicial REAL DEFAULT 0,
        total_vendas REAL DEFAULT 0,
        total_dinheiro REAL DEFAULT 0,
        total_tpa REAL DEFAULT 0,
        total_pix REAL DEFAULT 0,
        dinheiro_contado REAL DEFAULT 0,
        tpa_contado REAL DEFAULT 0,
        total_contado REAL DEFAULT 0,
        total_sistema REAL DEFAULT 0,
        diferenca REAL DEFAULT 0,
        estado TEXT DEFAULT 'ABERTO',
        observacoes TEXT
    )
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS detalhe_notas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        turno_id INTEGER,
        tipo TEXT,
        nota_5000 INTEGER DEFAULT 0,
        nota_2000 INTEGER DEFAULT 0,
        nota_1000 INTEGER DEFAULT 0,
        nota_500 INTEGER DEFAULT 0,
        nota_200 INTEGER DEFAULT 0,
        nota_100 INTEGER DEFAULT 0,
        nota_50 INTEGER DEFAULT 0,
        nota_20 INTEGER DEFAULT 0,
        nota_10 INTEGER DEFAULT 0,
        total REAL DEFAULT 0
    )
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS taloes_tpa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        turno_id INTEGER,
        numero_talao TEXT,
        valor REAL,
        data_hora TEXT,
        conciliado INTEGER DEFAULT 0
    )
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS fecho_dia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        total_turnos INTEGER DEFAULT 0,
        total_vendas REAL DEFAULT 0,
        total_dinheiro REAL DEFAULT 0,
        total_tpa REAL DEFAULT 0,
        total_pix REAL DEFAULT 0,
        total_faltas REAL DEFAULT 0,
        total_sobras REAL DEFAULT 0,
        dinheiro_fisico REAL DEFAULT 0,
        tpa_fisico REAL DEFAULT 0,
        total_contado REAL DEFAULT 0,
        total_sistema REAL DEFAULT 0,
        diferenca_final REAL DEFAULT 0,
        valor_depositar REAL DEFAULT 0,
        valor_repor REAL DEFAULT 0,
        banco_destino TEXT,
        numero_deposito TEXT,
        data_deposito TEXT,
        estado TEXT DEFAULT 'ABERTO',
        gerente_id INTEGER,
        gerente_nome TEXT,
        confirmado_em TEXT,
        observacoes TEXT
    )
""")

c.commit()
c.close()

print("OK - Tabelas criadas com sucesso!")
print("  - turnos_caixa")
print("  - detalhe_notas")
print("  - taloes_tpa")
print("  - fecho_dia")