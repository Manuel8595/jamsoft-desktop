# Histórico de Versões — JAM Soft Desktop

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