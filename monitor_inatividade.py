"""
Monitor de inactividade - bloqueia a sessao apos N minutos.
"""

import tkinter as tk
from tkinter import messagebox
from datetime import datetime


class MonitorInatividade:
    """
    Monitoriza a inactividade do utilizador.

    - Se ficar N minutos sem mexer, avisa 1 minuto antes.
    - Se continuar sem mexer, BLOQUEIA a sessao.
    - Ao autenticar, continua onde estava.
    """

    def __init__(self, root, utilizador, timeout_min=15, callback_bloqueio=None):
        self.root = root
        self.utilizador = utilizador
        self.timeout_min = timeout_min
        self.callback_bloqueio = callback_bloqueio

        self.ultima_atividade = datetime.now()
        self.ativo = True
        self.bloqueado = False
        self.avisado = False
        self.job_id = None

        # Bind de eventos globais (cliques e teclas)
        self._binds = []
        self._registar_eventos()

        # Iniciar loop
        self._loop()

    def _registar_eventos(self):
        """Regista handlers para detectar actividade."""
        eventos = [
            "<Button>", "<Key>", "<Motion>",
            "<ButtonPress>", "<ButtonRelease>",
        ]

        def _marcar_atividade(event=None):
            if not self.bloqueado:
                self.ultima_atividade = datetime.now()
                self.avisado = False

        for evt in eventos:
            try:
                bid = self.root.bind_all(evt, _marcar_atividade, add="+")
                self._binds.append((evt, bid))
            except Exception:
                pass

    def _loop(self):
        """Verifica o tempo de inactividade a cada 30s."""
        if not self.ativo:
            return

        try:
            agora = datetime.now()
            diff = agora - self.ultima_atividade
            minutos = diff.total_seconds() / 60

            # Se ja passou o timeout -> BLOQUEAR
            if minutos >= self.timeout_min and not self.bloqueado:
                self._bloquear()
                return

            # Aviso 1 minuto antes (só uma vez)
            if (not self.bloqueado and
                not self.avisado and
                minutos >= (self.timeout_min - 1)):
                self._avisar()
        except Exception as e:
            print(f"[Monitor] Erro: {e}")

        # Re-agendar
        self.job_id = self.root.after(30000, self._loop)

    def _avisar(self):
        """Aviso 1 min antes de bloquear (não reinicia timer)."""
        self.avisado = True
        try:
            minutos_restantes = max(
                1,
                int(self.timeout_min - 
                    (datetime.now() - self.ultima_atividade).total_seconds() / 60)
            )

            self.root.bell()
            messagebox.showwarning(
                "Sessao vai expirar",
                f"A sua sessao vai expirar em {minutos_restantes} minuto(s)\n\n"
                f"Mexa o rato ou o teclado para continuar ligado."
            )
        except Exception:
            pass

    def _bloquear(self):
        """Bloqueia a sessao e pede credenciais."""
        self.bloqueado = True

        # Guardar janelas abertas
        janelas_abertas = []
        for w in self.root.winfo_children():
            if isinstance(w, tk.Toplevel) and w.winfo_viewable():
                janelas_abertas.append(w)

        # Esconder temporariamente (nao destruir)
        for j in janelas_abertas:
            try:
                j.withdraw()
            except Exception:
                pass

        # Popup de bloqueio
        self._pedir_credenciais(janelas_abertas)

    def _pedir_credenciais(self, janelas_abertas):
        """Mostra popup para autenticar."""
        try:
            from database import autenticar

            bloqueio = tk.Toplevel(self.root)
            bloqueio.title("Sessao Bloqueada")
            bloqueio.geometry("480x420")
            bloqueio.configure(bg="#0f172a")
            bloqueio.attributes("-topmost", True)
            bloqueio.protocol("WM_DELETE_WINDOW", lambda: None)
            bloqueio.grab_set()

            bloqueio.update_idletasks()
            x = (bloqueio.winfo_screenwidth() - 480) // 2
            y = (bloqueio.winfo_screenheight() - 420) // 2
            bloqueio.geometry(f"480x420+{x}+{y}")

            # Header
            header = tk.Frame(bloqueio, bg="#dc2626", height=70)
            header.pack(fill=tk.X)
            header.pack_propagate(False)
            tk.Label(header, text="SESSAO BLOQUEADA",
                     font=("Segoe UI", 16, "bold"),
                     bg="#dc2626", fg="white").pack(pady=20)

            tk.Label(bloqueio,
                     text=f"Sessao de {self.utilizador['nome']}\n\n"
                          f"Ficou inactivo por {self.timeout_min} minutos.\n\n"
                          f"Introduza as credenciais para continuar:",
                     font=("Segoe UI", 11),
                     bg="#0f172a", fg="#f8fafc",
                     justify=tk.CENTER).pack(pady=(20, 15))

            frame = tk.Frame(bloqueio, bg="#0f172a")
            frame.pack(pady=10)

            tk.Label(frame, text="Utilizador:",
                     font=("Segoe UI", 10, "bold"),
                     bg="#0f172a", fg="#f8fafc").grid(row=0, column=0,
                                                       sticky=tk.W, padx=5, pady=5)
            e_user = tk.Entry(frame, font=("Segoe UI", 11), width=22,
                              bd=1, relief=tk.SOLID)
            e_user.grid(row=0, column=1, padx=5, pady=5, ipady=4)
            e_user.insert(0, self.utilizador.get("username", ""))
            e_user.focus()

            tk.Label(frame, text="Senha:",
                     font=("Segoe UI", 10, "bold"),
                     bg="#0f172a", fg="#f8fafc").grid(row=1, column=0,
                                                       sticky=tk.W, padx=5, pady=5)
            e_pass = tk.Entry(frame, font=("Segoe UI", 11), width=22,
                              bd=1, relief=tk.SOLID, show="*")
            e_pass.grid(row=1, column=1, padx=5, pady=5, ipady=4)

            msg_var = tk.StringVar()
            tk.Label(bloqueio, textvariable=msg_var,
                     font=("Segoe UI", 10),
                     bg="#0f172a", fg="#f87171").pack()

            def confirmar(event=None):
                u = e_user.get().strip().lower()
                p = e_pass.get()

                if not u or not p:
                    msg_var.set("Preencha utilizador e senha")
                    return

                try:
                    sucesso, dados = autenticar(u, p)
                except Exception as e:
                    msg_var.set(f"Erro: {e}")
                    return

                if not sucesso or not dados:
                    msg_var.set("Credenciais invalidas")
                    e_pass.delete(0, tk.END)
                    return

                # Autenticado - desbloquear
                bloqueio.destroy()
                self.bloqueado = False
                self.avisado = False
                self.ultima_atividade = datetime.now()

                # Re-mostrar janelas
                for j in janelas_abertas:
                    try:
                        j.deiconify()
                    except Exception:
                        pass

                # Se for outro utilizador, avisar
                if dados["id"] != self.utilizador.get("id"):
                    messagebox.showinfo("Sessao Continuada",
                        f"Bem-vindo(a), {dados['nome']}.\n\n"
                        f"Continua na sessao anterior.")

            e_user.bind("<Return>", lambda e: e_pass.focus())
            e_pass.bind("<Return>", confirmar)

            tk.Button(bloqueio, text="Desbloquear",
                      font=("Segoe UI", 12, "bold"),
                      bg="#16a34a", fg="white",
                      width=20, height=2, bd=0, cursor="hand2",
                      command=confirmar).pack(pady=20)

        except Exception as e:
            print(f"[Monitor] Erro ao bloquear: {e}")
            self.bloqueado = False

    def parar(self):
        """Para o monitor."""
        self.ativo = False
        if self.job_id:
            try:
                self.root.after_cancel(self.job_id)
            except Exception:
                pass

        for evt, _ in self._binds:
            try:
                self.root.unbind_all(evt)
            except Exception:
                pass