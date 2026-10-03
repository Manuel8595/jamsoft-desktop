# DOCUMENTO TÉCNICO — JAM SOFT

## Sistema de Gestão de Farmácias

**Versão:** 1.0
**Data:** ___/___/______
**Empresa:** ________________
**NIF:** ________________
**Contacto:** ________________

---

## 1. IDENTIFICAÇÃO DO SOFTWARE

| Campo | Valor |
|---|---|
| **Nome** | JAM Soft - Sistema de Gestão de Farmácias |
| **Versão** | 1.0 |
| **Tipo** | Aplicação desktop + Plataforma web |
| **Linguagem** | Python 3.12 |
| **Base de dados** | SQLite (local) + Supabase PostgreSQL (nuvem) |
| **Sistema operativo** | Windows 10 / 11 |

---

## 2. ARQUITECTURA

### 2.1 Componentes

- **Aplicação desktop** — corre no PC da farmácia
  - PDV (Ponto de Venda)
  - Gestão de stock e lotes
  - Gestão de caixa e turnos
  - Emissão de facturas
  - Exportação SAF-T (AO)
- **Plataforma web** — monitorização remota
  - Dashboard multi-farmácia
  - Relatórios
  - IA (orçamentos, alertas)
  - Diagnóstico remoto
- **Base de dados** — dupla
  - Local: SQLite (funciona offline)
  - Nuvem: Supabase PostgreSQL (sincronização)

### 2.2 Segurança

- Autenticação com Supabase Auth (JWT)
- Senhas com bcrypt (12 rounds)
- Row Level Security (RLS) na nuvem
- HTTPS/TLS para comunicação
- Auditoria completa de operações

---

## 3. CONFORMIDADE FISCAL — AGT

### 3.1 Requisitos Implementados

| # | Requisito AGT | Estado | Implementação |
|---|---|---|---|
| 1 | Hash em facturas | ✅ | SHA-256 de numero;serie;data;nif;total;nif_cliente |
| 2 | QR Code | ✅ | Link para verificação + hash |
| 3 | Exportação SAF-T (AO) | ✅ | XML formato OECD |
| 4 | Numeração sequencial | ✅ | Sem saltos, série configurável |
| 5 | Imutabilidade de facturas | ✅ | Facturas emitidas não podem ser alteradas |
| 6 | Aviso legal | ✅ | "Processado por programa validado n.º __/AGT/__" |
| 7 | Livro de facturas | ✅ | Listagem completa com filtros |
| 8 | Regime fiscal | ✅ | Configurável (GERAL, SIMPLIFICADO, EXONERADO) |

### 3.2 Estrutura do Hash

Ordem dos dados: numero;serie;data;nif_empresa;total;nif_cliente

Exemplo: FT 2026/00026;FT 2026/;2026-10-02 15:35:48;5401234567;456000.00;5412000785

Hash SHA-256: 7BE9EA49DE7FF80606941D7AFA0583ABC589F7BC780878E8DAF1D694536D9EE2

**Nota:** Este hash é provisório. A assinatura RSA será aplicada quando a AGT fornecer a chave privada.

### 3.3 Estrutura do SAF-T (AO)

Ficheiro XML com namespace: urn:OECD:StandardAuditFile-Tax:AO_1.00_01

Secções incluídas:
- Header (dados da empresa, período, versão)
- MasterFiles (clientes, produtos)
- SourceDocuments (facturas emitidas)

Ficheiro de exemplo: saft/SAFT_AO_YYYYMMDD_YYYYMMDD.xml

### 3.4 QR Code

Conteúdo do QR: https://<plataforma>/verificar?numero=<numero>&serie=<serie>&hash=<hash>

Permite:
- Verificação da autenticidade
- Consulta online da factura
- Validação do hash

---

## 4. FUNCIONALIDADES FISCAIS

### 4.1 Emissão de Facturas

- Numeração automática e sequencial
- Séries configuráveis
- Tipos: FT (Factura), FP (Proforma), NC (Nota de Crédito)
- Anulação com motivo registado
- Imutabilidade após emissão

### 4.2 IVA

- Classificação por produto
- Medicamentos isentos (uso terapêutico)
- Cosméticos e outros tributados (14%)
- Cálculo automático
- Totalização por taxa

### 4.3 Relatórios Fiscais

- Livro de facturas emitidas
- Livro de facturas anuladas
- Resumo de IVA por período
- Exportação SAF-T
- Exportação para contabilista

---

## 5. SEGURANÇA E AUDITORIA

### 5.1 Autenticação

- Login obrigatório
- Perfis: admin, gerente, farmacêutico, auditor
- Bloqueio após 3 tentativas falhadas
- Sessão com timeout (15 min)

### 5.2 Auditoria

Todas as operações são registadas:
- Vendas
- Anulações
- Descontos autorizados
- Fechos de caixa
- Alterações de preços
- Exportações SAF-T

### 5.3 Integridade

- Backup automático diário
- Verificação de integridade SQLite
- Sincronização cloud com UUID
- Log de operações

---

## 6. CERTIFICAÇÃO SOLICITADA

Solicitamos à AGT:

1. Número de validação do software
2. Chave RSA privada para assinatura digital
3. XSD oficial do SAF-T (AO) para ajuste do formato
4. Especificações técnicas completas
5. Ambiente de testes para validação

---

## 7. CONTACTOS

Responsável Técnico:
Nome: ________________
Telefone: ________________
Email: ________________

Responsável Legal:
Nome: ________________
Telefone: ________________
Email: ________________

---

## 8. ANEXOS

- [ ] Ficheiro SAF-T de exemplo
- [ ] Captura de ecrã do sistema
- [ ] Manual do utilizador
- [ ] Diagrama de arquitectura

---

**Assinatura:** ________________
**Data:** ___/___/______