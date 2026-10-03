# ============================================================
# ============ SINCRONIZACAO AUTOMATICA EM BACKGROUND ========
# ============================================================
# 
# Corre em background (thread) e sincroniza a cada X minutos.
# Nao interrompe o utilizador.
# 
# ============================================================

import threading
import time
from datetime import datetime
from config_cloud import SYNC_ENABLED


# Configuracoes
INTERVALO_SYNC = 5 * 60      # 5 minutos em segundos
INTERVALO_ESTADO = 30        # 30 segundos (atualiza rodape)


class AutoSync:
    """Gestor de sincronizacao automatica em background."""
    
    def __init__(self):
        self.ativo = False
        self.thread = None
        self.ultima_execucao = None
        self.ultimo_resultado = None
        self.callback = None
    
    def iniciar(self, callback_notificacao=None):
        """Inicia a sincronizacao automatica."""
        if not SYNC_ENABLED:
            self.ativo = False
            print("[AutoSync] Desactivado pelas definicoes de seguranca")
            return
        if self.ativo:
            return
        
        self.ativo = True
        self.callback = callback_notificacao
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print(f"[AutoSync] Iniciado (a cada {INTERVALO_SYNC // 60} minutos)")
    
    def parar(self):
        """Para a sincronizacao automatica."""
        self.ativo = False
        print("[AutoSync] Parado")
    
    def _loop(self):
        """Loop principal da thread."""
        # Espera 30 segundos antes da primeira sincronizacao
        time.sleep(30)
        
        while self.ativo:
            try:
                self._executar_sync()
            except Exception as e:
                print(f"[AutoSync] Erro: {e}")
            
            # Espera o intervalo
            for _ in range(INTERVALO_SYNC):
                if not self.ativo:
                    return
                time.sleep(1)
    
    def _executar_sync(self):
        """Executa a sincronizacao."""
        # Importar aqui (lazy) para evitar dependencia circular
        try:
            from sincronizacao import (tem_internet, contar_pendentes,
                                         sincronizar_tudo, registar_sincronizacao)
        except Exception as e:
            print(f"[AutoSync] Erro ao importar: {e}")
            return
        
        # Conta pendentes
        p = contar_pendentes()
        if p["total"] == 0:
            self.ultima_execucao = datetime.now()
            self.ultimo_resultado = {"sucesso": True, "total": 0, "motivo": "Nada pendente"}
            return
        
        # Verifica internet
        online, motivo = tem_internet()
        if not online:
            self.ultima_execucao = datetime.now()
            self.ultimo_resultado = {"sucesso": False, "total": 0, "motivo": motivo}
            return
        
        # Sincroniza
        resultado = sincronizar_tudo()
        self.ultima_execucao = datetime.now()
        self.ultimo_resultado = resultado
        
        if resultado["sucesso"]:
            registar_sincronizacao(True, resultado["total"])
            print(f"[AutoSync] {resultado['total']} operacoes sincronizadas")
            
            # Notificar (se callback)
            if self.callback and resultado["total"] > 0:
                try:
                    self.callback(resultado)
                except Exception:
                    pass


# Instancia global
auto_sync = AutoSync()


def iniciar_auto_sync(callback=None):
    """Inicia a sincronizacao automatica."""
    auto_sync.iniciar(callback)


def parar_auto_sync():
    """Para a sincronizacao automatica."""
    auto_sync.parar()


def estado_auto_sync():
    """Retorna o estado atual."""
    return {
        "ativo": auto_sync.ativo,
        "ultima_execucao": auto_sync.ultima_execucao,
        "ultimo_resultado": auto_sync.ultimo_resultado,
    }


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  TESTE DE AUTO-SYNC - JAM SOFT")
    print("="*60)
    
    def notificar(resultado):
        print(f"\n[Notificacao] Sincronizados {resultado['total']} registos!")
    
    iniciar_auto_sync(callback=notificar)
    print("\nAuto-sync iniciado. Primeira execucao em 30 segundos.")
    print("Aguarda... (Ctrl+C para sair)\n")
    
    try:
        for i in range(120):
            time.sleep(1)
            if i % 10 == 0:
                e = estado_auto_sync()
                print(f"[{i}s] Ativo: {e['ativo']} | Ultima: {e['ultima_execucao']}")
    except KeyboardInterrupt:
        print("\n\nInterrompido.")
    
    parar_auto_sync()
    print("\nAuto-sync parado.")
    print("="*60 + "\n")
