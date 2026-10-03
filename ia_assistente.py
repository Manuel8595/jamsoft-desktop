import threading
from datetime import datetime, timedelta
from tkinter import *
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

try:
    import ollama
    OLLAMA_DISPONIVEL = True
except ImportError:
    OLLAMA_DISPONIVEL = False

from database import (
    total_vendas_dia, produtos_estoque_baixo,
    produtos_validade_proxima, inventario_valorizado,
    resumo_vendas_periodo, produtos_mais_vendidos,
    progresso_mes, projecao_fecho_mes,
    estatisticas_devolucoes, saldo_atual_farmacia, caixa_aberto
)
from moeda import formatar_kz

COR_FUNDO = "#0f172a"
COR_CARD = "#1e293b"
COR_PRIMARIA = "#7c3aed"
COR_DOURADO = "#fbbf24"
COR_VERDE = "#10b981"
COR_TEXTO = "#f8fafc"
COR_TEXTO_SEC = "#94a3b8"
COR_BORDA = "#334155"

MODELO_IA = "llama3.2"


def _obter_contexto_dados():
    """Recolhe dados relevantes da farmacia para o contexto da IA."""
    contexto = {}
    
    try:
        contexto["vendas_hoje"] = total_vendas_dia()
    except Exception:
        contexto["vendas_hoje"] = 0
    
    try:
        contexto["caixa_aberto"] = caixa_aberto()
    except Exception:
        contexto["caixa_aberto"] = None
    
    try:
        contexto["saldo_farmacia"] = saldo_atual_farmacia()
    except Exception:
        contexto["saldo_farmacia"] = 0
    
    try:
        inv = inventario_valorizado()
        contexto["inventario"] = {
            "valor_custo": inv[0] if inv else 0,
            "valor_venda": inv[1] if inv else 0,
            "n_produtos": inv[2] if inv else 0,
            "total_unidades": inv[3] if inv else 0,
        }
    except Exception:
        contexto["inventario"] = {}
    
    try:
        contexto["produtos_estoque_baixo"] = produtos_estoque_baixo()[:10]
    except Exception:
        contexto["produtos_estoque_baixo"] = []
    
    try:
        contexto["produtos_validade"] = produtos_validade_proxima(90)[:10]
    except Exception:
        contexto["produtos_validade"] = []
    
    try:
        contexto["progresso_mes"] = progresso_mes()
    except Exception:
        contexto["progresso_mes"] = {}
    
    try:
        hoje = datetime.now().strftime("%Y-%m-%d")
        ontem = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        r_hoje = resumo_vendas_periodo(hoje, hoje)
        r_ontem = resumo_vendas_periodo(ontem, ontem)
        
        contexto["resumo_hoje"] = {
            "num_vendas": r_hoje[0] if r_hoje else 0,
            "total": r_hoje[1] if r_hoje else 0,
        }
        contexto["resumo_ontem"] = {
            "num_vendas": r_ontem[0] if r_ontem else 0,
            "total": r_ontem[1] if r_ontem else 0,
        }
    except Exception:
        contexto["resumo_hoje"] = {}
        contexto["resumo_ontem"] = {}
    
    try:
        contexto["devolucoes_mes"] = estatisticas_devolucoes()
    except Exception:
        contexto["devolucoes_mes"] = {}
    
    try:
        contexto["top_produtos"] = produtos_mais_vendidos(
            (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            datetime.now().strftime("%Y-%m-%d"),
            limite=10
        )
    except Exception:
        contexto["top_produtos"] = []
    
    return contexto


def _construir_system_prompt(contexto):
    """Constroi o prompt de sistema com os dados da farmacia."""
    vendas_hoje = formatar_kz(contexto.get("vendas_hoje", 0))
    
    estoque_baixo = contexto.get("produtos_estoque_baixo", [])
    estoque_txt = "\n".join([f"  - {p[0]} (atual: {p[2]}, minimo: {p[3]})" for p in estoque_baixo]) or "  (nenhum)"
    
    validade = contexto.get("produtos_validade", [])
    validade_txt = "\n".join([f"  - {p[0]} (vence {p[2]})" for p in validade]) or "  (nenhum)"
    
    prog = contexto.get("progresso_mes", {})
    prog_txt = (
        f"  Vendas mes: {formatar_kz(prog.get('vendido', 0))}\n"
        f"  Orcamento mes: {formatar_kz(prog.get('orcamento', 0))}\n"
        f"  Atingimento: {prog.get('percentagem', 0):.1f}%"
    ) if prog else "  (sem dados)"
    
    inv = contexto.get("inventario", {})
    inv_txt = (
        f"  Valor em stock (custo): {formatar_kz(inv.get('valor_custo', 0))}\n"
        f"  Valor em stock (venda): {formatar_kz(inv.get('valor_venda', 0))}\n"
        f"  Total de produtos: {inv.get('n_produtos', 0)}"
    ) if inv else "  (sem dados)"
    
    dev = contexto.get("devolucoes_mes", {})
    dev_txt = (
        f"  Total devolvido: {dev.get('total_n', 0)} (valor: {formatar_kz(dev.get('total_valor', 0))})"
    ) if dev else "  (sem dados)"
    
    top = contexto.get("top_produtos", [])
    top_txt = "\n".join([f"  - {p[0]}: {p[2]} unidades" for p in top[:5]]) or "  (sem dados)"
    
    return f"""Es o assistente IA da JAM Soft, sistema de gestao para farmacias em Angola.

Data e hora actual: {datetime.now().strftime("%Y-%m-%d %H:%M")}

=== DADOS DA FARMACIA ===

VENDA DE HOJE: {vendas_hoje}

INVENTARIO:
{inv_txt}

PROGRESSO DO MES:
{prog_txt}

STOCK BAIXO:
{estoque_txt}

VALIDADE PROXIMA:
{validade_txt}

TOP PRODUTOS:
{top_txt}

DEVOLUCOES DO MES:
{dev_txt}

=== INSTRUCOES ===

Responde sempre em PORTUGUES (Angola).
Sê conciso e directo.
Usa os dados acima.
Nunca inventes numeros.
Sugere accoes quando apropriado."""


class ChatIA:
    def __init__(self, parent, utilizador_logado):
        self.parent = parent
        self.utilizador = utilizador_logado
        self.contexto = None
        self.historico = []
        
        self.janela = Toplevel(parent)
        self.janela.title("JAM Soft - Assistente IA")
        self.janela.geometry("900x700")
        self.janela.configure(bg=COR_FUNDO)
        
        self.janela.update_idletasks()
        x = (self.janela.winfo_screenwidth() - 900) // 2
        y = (self.janela.winfo_screenheight() - 700) // 2
        self.janela.geometry(f"900x700+{x}+{y}")
        
        self._construir_interface()
        self._carregar_contexto()
    
    def _construir_interface(self):
        header = Frame(self.janela, bg=COR_PRIMARIA, height=70)
        header.pack(fill=X)
        header.pack_propagate(False)
        
        Label(header, text="🤖 Assistente IA",
              font=("Segoe UI", 18, "bold"),
              bg=COR_PRIMARIA, fg="white").pack(pady=(12, 0))
        
        status_txt = "✅ Ollama ligado" if OLLAMA_DISPONIVEL else "❌ Ollama nao instalado"
        status_cor = "#86efac" if OLLAMA_DISPONIVEL else "#fca5a5"
        
        Label(header, text=status_txt,
              font=("Segoe UI", 9, "italic"),
              bg=COR_PRIMARIA, fg=status_cor).pack()
        
        frame_chat = Frame(self.janela, bg=COR_FUNDO)
        frame_chat.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        self.txt_chat = ScrolledText(
            frame_chat, wrap=WORD,
            font=("Segoe UI", 11),
            bg=COR_CARD, fg=COR_TEXTO,
            insertbackground=COR_TEXTO,
            bd=0, padx=15, pady=15
        )
        self.txt_chat.pack(fill=BOTH, expand=True)
        self.txt_chat.config(state=DISABLED)
        
        self.txt_chat.tag_configure("autor", foreground=COR_DOURADO,
                                      font=("Segoe UI", 11, "bold"))
        
        frame_sug = Frame(self.janela, bg=COR_FUNDO)
        frame_sug.pack(fill=X, padx=15, pady=(0, 5))
        
        Label(frame_sug, text="Sugestoes:",
              font=("Segoe UI", 9, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO_SEC).pack(anchor=W)
        
        frame_botoes_sug = Frame(frame_sug, bg=COR_FUNDO)
        frame_botoes_sug.pack(fill=X, pady=5)
        
        sugestoes = [
            "Quantas vendas fiz hoje?",
            "Que produtos devo reabastecer?",
            "Como esta o mes?",
        ]
        
        for s in sugestoes:
            Button(frame_botoes_sug, text=s,
                   font=("Segoe UI", 9),
                   bg=COR_BORDA, fg=COR_TEXTO,
                   bd=0, cursor="hand2", padx=10, pady=4,
                   command=lambda txt=s: self._enviar_sugestao(txt)
                   ).pack(side=LEFT, padx=3)
        
        frame_input = Frame(self.janela, bg=COR_CARD, height=60)
        frame_input.pack(fill=X, padx=15, pady=(5, 15))
        frame_input.pack_propagate(False)
        
        self.entry_pergunta = Entry(
            frame_input,
            font=("Segoe UI", 12),
            bg=COR_CARD, fg=COR_TEXTO,
            insertbackground=COR_TEXTO,
            bd=0
        )
        self.entry_pergunta.pack(side=LEFT, fill=BOTH, expand=True, padx=15, pady=15)
        self.entry_pergunta.bind('<Return>', lambda e: self._enviar())
        self.entry_pergunta.focus()
        
        Button(frame_input, text="➤",
               font=("Segoe UI", 14, "bold"),
               bg=COR_PRIMARIA, fg="white",
               bd=0, cursor="hand2", width=4,
               command=self._enviar
               ).pack(side=RIGHT, padx=10, pady=10)
    
    def _carregar_contexto(self):
        self._escrever("🤖", "A carregar dados da farmacia...\n")
        
        def carregar():
            try:
                self.contexto = _obter_contexto_dados()
                self.janela.after(0, self._contexto_pronto)
            except Exception as e:
                self.janela.after(0, lambda: self._erro_contexto(str(e)))
        
        threading.Thread(target=carregar, daemon=True).start()
    
    def _contexto_pronto(self):
        v = formatar_kz(self.contexto.get("vendas_hoje", 0))
        n_prod = self.contexto.get("inventario", {}).get("n_produtos", 0)
        msg = (
            f"Dados carregados!\n\n"
            f"Vendas de hoje: {v}\n"
            f"Produtos em stock: {n_prod}\n\n"
            f"Podes fazer perguntas! Exemplos:\n"
            f"  - Quantas vendas fiz hoje?\n"
            f"  - Que produtos devo reabastecer?\n"
            f"  - Como esta o mes?\n\n"
        )
        self._escrever("🤖", msg)
    
    def _erro_contexto(self, erro):
        self._escrever("❌", f"Erro ao carregar dados: {erro}\n")
    
    def _enviar_sugestao(self, texto):
        self.entry_pergunta.delete(0, END)
        self.entry_pergunta.insert(0, texto)
        self._enviar()
    
    def _enviar(self):
        pergunta = self.entry_pergunta.get().strip()
        if not pergunta:
            return
        
        if not OLLAMA_DISPONIVEL:
            messagebox.showerror(
                "Ollama nao instalado",
                "Para usar a IA, precisas do Ollama.\n\n"
                "Vai a https://ollama.com/download\n"
                "Instala e corre: ollama pull llama3.2"
            )
            return
        
        self.entry_pergunta.delete(0, END)
        self._escrever("👤", f"{pergunta}\n")
        self._escrever("🤖", "A pensar...\n")
        
        def processar():
            try:
                system_prompt = _construir_system_prompt(self.contexto or {})
                
                mensagens = [{"role": "system", "content": system_prompt}]
                mensagens.extend(self.historico[-6:])
                mensagens.append({"role": "user", "content": pergunta})
                
                resposta = ollama.chat(
                    model=MODELO_IA,
                    messages=mensagens,
                    options={"num_predict": 300}
                )
                
                texto_resposta = resposta["message"]["content"]
                
                self.historico.append({"role": "user", "content": pergunta})
                self.historico.append({"role": "assistant", "content": texto_resposta})
                
                self.janela.after(0, lambda: self._mostrar_resposta(texto_resposta))
            except Exception as e:
                self.janela.after(0, lambda: self._erro_resposta(str(e)))
        
        threading.Thread(target=processar, daemon=True).start()
    
    def _remover_pensar(self):
        self.txt_chat.config(state=NORMAL)
        conteudo = self.txt_chat.get("1.0", END)
        if conteudo.endswith("A pensar...\n"):
            self.txt_chat.delete("end-2l", "end-1l")
        self.txt_chat.config(state=DISABLED)
    
    def _mostrar_resposta(self, texto):
        self._remover_pensar()
        self._escrever("🤖", f"{texto}\n\n")
    
    def _erro_resposta(self, erro):
        self._remover_pensar()
        self._escrever("❌", f"Erro: {erro}\n\n")
    
    def _escrever(self, autor, texto):
        self.txt_chat.config(state=NORMAL)
        self.txt_chat.insert(END, f"{autor} ", "autor")
        self.txt_chat.insert(END, texto)
        self.txt_chat.see(END)
        self.txt_chat.config(state=DISABLED)


def abrir_assistente_ia(parent, utilizador_logado):
    """Abre o assistente IA."""
    if not OLLAMA_DISPONIVEL:
        resposta = messagebox.askyesno(
            "Ollama nao instalado",
            "O Ollama nao esta instalado.\n\n"
            "O assistente IA precisa do Ollama.\n\n"
            "Queres ver as instrucoes?"
        )
        if resposta:
            messagebox.showinfo(
                "Como instalar",
                "1. Vai a https://ollama.com/download\n"
                "2. Instala o Ollama para Windows\n"
                "3. No PowerShell corre:\n\n"
                "   ollama pull llama3.2\n\n"
                "4. Reinicia a app"
            )
        return
    
    ChatIA(parent, utilizador_logado)