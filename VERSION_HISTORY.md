# Histórico de Versões — JAM Soft Desktop


## v1.0.3 — 07/10/2026

### Adicionado
- Logo JAM Soft 3D nas facturas PDF (A4 + Térmica)
- Logo JAM Soft 3D no cabeçalho do Dashboard
- 3 KPIs novos no Dashboard: Clientes, Produtos em Stock, Lucro Potencial
- Efeito hover nos cards do Dashboard (muda de cor ao passar o rato)
- Pasta `scripts/` para organizar ferramentas auxiliares

### Alterado
- Dashboard reorganizado em 2 linhas (8 KPIs)
- Cores e emojis nos títulos dos cards
- Facturas usam `facturas/logo.png` (transparente)
- Limpeza: 20 ficheiros temporários removidos

### Corrigido
- Bug crítico: logo nas facturas não aparecia (`emp[9]` vs `emp[10]`)
- Caminho relativo do logo convertido para absoluto (`os.path.isabs`)
- Encoding UTF-8 em todos os ficheiros Python
- Acentos em português (críticos, períodos, histórico, etc.)

---

## v1.0.2 — 03/10/2026

### Adicionado
- Login em fullscreen com card centralizado
- Ícone da aplicação nas janelas (.ico com múltiplos tamanhos)
- Logo no ecrã de login
- Cores alinhadas com o logotipo (roxo + dourado)
- Script `criar_ico.py` — converte PNG para ICO

### Alterado
- `login.py` reescrito com design moderno
- `main.py` com ícone da janela

---

## v1.0.1 — 03/10/2026

### Adicionado
- Logotipos profissionais (10 versões optimizadas)
- Script `gerar_logos.py` — gera logos programaticamente
- Script `preparar_logos.py` — redimensiona para todos os tamanhos
- Script `gerar_pdf_profissional.py` — PDFs A4 com capa bonita
- Script `gerar_pdf_manual.py` — PDF simples
- Pasta `logos/` completa

### Alterado
- `RESUMO_SISTEMA.md` melhorado
- `.gitignore` actualizado (ignora PDFs gerados)

---

## v1.0.0 — 03/10/2026

**Versão inicial** 🎉

### Funcionalidades
- ✅ PDV (Ponto de Venda)
- ✅ Controlo de stock com FEFO
- ✅ Fecho de caixa com TPA
- ✅ Pagamentos mistos (dinheiro + Multicaixa + transferência)
- ✅ Módulo fiscal (facturas + SAF-T)
- ✅ IVA configurável (14% Luanda)
- ✅ QR Code nas facturas
- ✅ Hash SHA-256
- ✅ Transferências entre farmácias (IBT)
- ✅ Sincronização automática com Supabase
- ✅ Backup automático local + OneDrive
- ✅ Heartbeat para plataforma web
- ✅ Sistema de auto-update via GitHub
- ✅ Numeração de versões