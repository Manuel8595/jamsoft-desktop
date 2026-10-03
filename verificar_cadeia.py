from database import conectar

conn = conectar()
cur = conn.cursor()

# ─── 1. Contagens ───
cur.execute("SELECT COUNT(*) FROM facturas WHERE serie LIKE 'FT%'")
total = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM facturas WHERE serie LIKE 'FT%' AND hash_documento IS NOT NULL AND hash_documento != ''")
com_hash = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM facturas WHERE serie LIKE 'FT%' AND hash_anterior IS NOT NULL AND hash_anterior != ''")
com_anterior = cur.fetchone()[0]

print(f"Total FT: {total}")
print(f"Com hash: {com_hash}")
print(f"Com hash_anterior (encadeado): {com_anterior}")
print()

# ─── 2. Últimas 10 ───
cur.execute("SELECT id, numero, hash_documento, hash_anterior FROM facturas WHERE serie LIKE 'FT%' ORDER BY id DESC LIMIT 10")

print("Ultimas 10 facturas FT:")
print()
for f in cur.fetchall():
    fid, numero, h, ha = f
    h_txt = (h[:20] + "...") if h else "(VAZIO)"
    ha_txt = (ha[:20] + "...") if ha else "(VAZIO)"
    print(f"ID {fid} | {numero}")
    print(f"  hash:     {h_txt}")
    print(f"  anterior: {ha_txt}")
    print()

# ─── 3. QR Code ───
cur.execute("SELECT numero, qr_code FROM facturas ORDER BY id DESC LIMIT 1")
numero, qr = cur.fetchone()
print(f"QR da ultima factura ({numero}):")
print(f"  {qr if qr else '(VAZIO)'}")
print(f"  Tamanho: {len(qr) if qr else 0} caracteres")

conn.close()