import os
import shutil
import sqlite3
from datetime import datetime
from tkinter import *
from tkinter import messagebox, ttk
from database import registar_auditoria

COR_FUNDO = "#eef2ff"
COR_PRIMARIA = "#4f46e5"
COR_TEXTO = "#1e1b4b"
COR_PERIGO = "#dc2626"
COR_HEADER = "#3730a3"
COR_CARD = "#ffffff"
COR_VERDE = "#16a34a"

PASTA_BACKUPS = "backups"
DB_PRINCIPAL = "farmacia.db"


def garantir_pasta_backups():
    """Cria a pasta de backups se nao existir."""
    if not os.path.exists(PASTA_BACKUPS):
        os.makedirs(PASTA_BACKUPS)


def criar_backup(motivo="manual"):
    """Cria um backup do farmacia.db na pasta backups/.
    Copia tambem para o destino externo (OneDrive / Google Drive / etc).
    Retorna o nome do ficheiro criado ou None se erro."""
    if not os.path.exists(DB_PRINCIPAL):
        return None
    
    garantir_pasta_backups()
    
    agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_backup = f"farmacia_{agora}_{motivo}.db"
    caminho = os.path.join(PASTA_BACKUPS, nome_backup)
    
    try:
        # Usa o mecanismo de backup do SQLite para produzir uma cópia
        # consistente mesmo quando a aplicação está aberta.
        origem = sqlite3.connect(DB_PRINCIPAL, timeout=5)
        destino = sqlite3.connect(caminho, timeout=5)
        try:
            origem.backup(destino)
            resultado = destino.execute("PRAGMA integrity_check").fetchone()
            if not resultado or resultado[0] != "ok":
                raise sqlite3.DatabaseError(
                    f"O backup não passou na verificação de integridade: {resultado}"
                )
        finally:
            destino.close()
            origem.close()
        
        # Copiar tambem para destino externo
        try:
            copiar_para_backup_externo(nome_backup)
        except Exception as e:
            print(f"[Backup Externo] Aviso: {e}")
        
        return nome_backup
    except Exception as e:
        if os.path.exists(caminho):
            try:
                os.remove(caminho)
            except OSError:
                pass
        print(f"Erro ao criar backup: {e}")
        return None


def listar_backups():
    """Retorna lista de backups ordenados por data (mais recente primeiro).
    Cada item: (nome, tamanho_kb, data_formatada)."""
    garantir_pasta_backups()
    
    backups = []
    for ficheiro in os.listdir(PASTA_BACKUPS):
        if ficheiro.endswith(".db"):
            caminho = os.path.join(PASTA_BACKUPS, ficheiro)
            try:
                tamanho = os.path.getsize(caminho) / 1024  # KB
                data_mod = datetime.fromtimestamp(os.path.getmtime(caminho))
                backups.append((ficheiro, tamanho, data_mod.strftime("%Y-%m-%d %H:%M:%S")))
            except Exception:
                pass
    
    backups.sort(key=lambda x: x[2], reverse=True)
    return backups


def restaurar_backup(nome_backup):
    """Restaura um backup, substituindo o farmacia.db atual.
    Antes de restaurar, faz um backup de seguranca do atual."""
    caminho_backup = os.path.join(PASTA_BACKUPS, nome_backup)
    
    if not os.path.exists(caminho_backup):
        return False, "Ficheiro de backup nao encontrado."
    
    try:
        # Backup de seguranca do atual
        if os.path.exists(DB_PRINCIPAL):
            segurança = f"farmacia_ANTES_RESTAURO_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.db"
            shutil.copy2(DB_PRINCIPAL, os.path.join(PASTA_BACKUPS, segurança))
        
        shutil.copy2(caminho_backup, DB_PRINCIPAL)
        return True, "Backup restaurado com sucesso!"
    except Exception as e:
        return False, f"Erro ao restaurar: {e}"


def apagar_backup(nome_backup):
    """Apaga um backup especifico."""
    caminho = os.path.join(PASTA_BACKUPS, nome_backup)
    try:
        if os.path.exists(caminho):
            os.remove(caminho)
            return True
        return False
    except Exception:
        return False


def limpar_backups_antigos(manter=30):
    """Mantem apenas os N backups mais recentes."""
    backups = listar_backups()
    if len(backups) <= manter:
        return 0
    
    apagados = 0
    for nome, _, _ in backups[manter:]:
        if apagar_backup(nome):
            apagados += 1
    return apagados


def backup_automatico(utilizador_logado=None):
    """Executa backup automatico no inicio do sistema."""
    nome = criar_backup("auto")
    if nome:
        # Limpar backups antigos (local + externo)
        limpar_backups_antigos(30)
        try:
            limpar_backups_externos(30)
        except Exception:
            pass
        
        # Registar em auditoria
        if utilizador_logado:
            registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                "BACKUP AUTO", f"Criado backup: {nome}")
        print(f"[Backup automatico] {nome}")
    return nome


def abrir_backup(utilizador_logado):
    """Abre a janela de gestao de backups."""
    
    janela = Toplevel()
    janela.title("JAM Soft - Gestao de Backups")
    janela.geometry("900x650")
    janela.configure(bg=COR_FUNDO)
    
    header = Frame(janela, bg=COR_HEADER, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Gestao de Backups", font=("Arial", 18, "bold"),
          bg=COR_HEADER, fg="white").pack(pady=20)
    
    # Info
    info_frame = Frame(janela, bg=COR_CARD, highlightthickness=1, highlightbackground="#c7d2fe")
    info_frame.pack(fill=X, padx=15, pady=15)
    
    Label(info_frame, text="Os backups ficam guardados na pasta 'backups' da aplicacao.",
          font=("Arial", 10, "italic"), bg=COR_CARD, fg=COR_TEXTO).pack(padx=15, pady=10)
    
    # Tabela
    frame_tab = Frame(janela, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=15, pady=10)
    
    colunas = ("Ficheiro", "Tamanho", "Data")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=15)
    tree.heading("Ficheiro", text="Ficheiro")
    tree.heading("Tamanho", text="Tamanho")
    tree.heading("Data", text="Data")
    tree.column("Ficheiro", width=400)
    tree.column("Tamanho", width=120)
    tree.column("Data", width=180)
    tree.pack(fill=BOTH, expand=True, side=LEFT)
    
    sb = Scrollbar(frame_tab, orient="vertical", command=tree.yview)
    sb.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=sb.set)
    
    status_var = StringVar(value="")
    Label(janela, textvariable=status_var, font=("Arial", 10, "bold"),
          bg=COR_FUNDO, fg=COR_PRIMARIA).pack(pady=5)
    
    def carregar():
        for i in tree.get_children():
            tree.delete(i)
        backups = listar_backups()
        for b in backups:
            nome, tam, data = b
            tree.insert("", END, values=(nome, f"{tam:.1f} KB", data))
        status_var.set(f"Total: {len(backups)} backups")
    
    carregar()
    
    def fazer_backup_agora():
        nome = criar_backup("manual")
        if nome:
            registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                "BACKUP MANUAL", f"Criado: {nome}")
            messagebox.showinfo("Backup Criado", f"Backup guardado:\n{nome}")
            carregar()
        else:
            messagebox.showerror("Erro", "Nao foi possivel criar o backup.")
    
    def restaurar():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um backup.")
            return
        
        nome = tree.item(sel[0])["values"][0]
        
        if not messagebox.askyesno("Confirmar Restauro",
            f"Restaurar o backup:\n\n{nome}\n\n"
            "AVISO: O banco de dados atual sera substituido.\n"
            "Um backup de seguranca do atual sera criado automaticamente.\n\n"
            "Depois do restauro, precisa de FECHAR e ABRIR o sistema."):
            return
        
        sucesso, msg = restaurar_backup(nome)
        if sucesso:
            registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                "RESTAURAR BACKUP", f"Restaurado: {nome}")
            messagebox.showinfo("Sucesso", msg + "\n\nFecha e abre o sistema para aplicar.")
        else:
            messagebox.showerror("Erro", msg)
    
    def apagar():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um backup.")
            return
        
        nome = tree.item(sel[0])["values"][0]
        
        if messagebox.askyesno("Confirmar", f"Apagar permanentemente:\n{nome}?"):
            if apagar_backup(nome):
                registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                    "APAGAR BACKUP", f"Apagado: {nome}")
                carregar()
            else:
                messagebox.showerror("Erro", "Nao foi possivel apagar.")
    
    def abrir_pasta():
        """Abre a pasta de backups no explorador."""
        garantir_pasta_backups()
        caminho_abs = os.path.abspath(PASTA_BACKUPS)
        try:
            os.startfile(caminho_abs)
        except Exception:
            messagebox.showinfo("Info", f"Pasta: {caminho_abs}")
    
    # Botoes
    frame_btn = Frame(janela, bg=COR_FUNDO)
    frame_btn.pack(pady=10)
    
    estilo = {"font": ("Arial", 11, "bold"), "width": 20, "height": 2,
              "bd": 0, "cursor": "hand2", "fg": "white"}
    
    Button(frame_btn, text="Novo Backup", bg=COR_VERDE,
           command=fazer_backup_agora, **estilo).grid(row=0, column=0, padx=5)
    Button(frame_btn, text="Restaurar", bg=COR_PRIMARIA,
           command=restaurar, **estilo).grid(row=0, column=1, padx=5)
    Button(frame_btn, text="Apagar", bg=COR_PERIGO,
           command=apagar, **estilo).grid(row=0, column=2, padx=5)
    Button(frame_btn, text="Abrir Pasta", bg="#0891b2",
           command=abrir_pasta, **estilo).grid(row=1, column=0, padx=5, pady=5)
    Button(frame_btn, text="Actualizar", bg="#7c3aed",
           command=carregar, **estilo).grid(row=1, column=1, padx=5, pady=5)

    



# ============================================================
# ============ BACKUP EXTERNO (DETECCAO AUTOMATICA) =========
# ============================================================
# Procura automaticamente por:
#   1. OneDrive
#   2. Google Drive
#   3. Dropbox
#   4. iCloud Drive (Mac)
#   5. Pasta manual C:\JAMSoft_Backups
#   6. Pen drives (E:, F:, G:)
# ============================================================

def detectar_destino_backup():
    """Procura por servicos de nuvem ou pasta manual.
    Retorna o caminho da pasta JAMSoft_Backups ou None."""

    candidatos = []

    # 1. OneDrive
    for base in ["OneDrive", "OneDrive - Personal", "OneDrive - Pessoal"]:
        candidatos.append(os.path.join(os.path.expanduser("~"), base, "JAMSoft_Backups"))

    # 2. Google Drive
    for base in ["Google Drive", "GoogleDrive", "Google Drive - Pessoal"]:
        candidatos.append(os.path.join(os.path.expanduser("~"), base, "JAMSoft_Backups"))

    # 3. Dropbox
    candidatos.append(os.path.join(os.path.expanduser("~"), "Dropbox", "JAMSoft_Backups"))

    # 4. iCloud (Mac)
    candidatos.append(os.path.join(os.path.expanduser("~"), "iCloud Drive", "JAMSoft_Backups"))

    # 5. Pasta manual (utilizador cria manualmente)
    candidatos.append("C:\\JAMSoft_Backups")

    # 6. Pen drives
    for drive in ["E", "F", "G", "H"]:
        candidatos.append(f"{drive}:\\JAMSoft_Backups")

    # Procurar primeiro destino que tenha a pasta-pai
    for destino in candidatos:
        pasta_pai = os.path.dirname(destino)
        if os.path.exists(pasta_pai):
            return destino

    return None


def obter_destino_backup():
    """Retorna o destino a usar. Se nao existir, cria na pasta manual."""
    destino = detectar_destino_backup()

    if destino:
        return destino

    # Nenhum destino detectado - usar pasta local temporaria como fallback
    # (o gerente deve ser avisado depois)
    fallback = "C:\\JAMSoft_Backups"
    try:
        os.makedirs(fallback, exist_ok=True)
        print(f"[Backup] AVISO: nenhuma nuvem detectada. Usando {fallback}")
        return fallback
    except Exception:
        print("[Backup] AVISO: nao foi possivel criar pasta de backup externo")
        return None


def garantir_pasta_backup_externo():
    """Garante que a pasta de destino existe."""
    destino = obter_destino_backup()
    if not destino:
        return None

    try:
        if not os.path.exists(destino):
            os.makedirs(destino)
        return destino
    except Exception as e:
        print(f"[Backup] Erro ao criar pasta destino: {e}")
        return None


def copiar_para_backup_externo(nome_backup):
    """Copia um backup para o destino externo detectado.
    Retorna True se conseguiu."""
    if not nome_backup:
        return False

    destino = garantir_pasta_backup_externo()
    if not destino:
        return False

    origem = os.path.join(PASTA_BACKUPS, nome_backup)
    destino_ficheiro = os.path.join(destino, nome_backup)

    if not os.path.exists(origem):
        return False

    try:
        shutil.copy2(origem, destino_ficheiro)
        print(f"[Backup Externo] Copiado para: {destino}")
        return True
    except Exception as e:
        print(f"[Backup Externo] Erro: {e}")
        return False


def limpar_backups_externos(manter=30):
    """Mantem apenas os N backups mais recentes no destino externo."""
    destino = detectar_destino_backup()
    if not destino or not os.path.exists(destino):
        return 0

    try:
        ficheiros = []
        for f in os.listdir(destino):
            if f.endswith(".db"):
                caminho = os.path.join(destino, f)
                ficheiros.append((f, os.path.getmtime(caminho)))

        ficheiros.sort(key=lambda x: x[1], reverse=True)

        apagados = 0
        for nome, _ in ficheiros[manter:]:
            try:
                os.remove(os.path.join(destino, nome))
                apagados += 1
            except Exception:
                pass

        return apagados
    except Exception:
        return 0


def estado_backup_externo():
    """Retorna informacao sobre o estado do backup externo.
    Util para mostrar na interface."""
    destino = detectar_destino_backup()

    if not destino:
        return {
            "configurado": False,
            "destino": None,
            "servico": None,
            "num_backups": 0,
        }

    servico = "Desconhecido"
    if "OneDrive" in destino:
        servico = "OneDrive"
    elif "Google" in destino:
        servico = "Google Drive"
    elif "Dropbox" in destino:
        servico = "Dropbox"
    elif "iCloud" in destino:
        servico = "iCloud Drive"
    elif ":" in destino and destino[1] == ":":
        if destino[0].upper() in "EFGH":
            servico = f"Pen Drive ({destino[0]}:)"
        else:
            servico = "Pasta Manual"

    num = 0
    if os.path.exists(destino):
        num = len([f for f in os.listdir(destino) if f.endswith(".db")])

    return {
        "configurado": True,
        "destino": destino,
        "servico": servico,
        "num_backups": num,
    }
