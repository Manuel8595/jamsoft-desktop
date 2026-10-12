# Histórico de Versões — JAM Soft Desktop

## v1.0.5 — 12/10/2026

### Adicionado
- Setup profissional com 3 atalhos (Startup + Desktop + Menu Iniciar)
- Ícone personalizado (logo JAM Soft 3D) nos atalhos
- Detecção automática da pasta Desktop (compatível com OneDrive)
- Manual completo para abrir nova filial (MANUAL_NOVA_FILIAL.md)
- Kit de Instalação genérico (Kit_Instalacao_TriJAM)
- Página "Farmácias" no Painel Master (agrupado por NIF)
- Página "Histórico" no Painel Master (validações recentes)
- 7 verificações no INSTALAR.bat (Python, internet, espaço, dependências)
- INSTRUCOES_RAPIDAS.txt (guia de 5 minutos)
- CHECKLIST.txt (para instalação em filial)

### Alterado
- DOCUMENTO_TECNICO_AGT.md actualizado para v1.0.4
- Empresa preenchida: TRI JAM COMÉRCIO E PRESTAÇÃO DE SERVIÇO
- NIF: 5003507920
- Setup ZIP agora tem 8 docs (antes 5)

### Corrigido
- Bug: atalho Desktop falhava em PCs com OneDrive
- Bug: caminho do Desktop fixo (agora dinâmico)
- Bug: menu Iniciar não era criado (agora dinâmico)

### Ficheiros novos
- MANUAL_NOVA_FILIAL.md
- master_panel/pages/4_Farmacias.py
- master_panel/pages/5_Historico.py
- Kit_Instalacao_TriJAM/ (kit completo)

---

## v1.0.4 — 10/10/2026

### Adicionado
- Sistema de activação por chave (SaaS-ready)
- Wizard de activação no desktop (Tkinter)
- Validação online da chave via Supabase REST
- Painel Master online (Streamlit Cloud)
- Login Supabase Auth no Painel Master
- 3 páginas no Painel Master: Chaves, Criar Chave, Estatísticas
- Script gerar_chave.py com menu interactivo
- Tabela activacoes no Supabase com RLS
- Configuração multi-filial com séries diferentes
- Logo JAM Soft 3D no login do Painel Master
- Animação float no logo da Plataforma CEO
- Tamanho responsivo do logo (desktop/tablet/mobile)

### Alterado
- preparar_setup_v3.py — setup profissional com estrutura organizada
- main.py — verificação de activação antes do login
- Perfis de utilizador normalizados para minúsculas (admin vs ADMINISTRADOR)
- app.py (CEO) — logo com animação CSS

### Corrigido
- Bug crítico: perfil admin criado em MAIÚSCULAS (bloqueava menus)
- Bug: VERSION não copiado para codigo/ no setup
- Bug: nomes de funções com acento (listar_historico)
- Bug: acentos portugueses em todos os ficheiros web
- Bug: login do CEO com erro de import

### Ficheiros novos
- activacao.py — wizard de activação
- config_activacao.py — gestão de activação local
- scripts/gerar_chave.py — gerador de chaves
- scripts/preparar_setup_v3.py — setup profissional
- master_panel/ — painel de gestão online

---

## v1.0.3 — 07/10/2026

### Adicionado
- Logo JAM Soft 3D nas facturas PDF (A4 + Térmica)
- Logo JAM Soft 3D no cabeçalho do Dashboard
- 3 KPIs novos no Dashboard: Clientes, Produtos em Stock, Lucro Potencial
- Efeito hover nos cards do Dashboard
- Pasta scripts/ para organizar ferramentas auxiliares

### Alterado
- Dashboard reorganizado em 2 linhas (8 KPIs)
- Cores e emojis nos títulos dos cards
- Facturas usam facturas/logo.png (transparente)
- Limpeza: 20 ficheiros temporários removidos

### Corrigido
- Bug crítico: logo nas facturas não aparecia
- Caminho relativo do logo convertido para absoluto
- Encoding UTF-8 em todos os ficheiros Python
- Acentos em português

---

## v1.0.2 — 03/10/2026

### Adicionado
- Login em fullscreen com card centralizado
- Ícone da aplicação nas janelas (.ico com múltiplos tamanhos)
- Logo no ecrã de login
- Cores alinhadas com o logotipo (roxo + dourado)
- Script criar_ico.py — converte PNG para ICO

### Alterado
- login.py reescrito com design moderno
- main.py com ícone da janela

---

## v1.0.1 — 03/10/2026

### Adicionado
- Logotipos profissionais (10 versões optimizadas)
- Script gerar_logos.py — gera logos programaticamente
- Script preparar_logos.py — redimensiona para todos os tamanhos
- Pasta logos/ completa

### Alterado
- RESUMO_SISTEMA.md melhorado
- .gitignore actualizado

---

## v1.0.0 — 03/10/2026

### Versão inicial
- PDV (Ponto de Venda)
- Controlo de stock com FEFO
- Fecho de caixa com TPA
- Pagamentos mistos
- Módulo fiscal (facturas + SAF-T)
- IVA configurável
- QR Code nas facturas
- Hash SHA-256
- Transferências entre farmácias (IBT)
- Sincronização automática com Supabase
- Backup automático local + OneDrive
- Heartbeat para plataforma web
- Sistema de auto-update via GitHub
