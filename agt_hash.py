"""
Módulo de hash encadeado para facturas AGT.
O hash de cada factura depende do hash da factura anterior (mesma série).
"""
import hashlib
from database import conectar


def obter_hash_anterior(serie):
    """
    Devolve o hash da última factura emitida na série indicada.
    Se não houver nenhuma, devolve string vazia.
    """
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT hash_documento FROM facturas
        WHERE serie = ? AND hash_documento IS NOT NULL AND hash_documento != ''
        ORDER BY id DESC LIMIT 1
    """, (serie,))
    r = cur.fetchone()
    conn.close()

    return r[0] if r and r[0] else ""


def gerar_hash_encadeado(numero, serie, data, nif_empresa, total,
                          cliente_nif="", hash_anterior=""):
    """
    Gera hash SHA-256 encadeado (padrão AGT):
    hash = SHA256(hash_anterior + numero;serie;data;nif;total;cliente_nif)

    Se hash_anterior for vazio (primeira factura), o hash é calculado
    apenas com os dados da factura.
    """
    dados = f"{numero};{serie};{data};{nif_empresa};{total};{cliente_nif}"

    if hash_anterior:
        conteudo = f"{hash_anterior}{dados}"
    else:
        conteudo = dados

    hash_obj = hashlib.sha256(conteudo.encode("utf-8"))
    return hash_obj.hexdigest().upper()


def calcular_hash_factura(numero, serie, data, nif_empresa, total, cliente_nif=""):
    """
    Função de alto nível: busca automaticamente o hash anterior da série
    e devolve (hash_novo, hash_anterior).
    """
    hash_anterior = obter_hash_anterior(serie)

    hash_novo = gerar_hash_encadeado(
        numero=numero,
        serie=serie,
        data=data,
        nif_empresa=nif_empresa,
        total=total,
        cliente_nif=cliente_nif,
        hash_anterior=hash_anterior,
    )

    return hash_novo, hash_anterior


def validar_cadeia(serie, verbose=False):
    """
    Valida que a cadeia de hashes de uma série está íntegra.
    Percorre todas as facturas e confirma que cada hash depende
    correctamente do anterior.

    Devolve (ok, mensagem, num_validas, num_invalidas).
    """
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, numero, data, hash_documento, hash_anterior,
               (SELECT nif FROM empresa LIMIT 1) as nif,
               total, cliente_nif
        FROM facturas
        WHERE serie = ?
        ORDER BY id ASC
    """, (serie,))
    facturas = cur.fetchall()
    conn.close()

    if not facturas:
        return True, "Sem facturas na série", 0, 0

    validas = 0
    invalidas = 0
    hash_esperado_anterior = ""

    for f in facturas:
        fid, numero, data, hash_guardado, hash_anterior_guardado, nif, total, cli_nif = f

        if not hash_guardado:
            if verbose:
                print(f"⚠️ Factura {numero} sem hash")
            invalidas += 1
            continue

        # Recalcular hash esperado
        dados = f"{numero};{serie};{data};{nif or ''};{total};{cli_nif or ''}"
        if hash_esperado_anterior:
            conteudo = f"{hash_esperado_anterior}{dados}"
        else:
            conteudo = dados

        hash_esperado = hashlib.sha256(conteudo.encode("utf-8")).hexdigest().upper()

        if hash_esperado == hash_guardado:
            validas += 1
        else:
            invalidas += 1
            if verbose:
                print(f"❌ Factura {numero} — hash não confere")

        hash_esperado_anterior = hash_guardado

    ok = (invalidas == 0)
    if ok:
        msg = f"✅ Cadeia válida: {validas} facturas íntegras"
    else:
        msg = f"❌ Cadeia inválida: {invalidas} facturas corrompidas"

    return ok, msg, validas, invalidas