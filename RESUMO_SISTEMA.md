# JAM Soft — Manual Completo

**Versão:** 1.0.0
**Data:** 03/10/2026
**Autor:** Manuel Carlos Simão

---

## ÍNDICE

1. Visão Geral
2. Arquitectura
3. Funcionalidades
4. Segurança
5. Sincronização
6. Backup
7. Auto-Update
8. Numeração de Versões
9. Tecnologias
10. Início Rápido
11. Operação Diária (Funcionário)
12. Plataforma Web (CEO)
13. Manutenção
14. Problemas Comuns
15. Guia para Programadores
16. Estrutura de Pastas
17. Estado do Projecto
18. Contactos e Suporte

---

## 1. Visão Geral

O **JAM Soft** é um sistema completo de gestão de farmácias em Angola, composto por:

| Componente | Descrição | Tecnologia |
|------------|-----------|------------|
| **Aplicação Desktop** | Opera nas farmácias (vendas, stock, fiscal) | Python + Tkinter + SQLite |
| **Plataforma Web** | Painel do CEO (monitorização) | Streamlit + Supabase |
| **Base de Dados** | Dados centrais na nuvem | Supabase (PostgreSQL) |
| **Sincronização** | Automática a cada 5 minutos | HTTP REST |
| **Backup** | Triplo (local + OneDrive + Gmail) | Automático |
| **Auto-update** | Actualizações via GitHub | `git pull` automático |

---

## 2. Arquitectura
┌─────────────────────────────────────────────────────────┐
│                    FARMÁCIA (Desktop)                   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Aplicação JAM Soft (Python + Tkinter)           │   │
│  │  • PDV (vendas)                                   │   │
│  │  • Stock (com FEFO)                               │   │
│  │  • Caixa (turnos, TPA)                            │   │
│  │  • Fiscal (facturas, SAF-T)                       │   │
│  │  • IBT (transferências)                           │   │
│  └──────────────────────────────────────────────────┘   │
│                          │                               │
│                          ▼                               │
│  ┌──────────────────────────────────────────────────┐   │
│  │  SQLite Local (farmacia.db)                       │   │
│  └──────────────────────────────────────────────────┘   │
│                          │                               │
│         ┌────────────────┼────────────────┐              │
│         ▼                ▼                ▼              │
│    ┌─────────┐     ┌──────────┐    ┌──────────┐         │
│    │ Backups │     │ OneDrive │    │  GitHub  │         │
│    │ Locais  │     │ (externo)│    │ (update) │         │
│    └─────────┘     └──────────┘    └──────────┘         │
└─────────────────────────────────────────────────────────┘
                          │
                ┌─────────┴─────────┐
                │  Sincronização    │
                │   (5 em 5 min)    │
                └─────────┬─────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  NUVEM (Supabase)                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │  PostgreSQL (dados centrais)                      │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              PLATAFORMA WEB (Streamlit)                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Painel do CEO / Gestores                         │   │
│  │  • Resumo do País                                 │   │
│  │  • Ranking de Farmácias                           │   │
│  │  • Alertas                                        │   │
│  │  • Orçamentos (com IA)                            │   │
│  │  • Vendas, Stock, Perdas                          │   │
│  │  • Financeiro, Utilizadores                       │   │
│  │  • Transferências IBT                             │   │
│  │  • Chat IA                                        │   │
│  │  • Backup de Dados                                │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘

NICIAR_FARMACIA.bat:
[2/5] A criar backup da base de dados...
Backup criado: backups\farmacia_20261003.db

[Backup Externo] Copiado para:
C:\Users\manue\OneDrive\JAMSoft_Backups


**Rotação:** mantém últimos 30 dias

### 6.2 Plataforma Web

**Manual (botão):**

- Menu → Backup → Criar Backup
- Descarregar ficheiro `.enc` (encriptado)

**Automático (diário):**

- Corre às 23h (cron-job.org)
- Envia email com anexo para `simaom510@gmail.com`

---

## 7. Auto-Update

### 7.1 Como funciona

1. Programador faz correcção no VS Code
2. `git add .` / `git commit` / `git push`
3. Código vai para GitHub
4. Funcionário abre `INICIAR_FARMACIA.bat`
5. `.bat` faz `git pull` automaticamente
6. Código actualiza (dados NÃO são tocados)
7. Aplicação abre com nova versão

### 7.2 Vantagens

- Actualizações sem desinstalar
- Base de dados preservada
- Rollback fácil (tag anterior)
- Histórico completo (`git log`)

---

## 8. Numeração de Versões

### 8.1 Formato

v1.0.0
│ │ │
│ │ └─ PATCH (correcções)
│ └─── MINOR (novas funcionalidades)
└───── MAJOR (mudanças grandes


### 8.2 Ficheiros

| Ficheiro | Função |
|----------|--------|
| `VERSION` | Versão actual (texto) |
| `VERSION_HISTORY.md` | Histórico completo |
| `version.py` | Helper Python |

### 8.3 Exemplo no GitHub


### Ficheiros

| Ficheiro | Função |
|----------|--------|
| `VERSION` | Versão actual |
| `VERSION_HISTORY.md` | Histórico completo |
| `version.py` | Helper Python |

### Tags no GitHub

- `v1.0.0` — Versão inicial
- `v1.0.1` — Correcção
- `v1.1.0` — Nova funcionalidade
- `v2.0.0` — Mudança grande

---

## 9. Tecnologias

### Desktop

- **Python 3.12** — Linguagem
- **Tkinter** — Interface gráfica
- **SQLite** — Base de dados local
- **ReportLab** — PDFs
- **qrcode** — QR Codes
- **requests** — HTTP/sync

### Web

- **Streamlit** — Framework web
- **Supabase** — Base de dados nuvem
- **PostgreSQL** — Motor
- **Plotly** — Gráficos
- **Groq API** — IA (Chat)
- **ReportLab** — PDFs

### Infraestrutura

- **GitHub** — Código + auto-update
- **Streamlit Cloud** — Hospedagem web
- **Supabase** — Base de dados
- **OneDrive** — Backup externo
- **Gmail** — Backup por email
- **cron-job.org** — Agendamentos

---

## 10. Estado do Projecto

### Concluído

- PDV com pagamentos mistos
- Stock com FEFO
- Fecho de caixa
- Fiscal (facturas, PDFs)
- SAF-T básico
- IBT (transferências)
- Sincronização automática
- Backup triplo
- Auto-update
- Plataforma web completa
- Chat IA
- Backup web automático
- PWA no telemóvel
- Numeração de versões

### Pendente

- Certificação AGT (processo burocrático)
- Assinatura digital RSA nas facturas
- Comunicação tempo real com AGT
- QR Code oficial AGT
- Chave pública registada no Portal do Parceiro

---

## 11. Contactos

**Suporte Técnico:**
- Email: suporte@jamsoft.ao
- Telefone: +244 XXX XXX XXX

**Documentação:**
- `MANUAL_UTILIZACAO.md` — Como usar
- `VERSION_HISTORY.md` — Histórico
- `LEIA-ME.txt` — Instalação

---

**JAM Soft © 2026 — Todos os direitos reservados**