# Manual — Como Abrir uma Nova Filial JAM Soft

**Versão:** 1.0.4
**Data:** 12/10/2026

---

## Visão Geral

Este manual explica como abrir uma nova filial JAM Soft.
Tempo estimado: 30-45 minutos por filial.

---

## Pré-requisitos

- PC com Windows 10 ou 11
- Ligação à internet
- Python 3.12+ instalado
- Ficheiro JAM_Soft_v1.0.4_Setup.zip
- Acesso ao Painel Master
- NIF da empresa: 5003507920

---

## PASSO 1 — Criar Chave no Painel Master

### 1.1 Abrir o Painel

URL: https://jamsoft-desktop-sojwnjzazqbevehnuees.streamlit.app

### 1.2 Login

- Email: simaom510@gmail.com
- Senha: (a tua)

### 1.3 Criar Chave

Menu lateral > Criar Chave
- Nome: Tri JAM [Filial]
- NIF: 5003507920
- Série: FT2026/[XXX]/
- Notas: Filial aberta em DD/MM/AAAA

### 1.4 Copiar a Chave

Chave tipo: JAM-XXXX-XXXX-XXXX-XXXX
IMPORTANTE: Guarda em local seguro!

---

## PASSO 2 — Instalar no PC

### 2.1 Copiar Setup

Copia JAM_Soft_v1.0.4_Setup.zip para C:\farmacia-app\

### 2.2 Extrair

Botão direito > Extrair para C:\farmacia-app\

### 2.3 Correr INSTALAR.bat

Duplo-clique em INSTALAR.bat
Aguarda 2-5 minutos.

### 2.4 Correr INICIAR_FARMACIA.bat

Wizard de activação aparece.

### 2.5 Colar Chave

Cola a chave > Activar
Popup "Activação Concluída".

### 2.6 Primeiro Login

Utilizador: admin
Senha: admin

---

## PASSO 3 — Configurar Filial

### 3.1 Configurar Empresa

Fiscal > Configurar Empresa
- Nome: Tri JAM [Filial]
- NIF: 5003507920
- Série: FT2026/[XXX]/ (DIFERENTE de outras filiais)
- Logo, endereço, telefone

### 3.2 Configurar Metas

Metas > Nova Meta
- Meta mensal
- Meta diária

---

## PASSO 4 — Criar Utilizador Gerente

### 4.1 Novo Utilizador

Utilizadores > Novo
- Nome: [Nome do gerente]
- Utilizador: [username]
- Senha: forte
- Perfil: gerente ou admin

### 4.2 Alterar Senha do Admin

Utilizadores > admin > Editar
- Nova senha forte
- OU apagar o admin

---

## PASSO 5 — Testar

### 5.1 Testar Venda

PDV > Adiciona produto > Finaliza

### 5.2 Testar Sincronização

Aguarda 1-2 min
Verifica na Plataforma CEO

### 5.3 Testar Fecho de Caixa

Gestão de Caixa > Menu Caixa > Abre > Fecha

---

## Troubleshooting

### Python não encontrado

Instala de python.org/downloads
Marca "Add Python to PATH"

### Chave não encontrada

- Confirma cópia correcta
- Verifica Painel Master
- Cria chave nova

### Cloud desligada no .env

- Verifica codigo/.env
- Copia do PC principal

### Menus não aparecem

Executa:
python -c "import sqlite3; c = sqlite3.connect('codigo/farmacia.db'); c.execute(\"UPDATE utilizadores SET perfil='admin' WHERE UPPER(perfil)='ADMINISTRADOR'\"); c.commit(); c.close()"

### Sincronização não funciona

- Verifica internet
- App funciona offline
- Verifica indicador NUVEM

---

## Checklist Final

- [ ] Chave criada no Painel Master
- [ ] JAM Soft instalado
- [ ] Wizard concluído
- [ ] Login admin/admin OK
- [ ] Empresa configurada
- [ ] Utilizador gerente criado
- [ ] Senha do admin alterada
- [ ] Meta mensal definida
- [ ] Teste de venda OK
- [ ] Sincronização na Plataforma CEO

---

## Suporte

Email: suporte@jamsoft.ao
Painel Master: https://jamsoft-desktop-sojwnjzazqbevehnuees.streamlit.app

---

## Abreviaturas sugeridas

| Localização | Série |
|-------------|-------|
| Luanda | FT2026/ |
| Viana | FT2026/VIA/ |
| Kilamba | FT2026/KLB/ |
| Talatona | FT2026/TAL/ |
| Cacuaco | FT2026/CAC/ |
| Cazenga | FT2026/CAZ/ |
| Maianga | FT2026/MAI/ |

---

FIM DO MANUAL
Versão 1.0.4 — 12/10/2026
