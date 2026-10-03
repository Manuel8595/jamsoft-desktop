from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
     Table, TableStyle, Preformatted, Image as RLImage)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime

# Cores do tema
VERDE = HexColor("#16a34a")
VERDE_ESCURO = HexColor("#14532d")
VERDE_CLARO = HexColor("#f0fdf4")
CINZA = HexColor("#6b7280")
LARANJA = HexColor("#ea580c")
VERMELHO = HexColor("#dc2626")
AZUL = HexColor("#0891b2")
ROXO = HexColor("#7c3aed")

styles = getSampleStyleSheet()

titulo_capa = ParagraphStyle('TituloCapa', parent=styles['Title'],
                              fontSize=30, textColor=VERDE, alignment=TA_CENTER,
                              spaceAfter=20, leading=38)

subtitulo_capa = ParagraphStyle('SubCapa', parent=styles['Normal'],
                                 fontSize=14, textColor=VERDE_ESCURO,
                                 alignment=TA_CENTER, spaceAfter=10)

h1 = ParagraphStyle('H1', parent=styles['Heading1'],
                     fontSize=20, textColor=VERDE, spaceBefore=20, spaceAfter=12,
                     borderPadding=5, leading=24)

h2 = ParagraphStyle('H2', parent=styles['Heading2'],
                     fontSize=15, textColor=VERDE_ESCURO,
                     spaceBefore=14, spaceAfter=8, leading=18)

h3 = ParagraphStyle('H3', parent=styles['Heading3'],
                     fontSize=12, textColor=LARANJA,
                     spaceBefore=10, spaceAfter=6, leading=16)

corpo = ParagraphStyle('Corpo', parent=styles['Normal'],
                        fontSize=11, textColor=HexColor("#1f2937"),
                        alignment=TA_JUSTIFY, spaceAfter=8, leading=15)

item = ParagraphStyle('Item', parent=corpo, leftIndent=20, bulletIndent=10, spaceAfter=4)

codigo = ParagraphStyle('Codigo', parent=styles['Code'],
                         fontSize=8.5, textColor=VERDE_ESCURO,
                         backColor=VERDE_CLARO, borderPadding=5, leading=11)

alerta = ParagraphStyle('Alerta', parent=corpo,
                         textColor=VERMELHO, fontSize=11,
                         borderColor=VERMELHO, borderWidth=1,
                         borderPadding=8, backColor=HexColor("#fef2f2"))

doc = SimpleDocTemplate(
    "Maquete_Sistema_Farmacia_Angola.pdf",
    pagesize=A4,
    rightMargin=2*cm, leftMargin=2*cm,
    topMargin=2*cm, bottomMargin=2*cm,
    title="Maquete conceptual - Sistema de Farmácia Angola",
    author="Projeto Farmacia-Inteligente"
)

elementos = []

# ============ CAPA ============
elementos.append(Spacer(1, 4*cm))
elementos.append(Paragraph("JAM SOFT", ParagraphStyle('Marca', fontSize=24,
                                                       textColor=VERDE_ESCURO,
                                                       alignment=TA_CENTER)))
elementos.append(Spacer(1, 0.5*cm))
elementos.append(Paragraph("Sistema de Farmácia Inteligente", titulo_capa))
elementos.append(Paragraph("Maquete conceptual - proposta de arquitectura", subtitulo_capa))
elementos.append(Spacer(1, 1*cm))
elementos.append(Paragraph("Angola | Kwanza (Kz) | IVA por produto | Aplicacao local", subtitulo_capa))
elementos.append(Spacer(1, 0.7*cm))
elementos.append(Paragraph(
    "AVISO: esta maquete nao comprova funcionalidades do programa instalado, "
    "seguranca em rede, integracao com a AGT ou certificacao fiscal. Consulte "
    "ESTADO_DO_PROJECTO.txt para o estado verificado.", alerta))
elementos.append(Spacer(1, 1.2*cm))
elementos.append(Paragraph(f"Versão 2.0 - {datetime.now().strftime('%d/%m/%Y')}", 
                            ParagraphStyle('Data', alignment=TA_CENTER, fontSize=10, textColor=CINZA)))
elementos.append(PageBreak())

# ============ SUMÁRIO ============
elementos.append(Paragraph(" Sumário", h1))
sumario = [
    "1. Visão Geral",
    "2. Arquitetura em Camadas",
    "3. Arquitetura de Rede Segura ",
    "4. Módulos do Sistema (10 módulos)",
    "5. Segurança - 5 Camadas de Proteção ",
    "6. Stack Tecnológica",
    "7. Estrutura de Pastas",
    "8. Integração da IA",
    "9. Fluxo Diário de Uso",
    "10. Fluxo de Login Seguro na Rede",
    "11. Roadmap de Desenvolvimento",
    "12. Checklist de Segurança",
    "13. Preview do Layout",
    "14. Status Atual do Projeto",
    "15. Próximos Passos",
]
for s in sumario:
    elementos.append(Paragraph(f"- {s}", item))
elementos.append(PageBreak())

# ============ 1. VISÃO GERAL ============
elementos.append(Paragraph("1.  Visão Geral", h1))
elementos.append(Paragraph(
    "Esta maquete apresenta uma proposta para um sistema de farmácia. Os "
    "componentes de rede, API, IA e segurança descritos nas páginas seguintes "
    "são ideias de projecto, nao funcionalidades verificadas no pacote actual. "
    "A aplicação entregue funciona localmente e mantém a sincronizacao cloud desligada.", corpo))
elementos.append(Paragraph("Características principais:", h3))
for c in [
    "Aplicação desktop local em Python",
    "Arquitectura cliente-servidor descrita como proposta, nao validada",
    "HTTPS e JWT descritos como requisitos de projecto, nao verificados nesta aplicação",
    "IVA classificado por produto; confirmar o regime e o enquadramento aplicáveis",
    "Integracao e certificacao fiscal AGT nao confirmadas neste pacote",
    "A versão entregue funciona localmente; a sincronizacao cloud está desligada",
]:
    elementos.append(Paragraph(f" {c}", item))
elementos.append(PageBreak())

# ============ 2. ARQUITETURA EM CAMADAS ============
elementos.append(Paragraph("2.  Arquitetura em Camadas", h1))

arq_texto = """

              CAMADA DE APRESENTAÇÃO                       
   PDV Desktop  |  Painel Web  |  App Mobile (futuro)     

              CAMADA DE SEGURANÇA                        
   HTTPS/TLS  |  JWT  |  Rate Limit  |  Auditoria         

                  CAMADA DE IA                             
   Assistente | Previsão | Alertas | Análise              

               CAMADA DE NEGÓCIO                           
   Estoque | Vendas | Financeiro | Lotes | Clientes       

                 CAMADA DE DADOS                           
   PostgreSQL (rede) | SQLite (local) | Backup cripto     

"""
elementos.append(Preformatted(arq_texto, codigo))
elementos.append(PageBreak())

# ============ 3. ARQUITETURA DE REDE ============
elementos.append(Paragraph("3.  Arquitetura de Rede Segura", h1))

elementos.append(Paragraph(
    "Quando o sistema é usado por vários computadores, o banco <b>não pode ficar "
    "exposto diretamente</b> na rede. A solução correta é uma arquitetura "
    "<b>cliente-servidor</b> com uma API central.", corpo))

rede_texto = """
       
           SERVIDOR DA FARMÁCIA    
                                    
             
           API (FastAPI)          
           Autenticação JWT       
           Regras de negócio      
             
                                    
             
           PostgreSQL             
           (só acesso local)      
             
       
                     HTTPS (porta 443)
                     Autenticação JWT
                     Criptografia TLS
                    
       
                               
                               
   [PC Caixa]   [PC Balcão]  [Notebook]
"""
elementos.append(Preformatted(rede_texto, codigo))

elementos.append(Paragraph("Vantagens dessa arquitetura:", h3))
for v in [
    "O banco <b>nunca</b> é exposto diretamente na rede",
    "Só a API fala com o banco (isolamento total)",
    "Toda comunicação é criptografada com HTTPS/TLS",
    "Autenticação com JWT (token com validade de 15 min)",
    "Cada PC é um cliente que faz requisições seguras",
    "Funciona com Wi-Fi ou cabo sem corromper dados",
    "Cada usuário tem seu nível de permissão",
    "Todas as ações são registradas em log de auditoria",
]:
    elementos.append(Paragraph(f" {v}", item))

elementos.append(PageBreak())

# ============ 4. MÓDULOS ============
elementos.append(Paragraph("4.  Módulos do Sistema", h1))

modulos = [
    ("4.1 Cadastros", ["Produtos (medicamentos, cosméticos, material)",
                        "Princípios ativos e interações medicamentosas",
                        "Laboratórios, Fornecedores, Clientes",
                        "Funcionários (login e permissões)",
                        "Convênios / Seguros de saúde"]),
    ("4.2 Estoque", ["Entrada por nota fiscal",
                      "Saída (venda, perda, vencimento, doação)",
                      "Controle de lotes (PEPS)",
                      "Estoque mínimo por produto",
                      "Transferência entre filiais",
                      "Inventário / contagem física"]),
    ("4.3 Vendas (PDV)", ["Leitura de código de barras",
                           "Vendas por prescrição médica",
                           "Vendas de controlados (receita digital)",
                           "Pagamentos: Dinheiro, Multicaixa, PIX",
                            "IVA geral 14%; isenção para medicamentos destinados exclusivamente a fins terapêuticos ou profilácticos",
                           "Cálculo de troco, descontos, cancelamento",
                           "Emissão de cupom / recibo"]),
    ("4.4 Financeiro", ["Caixa diário (abertura, sangria, fechamento)",
                         "Contas a pagar (fornecedores)",
                         "Contas a receber (convênios)",
                         "Fluxo de caixa, lucro/prejuízo"]),
    ("4.5 Fiscal", ["IVA classificado por produto; confirmar o regime aplicável",
                     "Facturas emitidas localmente; integração oficial AGT não implementada",
                     "Exportação SAF-T não verificada neste pacote",
                     "Livro de registo local"]),
    ("4.6 Validade", ["Alerta em 30 / 60 / 90 dias",
                       "Bloqueio de venda de vencidos",
                       "Sugestão de promoção",
                       "Devolução ao fornecedor"]),
    ("4.7 IA ", ["Previsão de demanda",
                    "Alerta inteligente de validade",
                    "Sugestão de reposição",
                    "Análise de vendas em linguagem natural",
                    "Chatbot interno para o farmacêutico",
                    "Detecção de padrões e fraudes"]),
    ("4.8 Relatórios ", ["Vendas por período (dia/semana/mês/ano)",
                            "Produtos mais vendidos",
                            "Margem de lucro por produto",
                            "Fluxo de clientes por horário",
                            "Curva ABC (produtos que mais faturam)"]),
    ("4.9 Segurança ", ["Login com senha criptografada (bcrypt)",
                           "Níveis: admin, farmacêutico, caixa, estagiário",
                           "Log de auditoria (quem fez o quê)",
                           "Backup automático local + nuvem",
                           "HTTPS + JWT para uso em rede",
                           "Criptografia do banco"]),
    ("4.10 Integrações ", ["Leitor de código de barras (USB)",
                              "Impressora térmica de cupom",
                              "Balança digital",
                              "API para convênios"]),
]

for titulo_mod, itens in modulos:
    elementos.append(Paragraph(titulo_mod, h2))
    for i in itens:
        elementos.append(Paragraph(f"- {i}", item))

elementos.append(PageBreak())

# ============ 5. SEGURANÇA - 5 CAMADAS ============
elementos.append(Paragraph("5.  Segurança - 5 Camadas de Proteção", h1))

elementos.append(Paragraph(
    "Segurança em rede não é uma coisa única. É feita de <b>camadas sobrepostas</b>. "
    "Se uma falhar, as outras seguram.", corpo))

camadas = [
    ("Camada 1 - Física", [
        "Roteador com senha forte (nunca a padrão de fábrica)",
        "Wi-Fi com WPA3 (ou WPA2 se o roteador for antigo)",
        "Rede separada para clientes (VLAN)",
        "Cabo em vez de Wi-Fi (mais seguro)",
        "Desativar WPS, UPnP e acesso remoto do roteador",
    ]),
    ("Camada 2 - Rede (Firewall)", [
        "Firewall no servidor: só libera a porta 443 (HTTPS)",
        "PostgreSQL aceita conexões somente de localhost",
        "Nunca expor o banco direto na rede",
        "Servidor com IP fixo local",
        "VPN (WireGuard) se houver acesso remoto",
    ]),
    ("Camada 3 - Aplicação (API)", [
        "HTTPS obrigatório (certificado SSL/TLS)",
        "Autenticação JWT (token válido por 15 min)",
        "Rate limiting: máximo 5 tentativas de login por minuto",
        "Validação de toda entrada (nunca confiar no cliente)",
        "CORS restrito aos IPs da farmácia",
        "Log de todas as requisições",
    ]),
    ("Camada 4 - Banco de Dados", [
        "PostgreSQL com senha forte",
        "Usuário da app sem permissões DROP/CREATE",
        "Criptografia em repouso",
        "Backup criptografado (AES-256) antes da nuvem",
        "Prazo de retenção conforme a obrigação aplicável (confirmar com AGT/contabilista)",
    ]),
    ("Camada 5 - Senhas e Criptografia", [
        "Senhas com bcrypt (cost factor 12)",
        "JWT assinado com chave secreta forte",
        "Chave secreta em variável de ambiente (.env)",
        "Sessão com timeout de 15 min de inatividade",
        "Bloqueio após 3 tentativas erradas de login",
    ]),
]

for titulo_c, itens_c in camadas:
    elementos.append(Paragraph(titulo_c, h2))
    for i in itens_c:
        elementos.append(Paragraph(f" {i}", item))

elementos.append(PageBreak())

# ============ 6. STACK ============
elementos.append(Paragraph("6.  Stack Tecnológica", h1))

stack_data = [
    ["Camada", "Tecnologia", "Motivo"],
    ["Linguagem", "Python 3.12", "Simples, robusto, com IA"],
    ["Interface Desktop", "Tkinter / CustomTkinter", "Nativo, sem complicações"],
    ["Servidor API", "FastAPI", "Rápido, seguro, moderno"],
    ["Autenticação", "JWT + bcrypt", "Padrão da indústria"],
    ["Banco (rede)", "PostgreSQL", "Multi-usuário, alta performance"],
    ["Banco (local)", "SQLite", "Zero configuração"],
    ["HTTPS", "Certificado SSL/TLS", "Comunicação criptografada"],
    ["IA", "Ollama + Qwen/Llama", "Roda local, sem custo de API"],
    ["Gráficos", "Matplotlib / Plotly", "Relatórios visuais"],
    ["PDF", "ReportLab", "Cupons e relatórios"],
    ["Backup", "shutil + Google Drive API", "Backup criptografado"],
    ["Empacotamento", "PyInstaller", "Gerar executável .exe"],
    ["Containers", "Docker (opcional)", "Facilita deploy no servidor"],
]

tabela = Table(stack_data, colWidths=[4*cm, 5*cm, 6*cm])
tabela.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), VERDE),
    ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#ffffff")),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#d1d5db")),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#ffffff"), VERDE_CLARO]),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
elementos.append(tabela)
elementos.append(PageBreak())

# ============ 7. ESTRUTURA DE PASTAS ============
elementos.append(Paragraph("7.  Estrutura de Pastas", h1))

estrutura = """farmacia-rede/
 servidor/                    # Roda no servidor da farmácia
    api/
       main.py              # FastAPI
       auth.py              # Login / JWT
       routes/              # Endpoints
       security.py          # Middleware de segurança
    database/
       models.py            # PostgreSQL
    .env                     # Chaves secretas (NUNCA no Git)
    run.py

 cliente/                     # Roda em cada PC da farmácia
    ui/
       login.py             # Tela de login
       pdv.py               # PDV
       ...
    api_client.py            # Fala com o servidor
    run.py

 docs/
    seguranca.md

 README.md
"""
elementos.append(Preformatted(estrutura, codigo))
elementos.append(PageBreak())

# ============ 8. IA ============
elementos.append(Paragraph("8.  Integração da IA", h1))

elementos.append(Paragraph("IA 1 - Previsão de Demanda", h3))
elementos.append(Paragraph(
    "Usa histórico de vendas + modelo preditivo para estimar quanto será "
    "vendido nos próximos 30 dias, sugerindo quantidade ideal de compra.", corpo))

elementos.append(Paragraph("IA 2 - Alerta Inteligente de Validade", h3))
elementos.append(Paragraph(
    "Compara a data de validade com a velocidade de venda do produto. "
    "Se for sobrar estoque antes do vencimento, sugere promoção ou devolução.", corpo))

elementos.append(Paragraph("IA 3 - Chatbot do Farmacêutico", h3))
elementos.append(Paragraph(
    "Assistente em linguagem natural via Ollama + Qwen. O farmacêutico pergunta "
    "coisas como: <i>\"Quanto vendi de dipirona este mês?\"</i> e a IA responde.", corpo))

elementos.append(Paragraph("IA 4 - Detecção de Anomalias e Fraudes", h3))
elementos.append(Paragraph(
    "Monitora padrões suspeitos: cancelamentos excessivos por um operador, "
    "descontos fora do comum, vendas fora do horário. Alerta o administrador.", corpo))

elementos.append(Paragraph("IA 5 - Análise Preditiva de Faturamento", h3))
elementos.append(Paragraph(
    "Prevê o faturamento do próximo mês, identifica produtos em queda e "
    "sugere ações de marketing.", corpo))

elementos.append(PageBreak())

# ============ 9. FLUXO DIÁRIO ============
elementos.append(Paragraph("9.  Fluxo Diário de Uso", h1))

fluxo = [
    ("Manhã - Abertura", [
        "Farmacêutico faz login no sistema (com senha)",
        "IA mostra resumo: produtos vencendo e estoque baixo",
        "Abre o caixa (informa valor inicial)",
    ]),
    ("Durante o dia - Vendas", [
        "Cliente chega, operador abre PDV",
        "Escaneia produtos (IVA automático)",
        "Recebe pagamento, imprime cupom, atualiza estoque",
        "Toda venda é enviada para o servidor via HTTPS",
    ]),
    ("Tarde - Gestão", [
        "Farmacêutico pergunta à IA: 'Qual produto mais vendeu hoje?'",
        "IA responde em linguagem natural",
        "Sistema sugere reposição baseada em previsão",
    ]),
    ("Fim do dia - Fechamento", [
        "Fecha o caixa (confere valores)",
        "IA gera relatório inteligente do dia",
        "Backup criptografado enviado para nuvem",
    ]),
]

for titulo_f, passos in fluxo:
    elementos.append(Paragraph(titulo_f, h2))
    for p in passos:
        elementos.append(Paragraph(f" {p}", item))

elementos.append(PageBreak())

# ============ 10. FLUXO DE LOGIN SEGURO ============
elementos.append(Paragraph("10.  Fluxo de Login Seguro na Rede", h1))

login_texto = """1. [PC Caixa]  -> envia usuário + senha para [Servidor] via HTTPS
2. [Servidor]  -> verifica senha com bcrypt
3. [Servidor]  -> gera token JWT (válido por 15 min)
4. [Servidor]  -> devolve token para o PC
5. [PC Caixa]  -> guarda o token na memória (nunca em disco)
6. [PC Caixa]  -> em cada ação, envia o token no cabeçalho
7. [Servidor]  -> valida o token antes de responder
8. [Servidor]  -> se expirou, pede login de novo
"""
elementos.append(Preformatted(login_texto, codigo))

elementos.append(Paragraph(
    " <b>Importante:</b> a senha nunca é guardada no PC. "
    "Só o token, e mesmo assim, temporário.", alerta))

elementos.append(PageBreak())

# ============ 11. ROADMAP ============
elementos.append(Paragraph("11.  Roadmap de Desenvolvimento", h1))

roadmap = [
    ["Fase", "Duração", "O que fazer"],
    ["Fase 1", "1 semana", " Base (cadastro, PDV, estoque, IVA)"],
    ["Fase 2", "1 semana", "Login + permissões + auditoria"],
    ["Fase 3", "2 semanas", "Relatórios (PDF, Excel) + gráficos"],
    ["Fase 4", "2 semanas", "Financeiro (caixa, contas)"],
    ["Fase 5", "3 semanas", "IA local (Ollama) + chatbot"],
    ["Fase 6", "2 semanas", "Backup automático + nuvem"],
    ["Fase 7", "2 semanas", "Impressão de cupom + código de barras"],
    ["Fase 8", "3 semanas", " Migração para Rede (API + PostgreSQL + HTTPS)"],
    ["Fase 9", "2 semanas", "Hardening de segurança + testes"],
    ["Fase 10", "2 semanas", "Empacotamento (.exe) + deploy"],
    ["Fase 11", "Contínuo", "Melhorias + IA avançada"],
]

tabela2 = Table(roadmap, colWidths=[2.5*cm, 3*cm, 9.5*cm])
tabela2.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), VERDE),
    ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#ffffff")),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#d1d5db")),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#ffffff"), VERDE_CLARO]),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
elementos.append(tabela2)
elementos.append(Spacer(1, 0.5*cm))
elementos.append(Paragraph("<b>Tempo total estimado:</b> ~5 meses (ritmo part-time).", corpo))
elementos.append(PageBreak())

# ============ 12. CHECKLIST DE SEGURANÇA ============
elementos.append(Paragraph("12.  Checklist de Segurança", h1))

elementos.append(Paragraph("Antes de colocar em rede, verifique:", corpo))

checklist = [
    "O roteador tem senha forte (não a padrão de fábrica)?",
    "O Wi-Fi usa WPA3 (ou WPA2)?",
    "Existe uma rede separada para clientes?",
    "O servidor tem IP fixo na rede?",
    "O firewall do servidor só libera a porta 443 (HTTPS)?",
    "O PostgreSQL só aceita conexões de localhost?",
    "As senhas dos usuários são fortes (8+ caracteres, com símbolos)?",
    "O .env com as chaves secretas NÃO está no Git?",
    "O backup é criptografado antes de subir para nuvem?",
    "O log de auditoria está ativo?",
    "O certificado HTTPS está instalado?",
    "Existe plano de resposta a incidentes?",
]
for c in checklist:
    elementos.append(Paragraph(f" {c}", item))

elementos.append(PageBreak())

# ============ 13. PREVIEW LAYOUT ============
elementos.append(Paragraph("13.  Preview do Layout", h1))

preview = """
   FARMÁCIA ANGOLA - Sistema Inteligente        admin  

                                                            
   PDV       ESTOQUE      FINANCEIRO                 
                                                            
   PRODUTOS  VALIDADE     RELATÓRIOS                 
                                                            
    
     ASSISTENTE IA                                     
    Você: "Quanto vendi esta semana?"                    
    IA: "Vendeu Kz 485.000,00 - 12% acima da semana     
         passada. Destaque: Dipirona."                   
    
                                                            
   Alerta IA: 3 produtos vencem em 30 dias. Sugiro       
     promoção de "X" para não perder Kz 45.000,00.         
                                                            
   Pré-visualização conceptual | dados fictícios | não é o ecrã actual do programa

"""
elementos.append(Preformatted(preview, codigo))
elementos.append(PageBreak())

# ============ 14. ESTADO VERIFICADO ============
elementos.append(Paragraph("14. Estado Verificado em 01/10/2026", h1))
elementos.append(Paragraph("Este resumo descreve apenas o que foi verificado nesta entrega:", corpo))

for s in [
    "Venda: 13 verificações isoladas passaram para stock, FEFO, lotes, IVA e rollback.",
    "Base SQLite: integridade OK e nenhuma violação de chave estrangeira.",
    "Histórico: 91 de 115 vendas estão sem linhas; 31 backups não recuperam esses detalhes.",
    "Supabase: a aplicação local não sincroniza; o bloqueio no servidor ainda não foi aplicado.",
    "AGT: integração oficial e certificação do software não foram confirmadas.",
]:
    elementos.append(Paragraph(f"{s}", item))

elementos.append(Spacer(1, 0.5*cm))
elementos.append(Paragraph(
    "Consulte ESTADO_DO_PROJECTO.txt para os limites e próximos passos. Este resumo não é uma declaração de conformidade fiscal.", corpo))
elementos.append(PageBreak())

# ============ 15. PRÓXIMOS PASSOS ============
elementos.append(Paragraph("15.  Próximos Passos Recomendados", h1))

for i, s in enumerate([
    "Login e permissões (segurança primeiro)",
    "Backup automático criptografado (proteger os dados)",
    "Impressão de cupom (profissionalizar o PDV)",
    "Relatórios em PDF (gestão)",
    "IA com Ollama (o diferencial)",
    "Migração para rede (API + PostgreSQL + HTTPS)",
    "Hardening final (rate limit, detecção de anomalias)",
], 1):
    elementos.append(Paragraph(f"<b>{i}.</b> {s}", item))

elementos.append(Spacer(1, 1.5*cm))
elementos.append(Paragraph("- Fim da Maquete -", 
    ParagraphStyle('Fim', alignment=TA_CENTER, fontSize=14, 
                    textColor=VERDE, fontName='Helvetica-Bold')))

elementos.append(Spacer(1, 0.5*cm))
elementos.append(Paragraph(
    "Sistema de Farmácia Inteligente - Angola | Maquete conceptual",
    ParagraphStyle('Rodape', alignment=TA_CENTER, fontSize=10, textColor=CINZA)))

# ============ GERAR PDF ============
doc.build(elementos)
print(" PDF gerado com sucesso: Maquete_Sistema_Farmacia_Angola.pdf")
