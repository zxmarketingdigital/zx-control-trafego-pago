#!/usr/bin/env python3
"""
Setup 6 — Etapa 1: Conectar MCP oficial Meta
Wrapper que orienta o Claude a chamar mcp__meta-official__authenticate.
Este script em si não chama o MCP — ele apenas valida pré/pós condições.
O fluxo de OAuth é executado pelo Claude direto via tool calls.
"""
import sys
from pathlib import Path

OPERACAO = Path.home() / ".operacao-ia"
META_ENV = OPERACAO / "config" / "meta.env"


def main():
    if not OPERACAO.exists():
        print("❌ Estrutura base não existe. Rode setup_base_s6.py primeiro.")
        sys.exit(1)

    print("📡 Etapa 1 — Conectar MCP oficial Meta")
    print("=" * 60)
    print()
    print("INSTRUÇÕES PARA O CLAUDE:")
    print()
    print("1. Chame: mcp__meta-official__authenticate")
    print("   - Receba o callback_url retornado")
    print("   - Mostre ao aluno: 'Abra essa URL e autorize: <url>'")
    print()
    print("2. Aguarde o aluno completar OAuth no browser e colar o callback URL")
    print()
    print("3. Chame: mcp__meta-official__complete_authentication(callback_url=<url>)")
    print()
    print("4. Valide chamando: mcp__meta-official__ads_get_ad_accounts")
    print("   - Liste as contas retornadas para o aluno")
    print("   - Pergunte qual conta vai usar (se houver mais de uma)")
    print()
    print("5. Salve o ad_account_id escolhido em ~/.operacao-ia/config/meta.env:")
    print("   META_AD_ACCOUNT_ID=act_XXXXXXXX")
    print()
    print("=" * 60)
    print()
    print("Permissões pedidas no OAuth:")
    print("  - ads_management")
    print("  - business_management")
    print()
    print("⚠️  Nunca exiba o access_token completo nos logs.")
    print()
    print("Após validar, marque a Etapa 1 como concluída.")


if __name__ == "__main__":
    main()
