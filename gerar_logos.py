"""
Gera 3 propostas de logotipo JAM Soft.
Sem internet, sem Canva — só PIL (Pillow).
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


# Cores JAM Soft
COR_PRIMARIA = "#7c3aed"     # Roxo
COR_DOURADO = "#fbbf24"      # Dourado
COR_ESCURA = "#0f172a"       # Azul escuro
COR_BRANCA = "#ffffff"
COR_VERDE = "#10b981"        # Verde farmácia


PASTA_SAIDA = Path("logos")
PASTA_SAIDA.mkdir(exist_ok=True)


def _carregar_fonte(tamanho):
    """Tenta carregar fontes comuns do Windows."""
    fontes = [
        "C:/Windows/Fonts/segoeuib.ttf",   # Segoe UI Bold
        "C:/Windows/Fonts/arialbd.ttf",    # Arial Bold
        "C:/Windows/Fonts/calibrib.ttf",   # Calibri Bold
    ]
    for f in fontes:
        try:
            return ImageFont.truetype(f, tamanho)
        except Exception:
            continue
    return ImageFont.load_default()


def _carregar_fonte_normal(tamanho):
    fontes = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
    ]
    for f in fontes:
        try:
            return ImageFont.truetype(f, tamanho)
        except Exception:
            continue
    return ImageFont.load_default()


# ============================================================
# PROPOSTA 1 — Moderna (quadrado roxo com pílula)
# ============================================================
def proposta_1():
    """Quadrado roxo com uma pílula dourada. Estilo app."""
    tamanho = 512
    img = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fundo roxo com cantos arredondados
    raio = 100
    draw.rounded_rectangle(
        [(0, 0), (tamanho, tamanho)],
        radius=raio,
        fill=COR_PRIMARIA,
    )

    # Círculo dourado (representa pílula)
    centro = tamanho // 2
    raio_circulo = 130
    draw.ellipse(
        [
            (centro - raio_circulo - 30, centro - raio_circulo - 50),
            (centro + raio_circulo - 30, centro + raio_circulo - 50),
        ],
        fill=COR_DOURADO,
    )

    # Círculo branco interior (efeito pílula)
    draw.ellipse(
        [
            (centro - raio_circulo + 30, centro - raio_circulo - 50 + 60),
            (centro + raio_circulo - 30, centro + raio_circulo - 50 - 60),
        ],
        fill=COR_BRANCA,
    )

    # Texto JAM Soft
    fonte = _carregar_fonte(72)
    texto = "JAM Soft"
    bbox = draw.textbbox((0, 0), texto, font=fonte)
    largura_texto = bbox[2] - bbox[0]
    draw.text(
        ((tamanho - largura_texto) // 2, tamanho - 130),
        texto,
        font=fonte,
        fill=COR_BRANCA,
    )

    img.save(PASTA_SAIDA / "logo_v1_moderna_512.png")
    img.resize((192, 192), Image.LANCZOS).save(
        PASTA_SAIDA / "logo_v1_moderna_192.png")

    print("✅ Proposta 1: Moderna (roxo + pílula dourada)")


# ============================================================
# PROPOSTA 2 — Clássica (letra grande + nome)
# ============================================================
def proposta_2():
    """Letra 'J' estilizada + texto. Estilo corporativo."""
    largura = 512
    altura = 512
    img = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fundo roxo
    draw.rectangle([(0, 0), (largura, altura)], fill=COR_ESCURA)

    # Faixa dourada
    draw.rectangle([(0, altura - 100), (largura, altura)], fill=COR_DOURADO)

    # Letra J grande
    fonte_j = _carregar_fonte(300)
    texto_j = "J"
    bbox = draw.textbbox((0, 0), texto_j, font=fonte_j)
    largura_j = bbox[2] - bbox[0]
    altura_j = bbox[3] - bbox[1]
    draw.text(
        ((largura - largura_j) // 2 - 80, (altura - altura_j) // 2 - 50),
        texto_j,
        font=fonte_j,
        fill=COR_PRIMARIA,
    )

    # Texto "AM Soft" ao lado
    fonte = _carregar_fonte(90)
    draw.text((200, 180), "AM", font=fonte, fill=COR_BRANCA)
    draw.text((200, 270), "Soft", font=fonte, fill=COR_BRANCA)

    img.save(PASTA_SAIDA / "logo_v2_classica_512.png")
    img.resize((192, 192), Image.LANCZOS).save(
        PASTA_SAIDA / "logo_v2_classica_192.png")

    print("✅ Proposta 2: Clássica (letra J + nome)")


# ============================================================
# PROPOSTA 3 — Minimalista (só texto elegante)
# ============================================================
def proposta_3():
    """Só texto elegante. Estilo Apple/moderno."""
    largura = 512
    altura = 512
    img = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fundo gradiente simulado (roxo escuro -> roxo)
    for y in range(altura):
        intensidade = int(15 + (y / altura) * 40)
        cor = f"#{int(70 * (1 - y / altura)) + 30:02x}3aed"
        draw.line([(0, y), (largura, y)], fill=f"#{int(60 - y / altura * 30):02x}3aed")

    # Círculo decorativo dourado (pequeno)
    draw.ellipse([(200, 150), (312, 262)], fill=COR_DOURADO)

    # "JAM" grande
    fonte_jam = _carregar_fonte(120)
    texto = "JAM"
    bbox = draw.textbbox((0, 0), texto, font=fonte_jam)
    w = bbox[2] - bbox[0]
    draw.text(((largura - w) // 2, 270), texto, font=fonte_jam, fill=COR_BRANCA)

    # "Soft" por baixo
    fonte_soft = _carregar_fonte_normal(60)
    texto2 = "SOFT"
    bbox2 = draw.textbbox((0, 0), texto2, font=fonte_soft)
    w2 = bbox2[2] - bbox2[0]
    draw.text(
        ((largura - w2) // 2, 400),
        texto2,
        font=fonte_soft,
        fill=COR_DOURADO,
    )

    img.save(PASTA_SAIDA / "logo_v3_minimalista_512.png")
    img.resize((192, 192), Image.LANCZOS).save(
        PASTA_SAIDA / "logo_v3_minimalista_192.png")

    print("✅ Proposta 3: Minimalista (texto elegante)")


# ============================================================
# LOGO HORIZONTAL (para documentos/PDF)
# ============================================================
def logo_horizontal():
    """Versão horizontal — para cabeçalhos, PDFs."""
    largura = 1200
    altura = 400
    img = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # "JAM" grande roxo
    fonte_jam = _carregar_fonte(180)
    draw.text((50, 80), "JAM", font=fonte_jam, fill=COR_PRIMARIA)

    # "Soft" dourado
    fonte_soft = _carregar_fonte(120)
    draw.text((50, 260), "Soft", font=fonte_soft, fill=COR_DOURADO)

    # Linha decorativa
    draw.rectangle([(600, 150), (610, 280)], fill=COR_PRIMARIA)

    # Subtítulo
    fonte_sub = _carregar_fonte_normal(60)
    draw.text((640, 180), "Gestão de Farmácias", font=fonte_sub, fill=COR_ESCURA)
    draw.text((640, 260), "Angola", font=fonte_sub, fill=COR_CINZA if False else "#64748b")

    img.save(PASTA_SAIDA / "logo_horizontal.png")
    print("✅ Logo horizontal criado (para documentos)")


# ============================================================
# FAVICON / ÍCONE PEQUENO
# ============================================================
def favicon():
    """Ícone muito pequeno (32x32) para browser/PWA."""
    tamanho = 32
    img = Image.new("RGBA", (tamanho, tamanho), COR_PRIMARIA)
    draw = ImageDraw.Draw(img)

    # Círculo dourado pequeno
    draw.ellipse([(8, 6), (24, 22)], fill=COR_DOURADO)
    # Ponto branco
    draw.ellipse([(13, 11), (19, 17)], fill=COR_BRANCA)

    img.save(PASTA_SAIDA / "favicon_32.png")
    print("✅ Favicon 32x32 criado")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print()
    print("=" * 60)
    print("  GERADOR DE LOGOTIPOS — JAM Soft")
    print("=" * 60)
    print()

    proposta_1()
    proposta_2()
    proposta_3()
    logo_horizontal()
    favicon()

    print()
    print("=" * 60)
    print("  Concluído!")
    print(f"  Ficheiros em: {PASTA_SAIDA}/")
    print("=" * 60)
    print()