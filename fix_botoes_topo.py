"""
Move os botoes da Lista IBT para o TOPO (abaixo do header).
Uso: python _fix_botoes_topo.py
"""

path = "transferencias.py"

with open(path, encoding="utf-8") as f:
    c = f.read()

# Mudar a linha do frame_btn: de side=BOTTOM para side=TOP
antigo = '''    frame_btn = Frame(janela, bg=COR_CARD, height=80)
    frame_btn.pack(fill=X, side=BOTTOM)
    frame_btn.pack_propagate(False)'''

novo = '''    frame_btn = Frame(janela, bg=COR_CARD, height=80)
    frame_btn.pack(fill=X, side=TOP)      # TOPO em vez de BOTTOM
    frame_btn.pack_propagate(False)'''

if antigo in c:
    c = c.replace(antigo, novo)
    print("OK - frame_btn agora fica no TOPO")
else:
    print("AVISO - padrao do frame_btn nao encontrado")

with open(path, "w", encoding="utf-8") as f:
    f.write(c)

print()
print("=" * 60)
print("OK - Correcao aplicada!")
print("=" * 60)