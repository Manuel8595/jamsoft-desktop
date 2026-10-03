# JAM Soft — Documento Técnico AGT

**Versão 2.0** | Data: 03/10/2026

## 1. IDENTIFICAÇÃO DO SOFTWARE

| Campo | Valor |
|-------|-------|
| Nome | JAM Soft |
| Versão | 2.0 |
| Empresa desenvolvedora | TRI JAM FARMA |
| NIF | 5401234567 |
| Endereço | Rua da Liberdade, 45, Luanda |
| Contacto | geral@farmacia.ao / +244 923 111 222 |
| Tipo | Software de facturação e gestão de farmácias |
| Plataformas | Desktop (Windows) + Web (Streamlit Cloud) |

## 2. REGISTO DE ALTERAÇÕES

### 03/10/2026 — Versão 2.0

Alterações críticas para conformidade AGT:

1. Hash encadeado implementado. Cada factura tem hash que depende do hash anterior da mesma série. Fórmula: hash_N = SHA256(hash_N-1 + dados_factura_N). Data de início da cadeia: 03/10/2026. Última factura na cadeia: FT 2026/00034 (ID 36). Módulo: agt_hash.py.

2. QR Code em todas as facturas. Presente no PDF A4 e no cupom Térmica 80mm. Aponta para URL de verificação pública. Módulo: impressao.py → função _desenhar_qr().

3. Assinatura RSA preparada. Suporta chave privada PEM. Algoritmo: RSA + SHA-256. Módulo: database.py → aplicar_assinatura_rsa(). Aguarda chave oficial da AGT.

4. Backup automático. Corre diariamente às 23h (cron-job.org). Encriptado AES-256. Enviado por email com anexo. Módulo: backup_service.py.

5. Botão "Impressão Facturas" no menu. Acesso directo a PDF A4 e Térmica. Localização: Menu principal → VENDAS E OPERACOES.

6. Correcção do arranque. INICIAR_FARMACIA.bat limpa cache automaticamente. Evita uso de código antigo em memória.

### 01/10/2026 — Versão 1.0

Estrutura base fiscal. Exportação SAF-T (AO). Séries sequenciais. Hash SHA-256 básico. Aviso legal "não validado pela AGT".

## 3. ESTADO ACTUAL DA CONFORMIDADE AGT

### 3.1. Componentes IMPLEMENTADOS

| Componente | Descrição | Data |
|------------|-----------|------|
| Séries sequenciais | Facturas numeradas (FT 2026/00034) | 2026 |
| Hash SHA-256 | Hash único por factura | 2026 |
| Hash encadeado | Dependência do hash anterior | 03/10/2026 |
| Assinatura RSA | Preparada (falta chave AGT) | 03/10/2026 |
| QR Code | Em todas as facturas A4 e Térmica | 03/10/2026 |
| Exportação SAF-T (AO) | XML mensal | 2026 |
| Configuração AGT | Campo nº validação + chave RSA | 2026 |
| Avisos legais | "DOCUMENTO LOCAL - NAO VALIDADO PELA AGT" | 2026 |
| Auditoria fiscal | Log de emissão e alterações | 2026 |
| Backup automático | Diário, AES-256, por email | 03/10/2026 |

### 3.2. Componentes EM FALTA

| Componente | Motivo | Dependência |
|------------|--------|-------------|
| Comunicação API REST (JSON) | Falta especificação técnica | Portal do Parceiro AGT |
| Número de Validação AGT | Falta processo de certificação | Submissão AGT |
| Certificado digital | Falta contratar | Multicert |
| Ambiente de homologação | Falta acesso de teste | Portal do Parceiro AGT |

## 4. DETALHES TÉCNICOS

### 4.1. Hash Encadeado

Fórmula: hash_factura_N = SHA256(hash_factura_N-1 + dados_factura_N)

Formato dos dados: numero;serie;data;nif_empresa;total;cliente_nif

Módulo: agt_hash.py
Funções principais: calcular_hash_factura() — calcula com base no anterior; validar_cadeia() — verifica integridade da série.

### 4.2. QR Code

URL de verificação: https://jamsoft-plataforma-nthcjcruax7wmg9rqxr4qz.streamlit.app/verificar?numero=[NUM]&serie=[SERIE]&hash=[HASH]

Formato: PNG, 25mm x 25mm (A4) / 18mm x 18mm (Térmica)

### 4.3. Assinatura RSA

Estado: Implementada, aguarda chave oficial.
Algoritmo: RSA + SHA-256
Armazenamento: Campo assinatura_digital (base64)

### 4.4. Exportação SAF-T (AO)

Formato: XML (SAF-T Angola 1.00_01)
Periodicidade: Mensal
Localização: Pasta saft/

### 4.5. Base de Dados

Motor: SQLite (local por terminal)
Ficheiro: farmacia.db
Tabelas fiscais: facturas (com hash_documento, hash_anterior, qr_code, assinatura_digital); itens_factura; config_agt; auditoria.

### 4.6. Segurança

| Medida | Implementação |
|--------|---------------|
| Autenticação | Utilizador + senha (bcrypt) |
| Permissões | Perfis: admin, gerente, farmacêutico, auditor |
| Auditoria | Todas as operações registadas |
| Backup | AES-256 + email diário |
| FEFO | Lotes seguem "primeiro a vencer, primeiro a sair" |

## 5. PRÓXIMOS PASSOS PARA CERTIFICAÇÃO

### Fase 1 — Preparação (Concluída)

Hash encadeado. QR Code. Assinatura RSA preparada. Documentação técnica. Backup.

### Fase 2 — Registo AGT (Esta semana)

Registar no Portal do Parceiro (portaldoparceiro.minfin.gov.ao). Registar software JAM Soft para certificação. Submeter chave pública RSA. Obter especificação técnica oficial. Obter certificado digital (Multicert).

### Fase 3 — Desenvolvimento (Após especificação)

Programar API REST (JSON). Testar em ambiente de homologação. Validar XML SAF-T. Corrigir divergências.

### Fase 4 — Submissão (Após testes)

Submeter software para avaliação AGT. Aguardar Número de Validação. Introduzir nº validação na app. Iniciar emissão oficial.

## 6. DOCUMENTAÇÃO ADICIONAL

| Documento | Localização |
|-----------|-------------|
| Estado do projecto | ESTADO_DO_PROJECTO.txt |
| Doc. técnico anterior (v1) | DOCUMENTO_TECNICO_AGT.md |
| Maquete PDF | Maquete_Sistema_Farmacia_Angola.pdf |
| Código fiscal | fiscal.py, saft_ao.py, database.py, impressao.py, agt_hash.py |
| Backups | backups/ |

## 7. CONTACTOS ÚTEIS

| Entidade | Contacto |
|----------|----------|
| Portal do Parceiro AGT | https://portaldoparceiro.minfin.gov.ao/ |
| Portal do Contribuinte AGT | https://portaldocontribuinte.minfin.gov.ao/ |
| Multicert | https://www.multicert.com/ |
| Suporte JAM Soft | geral@farmacia.ao |

## 8. DECLARAÇÃO

A empresa TRI JAM FARMA declara que:

1. O software JAM Soft 2.0 foi desenvolvido para cumprir os requisitos técnicos da AGT.
2. Todos os componentes técnicos disponíveis na especificação pública estão implementados.
3. A comunicação com o webservice da AGT será implementada após obtenção da especificação técnica oficial.
4. A aplicação está disponível para auditoria técnica pela AGT.

Assinatura: ________________________

Data: ___/___/2026

---

Documento gerado automaticamente pelo sistema JAM Soft. Para mais informações: geral@farmacia.ao