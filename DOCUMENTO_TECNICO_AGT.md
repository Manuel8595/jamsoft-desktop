# DOCUMENTO TÉCNICO — JAM SOFT

## Sistema de Gestão de Farmácias

---

**Versão:** 1.0.4
**Data:** 12/10/2026
**Empresa:** TRI JAM COMÉRCIO E PRESTAÇÃO DE SERVIÇO
**NIF:** 5003507920
**Sede:** Província de Luanda, Município de Kilamba Kiaxi, Comuna de Nova Vida, Bairro Projecto, Rua Fubu, Casa s/nº, junto ao Descontão
**Telefone:** +244 923 888 338

---

## 1. IDENTIFICAÇÃO DO SOFTWARE

| Campo | Valor |
|---|---|
| **Nome** | JAM Soft — Sistema de Gestão de Farmácias |
| **Versão** | 1.0.4 |
| **Data** | Outubro 2026 |
| **Tipo** | Aplicação Desktop + Plataforma Web + Painel Master |
| **Linguagem** | Python 3.12 |
| **Base de Dados** | SQLite (local) + Supabase PostgreSQL (nuvem) |
| **Sistema Operativo** | Windows 10 / 11 |
| **Arquitectura** | Multi-empresa (SaaS-ready) |
| **Produtor** | TRI JAM COMÉRCIO E PRESTAÇÃO DE SERVIÇO |

---

## 2. DESCRIÇÃO FUNCIONAL

O JAM Soft é um sistema completo de gestão de farmácias, composto por três componentes integrados:

### 2.1 Aplicação Desktop (Farmácia)

Corre no PC da farmácia. Funciona offline e sincroniza automaticamente.

**Módulos principais:**

- **PDV (Ponto de Venda)** — vendas rápidas com suporte a:
  - Pagamentos em dinheiro, Multicaixa e transferência
  - Pagamentos mistos
  - Descontos
  - Devoluções
- **Gestão de Stock com FEFO** (First Expired, First Out)
  - Controlo por lotes
  - Alertas de validade próxima
  - Alertas de stock mínimo
- **Gestão de Caixa e Turnos**
  - Abertura e fecho de caixa
  - Sangrias e reforços
  - Conciliação bancária
  - Fecho de dia
- **Módulo Fiscal**
  - Emissão de facturas (A4 e Térmica 80mm)
  - Facturas pró-forma
  - Notas de crédito
  - Exportação SAF-T (AO)
  - Hash SHA-256 por documento
  - QR Code para verificação
- **Inventário**
  - Contagens físicas
  - Ajustes automáticos
- **Compras e Fornecedores**
- **Clientes e Categorias**
- **Transferências IBT** (entre filiais)
- **Relatórios**
  - Vendas (dia/mês/ano)
  - Stock e FEFO
  - Fecho de caixa
  - Auditoria
- **Metas e Orçamentos com IA**
- **Backup Automático** (local + OneDrive)
- **Sincronização Automática** com a nuvem (5 em 5 minutos)
- **Sistema de Activação por Chave** (SaaS-ready)

### 2.2 Plataforma Web (CEO)

Monitorização remota multi-farmácia.

**Funcionalidades:**

- Login seguro (Supabase Auth)
- Dashboard com resumo do país
- Ranking de farmácias
- Alertas automáticos (stock baixo, validades, sem comunicação)
- Análise de vendas, stock, perdas
- Gestão financeira e depósitos
- Chat IA (Groq API)
- Backup encriptado (AES-256)
- PWA instalável no telemóvel

### 2.3 Painel Master (Gestão)

Gestão de chaves de activação e clientes.

**Funcionalidades:**

- Criação de chaves de activação
- Listagem e filtros avançados
- Vista agrupada por empresa (NIF)
- Histórico de validações
- Estatísticas e gráficos
- Revogação de chaves

---

## 3. ARQUITECTURA TÉCNICA

### 3.1 Componentes

- **Aplicação Desktop** — corre no PC da farmácia
  - Interface: Tkinter (Python)
  - Base de dados local: SQLite
  - Comunicação: requests (HTTPS)
  - Empacotamento: ZIP + INSTALAR.bat

- **Plataforma Web (CEO)** — Streamlit Cloud
  - Interface: Streamlit
  - Base de dados: Supabase PostgreSQL
  - Autenticação: Supabase Auth
  - URL: https://jamsoft-plataforma-nthcjcruax7wmg9rqxr4qz.streamlit.app

- **Painel Master** — Streamlit Cloud
  - Interface: Streamlit
  - Base de dados: Supabase PostgreSQL (tabela activacoes)
  - Autenticação: Supabase Auth
  - URL: https://jamsoft-desktop-sojwnjzazqbevehnuees.streamlit.app

- **Base de Dados**
  - **Local:** SQLite (funciona offline)
  - **Nuvem:** Supabase PostgreSQL (sincronização)

### 3.2 Segurança

- Autenticação com Supabase Auth (JWT)
- Senhas com bcrypt (12 rounds)
- Row Level Security (RLS) na nuvem
- HTTPS/TLS para comunicação
- Auditoria completa de operações
- Backup encriptado (AES-256)

### 3.3 Sincronização

- Fila de sincronização local
- Retry automático em caso de falha
- Heartbeat para a plataforma (a cada 5 minutos)
- Modo offline com sincronização diferida

---

## 4. CONFORMIDADE FISCAL — AGT

### 4.1 Requisitos Implementados

| # | Requisito AGT | Estado | Implementação |
|---|---|---|---|
| 1 | Numeração sequencial de facturas | ✅ | Série por empresa |
| 2 | Formato de factura em PDF | ✅ | A4 + Térmica 80mm |
| 3 | Hash SHA-256 por documento | ✅ | Calculado na emissão |
| 4 | QR Code para verificação | ✅ | Link para consulta online |
| 5 | Exportação SAF-T (AO) | ✅ | Formato XML padrão |
| 6 | Registo de operações | ✅ | Auditoria completa |
| 7 | Dados do emitente | ✅ | Nome, NIF, endereço |
| 8 | Dados do cliente | ✅ | Nome, NIF |
| 9 | Descrição de produtos | ✅ | Nome, quantidade, preço |
| 10 | IVA por produto | ✅ | Taxa configurável (14%) |
| 11 | Assinatura digital RSA | ⏳ | A implementar |
| 12 | Comunicação em tempo real AGT | ⏳ | A implementar |

### 4.2 Formato de Factura

Cada factura contém:
- Número sequencial (ex: FT2026/00001)
- Série da empresa
- Data e hora de emissão
- NIF da empresa
- Nome e endereço da empresa
- NIF e nome do cliente
- Lista de produtos com:
  - Descrição
  - Quantidade
  - Preço unitário
  - Taxa de IVA
  - Subtotal
- Total de IVA
- Total a pagar
- Forma de pagamento
- Hash SHA-256
- QR Code (link de verificação)
- Assinatura RSA (a implementar)

### 4.3 SAF-T (AO)

Exportação em XML no formato exigido pela AGT:
- Cabeçalho (Header)
- MasterFiles (produtos, clientes)
- SourceDocuments (facturas, vendas)
- Assinatura digital

---

## 5. REQUISITOS DO SISTEMA

### 5.1 Hardware (Farmácia)

| Componente | Mínimo | Recomendado |
|---|---|---|
| CPU | Dual-core 2.0 GHz | Quad-core 2.5 GHz |
| RAM | 4 GB | 8 GB |
| Disco | 10 GB livres | 50 GB livres |
| Ecrã | 1366x768 | 1920x1080 |
| Internet | Opcional | Recomendado |

### 5.2 Software

- **Windows 10 ou 11** (64-bit)
- **Python 3.12+** (instalado automaticamente)
- **Dependências:** ver `requirements.txt`

### 5.3 Instalação

- Extrair o ZIP `JAM_Soft_vX.X.X_Setup.zip`
- Correr `INSTALAR.bat`
- Seguir o `MANUAL_NOVA_FILIAL.md`
- Activar com chave (Painel Master)

---

## 6. MODELO DE CERTIFICAÇÃO

### 6.1 Multi-Empresa (SaaS-ready)

O JAM Soft suporta múltiplas empresas com o mesmo software:

- **Produtor:** TRI JAM COMÉRCIO E PRESTAÇÃO DE SERVIÇO
- **Cliente:** cada farmácia faz o seu registo AGT
- **Chave RSA:** por cliente (a implementar)
- **Número de certificação do software:** único (TRI JAM)
- **Séries de facturação:** diferentes por filial/empresa

### 6.2 Modelo Primavera

Semelhante ao Primavera:
- Certificação do **software** (1x pela TRI JAM)
- Cada **utilizador** faz o seu registo
- Documentação técnica partilhada
- Suporte técnico centralizado

---

## 7. MANUTENÇÃO E ACTUALIZAÇÕES

### 7.1 Auto-Update

- Via GitHub (repositório oficial)
- Actualizações automáticas ao arrancar
- Backup antes de cada actualização
- Modo offline suportado

### 7.2 Versões

- Actual: **1.0.4** (12/10/2026)
- Histórico completo em `VERSION_HISTORY.md`
- Tags no GitHub: v1.0.0 a v1.0.4

### 7.3 Suporte

- **Telefone:** +244 923 888 338
- **Documentação:** `MANUAL_JAMSOFT.md`
- **Manual de nova filial:** `MANUAL_NOVA_FILIAL.md`

---

## 8. DOCUMENTAÇÃO ADICIONAL

| Documento | Descrição |
|---|---|
| `MANUAL_JAMSOFT.md` | Manual do utilizador completo |
| `MANUAL_NOVA_FILIAL.md` | Como abrir uma nova filial |
| `RESUMO_SISTEMA.md` | Visão técnica |
| `VERSION_HISTORY.md` | Histórico de versões |
| `LEIA-ME.txt` | Instalação rápida |

---

## 9. SEGURANÇA E AUDITORIA

- **Autenticação:** username + senha (bcrypt)
- **Perfis:** admin, gerente, farmacêutico, auditor
- **Permissões:** controlo por módulo
- **Auditoria:** todas as operações registadas
- **Backup:** automático local + OneDrive
- **Encriptação:** AES-256 para backups

---

## 10. CONTACTOS

**TRI JAM COMÉRCIO E PRESTAÇÃO DE SERVIÇO**

- **NIF:** 5003507920
- **Sede:** Província de Luanda, Município de Kilamba Kiaxi, Comuna de Nova Vida, Bairro Projecto, Rua Fubu, Casa s/nº, junto ao Descontão
- **Telefone:** +244 923 888 338

---

**FIM DO DOCUMENTO**

Versão 1.0.4 — 12/10/2026
