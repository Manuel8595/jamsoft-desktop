"""
Cria pacote ZIP de distribuição (só código, sem dados).
"""
import zipfile
from pathlib import Path

from version import obter_versao


VERSAO = obter_versao()
NOME_ZIP = f"JAM_Soft_v{VERSAO}_Instalacao.zip"


INCLUIR_FICHEIROS = [
    "LEIA-ME.txt",
    "MANUAL_JAMSOFT.md",
    "RESUMO_SISTEMA.md",
    "VERSION",
    "VERSION_HISTORY.md",
    "requirements.txt",
    "INICIAR_FARMACIA.bat",
    ".gitignore",
]

INCLUIR_PASTAS = [
    "logos",
    "scripts",
]

EXCLUIR_TERMOS = [
    "farmacia.db",
    "farmacia_backup",
    ".env",
    ".sessao_supabase",
    "secrets.toml",
    "venv",
    ".venv",
    "__pycache__",
    ".pyc",
    ".pyo",
    "plataforma_web",
    "backups",
    "facturas",
    "relatorios",
    ".git",
    "teste_",
]


def _deve_excluir(caminho_str):
    s = str(caminho_str).replace("\\", "/").lower()
    for termo in EXCLUIR_TERMOS:
        if termo.lower() in s:
            return True
    return False


def criar_pacote():
    pasta = Path(__file__).parent
    n_ficheiros = 0
    tamanho = 0

    print()
    print("=" * 60)
    print(f"  CRIAR PACOTE — JAM Soft v{VERSAO}")
    print("=" * 60)
    print()

    with zipfile.ZipFile(NOME_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:

        # Ficheiros específicos
        for nome in INCLUIR_FICHEIROS:
            f = pasta / nome
            if f.is_file() and not _deve_excluir(nome):
                zipf.write(f, nome)
                n_ficheiros += 1
                tamanho += f.stat().st_size
                print(f"  + {nome}")

        # Todos os .py da raiz
        for f in pasta.glob("*.py"):
            nome = f.name
            if _deve_excluir(nome):
                continue
            zipf.write(f, nome)
            n_ficheiros += 1
            tamanho += f.stat().st_size
            print(f"  + {nome}")

        # Pastas
        for nome_pasta in INCLUIR_PASTAS:
            p = pasta / nome_pasta
            if p.is_dir():
                for f in p.rglob("*"):
                    if f.is_file() and not _deve_excluir(f.relative_to(pasta)):
                        rel = f.relative_to(pasta)
                        zipf.write(f, rel)
                        n_ficheiros += 1
                        tamanho += f.stat().st_size
                        print(f"  + {rel}")

    tamanho_zip = Path(NOME_ZIP).stat().st_size / (1024 * 1024)

    print()
    print("=" * 60)
    print(f"  ✅ Pacote criado: {NOME_ZIP}")
    print(f"     Ficheiros: {n_ficheiros}")
    print(f"     Tamanho:   {tamanho_zip:.1f} MB")
    print("=" * 60)
    print()


if __name__ == "__main__":
    criar_pacote()
    