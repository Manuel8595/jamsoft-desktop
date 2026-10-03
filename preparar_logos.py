"""
Redimensiona os logos para os tamanhos finais usados nas aplicações.
"""
from PIL import Image
from pathlib import Path


PASTA = Path("logos")


def redimensionar(entrada, saida, tamanho_max):
    """Mantém proporção, redimensiona até tamanho_max na maior dimensão."""
    if not entrada.exists():
        print(f"⚠️  {entrada} nao encontrado")
        return

    img = Image.open(entrada).convert("RGBA")
    largura, altura = img.size

    if largura > altura:
        nova_largura = tamanho_max
        nova_altura = int(altura * (tamanho_max / largura))
    else:
        nova_altura = tamanho_max
        nova_largura = int(largura * (tamanho_max / altura))

    img_nova = img.resize((nova_largura, nova_altura), Image.LANCZOS)
    img_nova.save(saida, "PNG", optimize=True)
    print(f"✅ {saida} ({nova_largura}x{nova_altura})")


def quadrado(entrada, saida, tamanho):
    """Cria versão quadrada com padding transparente."""
    if not entrada.exists():
        print(f"⚠️  {entrada} nao encontrado")
        return

    img = Image.open(entrada).convert("RGBA")
    img.thumbnail((tamanho, tamanho), Image.LANCZOS)

    novo = Image.new("RGBA", (tamanho, tamanho), (255, 255, 255, 0))
    x = (tamanho - img.size[0]) // 2
    y = (tamanho - img.size[1]) // 2
    novo.paste(img, (x, y), img)

    novo.save(saida, "PNG", optimize=True)
    print(f"✅ {saida} ({tamanho}x{tamanho})")


def quadrado_escuro(entrada, saida, tamanho):
    """Cria versão quadrada com fundo escuro."""
    if not entrada.exists():
        print(f"⚠️  {entrada} nao encontrado")
        return

    img = Image.open(entrada).convert("RGBA")
    img.thumbnail((int(tamanho * 0.8), int(tamanho * 0.8)), Image.LANCZOS)

    novo = Image.new("RGBA", (tamanho, tamanho), (15, 23, 42, 255))
    x = (tamanho - img.size[0]) // 2
    y = (tamanho - img.size[1]) // 2
    novo.paste(img, (x, y), img)

    novo.save(saida, "PNG", optimize=True)
    print(f"✅ {saida} ({tamanho}x{tamanho})")


if __name__ == "__main__":
    print()
    print("=" * 60)
    print("  PREPARAR LOGOS — JAM Soft")
    print("=" * 60)
    print()

    print("📱 Ícones da aplicação:")
    quadrado(PASTA / "logo_app.png", PASTA / "icon_192.png", 192)
    quadrado(PASTA / "logo_app.png", PASTA / "icon_512.png", 512)
    quadrado(PASTA / "logo_app.png", PASTA / "favicon_32.png", 32)
    quadrado(PASTA / "logo_app.png", PASTA / "favicon_64.png", 64)

    print()
    print("🌙 Ícone escuro:")
    quadrado_escuro(PASTA / "logo_app.png", PASTA / "icon_192_escuro.png", 192)

    print()
    print("📄 Logos horizontais:")
    redimensionar(PASTA / "logo_horizontal.png",
                  PASTA / "logo_horizontal_grande.png", 1200)
    redimensionar(PASTA / "logo_horizontal.png",
                  PASTA / "logo_horizontal_medio.png", 600)
    redimensionar(PASTA / "logo_horizontal.png",
                  PASTA / "logo_horizontal_pequeno.png", 300)

    print()
    print("=" * 60)
    print("  Concluído!")
    print("=" * 60)
    print()