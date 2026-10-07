"""
Converte o logo PNG para ICO (com multiplos tamanhos).
Windows mostra o tamanho certo em cada sítio.
"""
from PIL import Image
from pathlib import Path


PASTA = Path("logos")


def png_para_ico(png_entrada, ico_saida, tamanhos=None):
    """Converte PNG para ICO com múltiplos tamanhos."""
    if not png_entrada.exists():
        print(f"⚠️  {png_entrada} nao encontrado")
        return False

    if tamanhos is None:
        tamanhos = [16, 24, 32, 48, 64, 128, 256]

    img = Image.open(png_entrada).convert("RGBA")

    # Vamos usar o maior tamanho como base
    img = img.resize((256, 256), Image.LANCZOS)

    ico_saida.parent.mkdir(parents=True, exist_ok=True)
    img.save(ico_saida, format="ICO", sizes=[(t, t) for t in tamanhos])
    print(f"✅ {ico_saida}")
    return True


if __name__ == "__main__":
    print()
    print("=" * 60)
    print("  CRIAR ICO — JAM Soft")
    print("=" * 60)
    print()

    # Ícone principal (para janela)
    png_para_ico(
        PASTA / "logo_app.png",
        PASTA / "jamsoft.ico",
    )

    # Ícone alternativo (fundo escuro)
    png_para_ico(
        PASTA / "icon_192_escuro.png",
        PASTA / "jamsoft_escuro.ico",
    )

    print()
    print("=" * 60)
    print("  Concluido!")
    print("=" * 60)
    print()