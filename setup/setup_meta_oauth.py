#!/usr/bin/env python3
"""
Setup 6 — Etapa 2: Conectar MCP oficial Meta

Coordena com Claude o fluxo OAuth + grava ad_account_id em meta.env.

Modos:

  python3 setup_meta_oauth.py
    — Imprime instruções para o Claude executar o OAuth via tool calls
      do MCP oficial Meta. O OAuth em si é feito pelo Claude (não por
      este script).

  python3 setup_meta_oauth.py --set-account act_123456789
    — Após o Claude validar a conta, grava META_AD_ACCOUNT_ID em meta.env.
      Idempotente: substitui se já existir.

  python3 setup_meta_oauth.py --validate
    — Verifica se há access_token Meta acessível e meta.env preenchido.
      Exit 0 = OK; exit 1 = falta token; exit 2 = falta ad_account_id.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

OPERACAO = Path.home() / ".operacao-ia"
META_ENV = OPERACAO / "config" / "meta.env"
TEMPLATE = """# Setup 6 — Tráfego Pago Meta ADS
# Gerado por setup_meta_oauth.py

META_AD_ACCOUNT_ID={ad_account_id}
META_BUSINESS_ID=
META_PAGE_ID=
META_PIXEL_ID=

SUPABASE_URL=
SUPABASE_SERVICE_KEY=

OPERACAO_IA_HOME=~/.operacao-ia
"""


def read_token():
    cj = Path.home() / ".claude.json"
    if cj.exists():
        try:
            data = json.loads(cj.read_text())
        except Exception:
            data = {}
        for key in ("mcpServers", "mcp_servers", "mcp"):
            block = data.get(key, {}) if isinstance(data, dict) else {}
            for name, cfg in (block or {}).items():
                if "meta" in name.lower():
                    token = (cfg.get("access_token")
                             or cfg.get("token")
                             or (cfg.get("env") or {}).get("META_ACCESS_TOKEN"))
                    if token:
                        return token
    return os.environ.get("META_ACCESS_TOKEN") or None


def read_account_from_env():
    if not META_ENV.exists():
        return ""
    for line in META_ENV.read_text().splitlines():
        if line.startswith("META_AD_ACCOUNT_ID="):
            return line.split("=", 1)[1].strip()
    return ""


def write_account(ad_account_id):
    if not re.match(r"^act_\d+$", ad_account_id):
        print(f"❌ ad_account_id inválido: {ad_account_id} (esperado: act_<dígitos>)")
        return 1
    META_ENV.parent.mkdir(parents=True, exist_ok=True)
    if META_ENV.exists():
        lines = META_ENV.read_text().splitlines()
        out = []
        replaced = False
        for line in lines:
            if line.startswith("META_AD_ACCOUNT_ID="):
                out.append(f"META_AD_ACCOUNT_ID={ad_account_id}")
                replaced = True
            else:
                out.append(line)
        if not replaced:
            out.append(f"META_AD_ACCOUNT_ID={ad_account_id}")
        META_ENV.write_text("\n".join(out) + "\n")
    else:
        META_ENV.write_text(TEMPLATE.format(ad_account_id=ad_account_id))
    print(f"✅ META_AD_ACCOUNT_ID={ad_account_id} gravado em {META_ENV}")
    return 0


def cmd_validate():
    token = read_token()
    if not token:
        print("❌ Sem access_token Meta. Reconecte o MCP oficial.")
        return 1
    masked = token[:8] + "…" + token[-4:] if len(token) > 16 else "***"
    print(f"✅ Token presente ({masked}, len={len(token)})")
    acct = read_account_from_env()
    if not acct or "XXXXX" in acct:
        print("❌ META_AD_ACCOUNT_ID não preenchido em meta.env")
        return 2
    print(f"✅ META_AD_ACCOUNT_ID={acct}")
    return 0


def cmd_instructions():
    if not OPERACAO.exists():
        print("❌ Rode setup_base_s6.py (E0) primeiro.")
        return 1

    print("📡 Etapa 2 — Conectar MCP oficial Meta")
    print("=" * 60)
    print()
    print("INSTRUÇÕES PARA O CLAUDE (executar via tool calls):")
    print()
    print("1. mcp__meta-official__authenticate")
    print("   → recebe callback_url; mostre ao aluno e peça pra autorizar")
    print()
    print("2. Aguarde o aluno completar OAuth no browser e colar a URL final")
    print()
    print("3. mcp__meta-official__complete_authentication(callback_url=<url>)")
    print()
    print("4. mcp__meta-official__ads_get_ad_accounts")
    print("   → liste as contas para o aluno escolher (se >1)")
    print()
    print("5. python3 setup/setup_meta_oauth.py --set-account act_XXXXXXXX")
    print("   → grava o ad_account_id escolhido em meta.env")
    print()
    print("6. python3 setup/setup_meta_oauth.py --validate")
    print("   → confirma token + ad_account_id (deve retornar exit 0)")
    print()
    print("=" * 60)
    print()
    print("Permissões pedidas no OAuth: ads_management, business_management")
    print()
    print("⚠️  NUNCA exiba o access_token completo. Mostre só prefix+sufix.")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--set-account", metavar="ACT_ID",
                        help="Grava META_AD_ACCOUNT_ID em meta.env")
    parser.add_argument("--validate", action="store_true",
                        help="Valida token + meta.env preenchido")
    args = parser.parse_args()

    if args.set_account:
        return write_account(args.set_account)
    if args.validate:
        return cmd_validate()
    return cmd_instructions()


if __name__ == "__main__":
    sys.exit(main())
