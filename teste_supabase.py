"""Diagnóstico manual, sem mostrar chaves Supabase no terminal."""

from config_cloud import SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, CLOUD_ACCESS_ENABLED


def main():
    if not CLOUD_ACCESS_ENABLED:
        print("Ligação Supabase desactivada pelas definições de segurança.")
        return
    if not SUPABASE_URL or not SUPABASE_PUBLISHABLE_KEY:
        print("Configuração Supabase ausente. Verifique o ficheiro .env.")
        return

    import requests

    url = f"{SUPABASE_URL}/rest/v1/farmacias?select=id&limit=1"
    headers = {
        "apikey": SUPABASE_PUBLISHABLE_KEY,
        "Authorization": f"Bearer {SUPABASE_PUBLISHABLE_KEY}",
    }
    try:
        resposta = requests.get(url, headers=headers, timeout=10)
        print(f"Ligação Supabase: HTTP {resposta.status_code}")
        if not resposta.ok:
            print("O servidor recusou o pedido; confirme as permissões e as políticas RLS.")
    except requests.RequestException as erro:
        print(f"Não foi possível ligar ao Supabase: {erro}")


if __name__ == "__main__":
    main()
