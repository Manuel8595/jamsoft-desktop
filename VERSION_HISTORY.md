# Hist?rico de Vers?es ? JAM Soft Desktop

## v1.0.4 ? 10/10/2026

### Adicionado
- Sistema de activa??o por chave (SaaS-ready)
- Wizard de activa??o no desktop (Tkinter)
- Valida??o online da chave via Supabase REST
- Painel Master online (Streamlit Cloud)
- Login Supabase Auth no Painel Master
- 3 p?ginas no Painel Master: Chaves, Criar Chave, Estat?sticas
- Script `gerar_chave.py` com menu interactivo
- Tabela `activacoes` no Supabase com RLS
- Configura??o multi-filial com s?ries diferentes
- Logo JAM Soft 3D no login do Painel Master
- Anima??o float no logo da Plataforma CEO
- Tamanho responsivo do logo (desktop/tablet/mobile)

### Alterado
- `preparar_setup_v3.py` ? setup profissional com estrutura organizada
- `main.py` ? verifica??o de activa??o antes do login
- Perfis de utilizador normalizados para min?sculas (`admin` vs `ADMINISTRADOR`)
- `app.py` (CEO) ? logo com anima??o CSS

### Corrigido
- Bug cr?tico: perfil admin criado em MAI?SCULAS (bloqueava menus)
- Bug: `VERSION` n?o copiado para `codigo/` no setup
- Bug: nomes de fun??es com acento (`listar_historico`)
- Bug: acentos portugueses em todos os ficheiros web
- Bug: login do CEO com erro de import

### Ficheiros novos
- `activacao.py` ? wizard de activa??o
- `config_activacao.py` ? gest?o de activa??o local
- `scripts/gerar_chave.py` ? gerador de chaves
- `scripts/preparar_setup_v3.py` ? setup profissional
- `master_panel/` ? painel de gest?o online

---

## v1.0.3 ? 07/10/2026

### Adicionado
- Logo JAM Soft 3D nas facturas PDF (A4 + T?rmica)
- Logo JAM Soft 3D no cabe?alho do Dashboard
- 3 KPIs novos no Dashboard: Clientes, Produtos em Stock, Lucro Potencial
- Efeito hover nos cards do Dashboard
- Pasta `scripts/` para organizar ferramentas auxiliares

### Alterado
- Dashboard reorganizado em 2 linhas (8 KPIs)
- Cores e emojis nos t?tulos dos cards
- Facturas usam `facturas/logo.png` (transparente)
- Limpeza: 20 ficheiros tempor?rios removidos

### Corrigido
- Bug cr?tico: logo nas facturas n?o aparecia
- Caminho relativo do logo convertido para absoluto
- Encoding UTF-8 em todos os ficheiros Python
- Acentos em portugu?s

---

## v1.0.2 ? 03/10/2026

### Adicionado
- Login em fullscreen com card centralizado
- ?cone da aplica??o nas janelas (.ico com m?ltiplos tamanhos)
- Logo no ecr? de login
- Cores alinhadas com o logotipo (roxo + dourado)
- Script `criar_ico.py` ? converte PNG para ICO

### Alterado
- `login.py` reescrito com design moderno
- `main.py` com ?cone da janela

---

## v1.0.1 ? 03/10/2026

### Adicionado
- Logotipos profissionais (10 vers?es optimizadas)
- Script `gerar_logos.py` ? gera logos programaticamente
- Script `preparar_logos.py` ? redimensiona para todos os tamanhos
- Script `gerar_pdf_profissional.py` ? PDFs A4 com capa bonita
- Script `gerar_pdf_manual.py` ? PDF simples
- Pasta `logos/` completa

### Alterado
- `RESUMO_SISTEMA.md` melhorado
- `.gitignore` actualizado

---

## v1.0.0 ? 03/10/2026

**Vers?o inicial** ??

### Funcionalidades
- PDV (Ponto de Venda)
- Controlo de stock com FEFO
- Fecho de caixa com TPA
- Pagamentos mistos (dinheiro + Multicaixa + transfer?ncia)
- M?dulo fiscal (facturas + SAF-T)
- IVA configur?vel (14% Luanda)
- QR Code nas facturas
- Hash SHA-256
- Transfer?ncias entre farm?cias (IBT)
- Sincroniza??o autom?tica com Supabase
- Backup autom?tico local + OneDrive
- Heartbeat para plataforma web
- Sistema de auto-update via GitHub
