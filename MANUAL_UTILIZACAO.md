# JAM Soft — Manual de Utilização

**Versão:** 1.0.0
**Para:** Funcionários e CEOs

---

## 1. Abrir a Aplicação

1. Vai ao desktop do computador
2. Duplo-clique em **INICIAR_FARMACIA.bat**
3. Espera 30 segundos
4. Faz login (email + senha)
5. Pronto para trabalhar

### O que acontece automaticamente
[1/5] A verificar actualizacoes...
[2/5] A criar backup da base de dados...
[3/5] A verificar Python...
[4/5] A verificar dependencias...
[5/5] A iniciar aplicacao...


---

## 2. Fechar a Aplicação

1. Menu → **Terminar Sessão**
2. Fecha a janela preta (terminal)
3. Fecha a janela da aplicação

**Nunca desligues o PC directamente.**

---

## 3. Fazer uma Venda

1. Clica em **PDV**
2. Lê o código de barras do produto
3. Confirma a quantidade
4. Adiciona mais produtos (se necessário)
5. Clica em **Finalizar**
6. Escolhe a forma de pagamento:
   - Dinheiro
   - Multicaixa
   - Transferência
   - Misto (parte de cada)
7. Confirma o total
8. Imprime a factura (opcional)

---

## 4. Receber Stock

1. Menu → **Produtos**
2. Clica em **+ Novo Produto** ou **Entrada de Stock**
3. Preenche:
   - Nome do produto
   - Código de barras
   - Preço de custo
   - Preço de venda
   - Quantidade
   - Lote e validade
   - Isento de IVA? (só para medicamentos)
4. Guardar

---

## 5. Fechar o Caixa

**No fim do dia:**

1. Menu → **Caixa**
2. Clica em **Fechar Turno**
3. Conta o dinheiro físico
4. Conta os talões Multicaixa
5. Insere os valores
6. Confirma

O sistema calcula:
- Diferença em dinheiro
- Total TPA
- Total transferência
- Diferenças

---

## 6. Fazer uma Transferência (IBT)

### Se a farmácia precisa de stock

1. Menu → **Transferências**
2. Clica em **+ Nova**
3. Escolhe a farmácia de destino
4. Adiciona os produtos
5. Clica em **Enviar** (precisa de autorização do gestor)
6. Imprime o comprovativo PDF

### Se a farmácia vai receber

1. Menu → **Transferências**
2. Vê as que estão **Em trânsito**
3. Clica em **Receber**
4. Confirma as quantidades recebidas
5. Confirma

---

## 7. Ver a Plataforma Web (CEO)

### No computador

1. Abre o browser
2. Vai a: https://jamsoft-plataforma-nthcjcruax7wmg9rqxr4qz.streamlit.app
3. Login com email + senha

### No telemóvel (como app)

1. Abre o mesmo link no Chrome
2. Menu → **Instalar app**
3. Aparece o ícone JAM Soft no ecrã do telemóvel

---

## 8. Usar o Chat IA

1. Menu → **Chat IA**
2. Escreve ou clica nas sugestões:
   - "Quanto vendi hoje?"
   - "Que farmácia vendeu mais?"
   - "Que produtos estão com stock baixo?"
   - "Como está o mês?"

---

## 9. Fazer Backup

### No Desktop (automático)

- Backup local ao arrancar
- Cópia para OneDrive automaticamente
- Últimos 30 dias guardados

### Na Web (manual)

1. Menu → **Backup**
2. Clica **Criar Backup**
3. Descarrega o ficheiro `.enc`
4. Guarda no Google Drive ou OneDrive

### Na Web (automático)

- Corre todos os dias às 23h
- Chega email com o backup em anexo

---

## 10. Verificar a Versão

Ao abrir a aplicação, aparece:

Versao local: v1.0.0


E no GitHub:

- https://github.com/Manuel8595/jamsoft-desktop/tags

---

## 11. Actualizar a Aplicação

**Nada a fazer.** O `INICIAR_FARMACIA.bat` faz automaticamente:

1. Verifica se há nova versão
2. Descarrega do GitHub
3. Actualiza sem perder dados

---

## 12. Recuperar um Backup

**Só em caso de emergência:**

1. Fecha a aplicação
2. Vai a `C:\Users\manue\farmacia-app\backups\`
3. Copia o backup desejado
4. Cola na pasta `farmacia-app\`
5. Renomeia para `farmacia.db`
6. Abre a aplicação

**Se tiveres dúvidas, contacta suporte.**

---

## 13. Problemas Comuns

### "Python nao encontrado"

1. Vai a: https://www.python.org/downloads/
2. Instala Python 3.12
3. Marca **"Add to PATH"** durante a instalação
4. Reinicia o PC

### "Sem internet"

**Não é problema.** A aplicação funciona offline:

- Vendas funcionam
- Stock funciona
- Fecho de caixa funciona
- Sincronização é adiada

### "Actualizacao falhou"

1. Verifica se tens internet
2. Fecha a aplicação
3. Abre novamente
4. Se persistir, contacta suporte

### "Não consigo fazer login"

Verifica:

- Email está correcto?
- Senha está correcta?
- Caps Lock ligado?

Se esqueceste a senha, contacta o CEO/Administrador.

---

## 14. Emergência

Se algo crítico acontecer:

1. **NÃO desligues o PC**
2. **NÃO apagues nada**
3. Tira uma **foto do ecrã**
4. Contacta suporte imediatamente

---

## 15. Atalhos Úteis

### Aplicação Desktop

| Acção | Atalho |
|-------|--------|
| Nova venda | F2 |
| Consultar stock | F3 |
| Fechar turno | F5 |
| Pesquisar | Ctrl+F |
| Sair | Ctrl+Q |

### Plataforma Web

| Acção | Como |
|-------|------|
| Navegar | Menu lateral |
| Filtrar | Selectbox no topo |
| Actualizar | Botão de refresh |
| Exportar | Botão de download |

---

## 16. Suporte

**Email:** suporte@jamsoft.ao
**Telefone:** +244 XXX XXX XXX
**Horário:** Seg-Sex, 8h-18h

---

**JAM Soft © 2026 — Todos os direitos reservados**