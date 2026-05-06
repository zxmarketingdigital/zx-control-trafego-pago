#!/usr/bin/env python3
"""
Setup 6 — Etapa 2: Questionário Perfil de Campanhas
Coleta objetivos, KPIs, metas numéricas e estratégia decide() do aluno.
Salva em ~/.operacao-ia/config/meta_perfil.json.
"""
import json
import sys
from pathlib import Path

OPERACAO = Path.home() / ".operacao-ia"
PERFIL = OPERACAO / "config" / "meta_perfil.json"
META_ENV = OPERACAO / "config" / "meta.env"

OBJECTIVES = [
    ("LEAD_GENERATION", "Geração de Lead (form Meta ou redirect site)"),
    ("MESSAGES", "Conversa WhatsApp / Messenger / Instagram DM"),
    ("SALES", "Vendas (e-commerce / checkout)"),
    ("AWARENESS", "Reconhecimento (alcance / views)"),
    ("TRAFFIC", "Tráfego para site"),
    ("APP_INSTALL", "Instalações de App"),
]

KPIS_CATALOG = {
    "cpl":            {"label": "CPL (custo por lead)",       "better": "lower",  "format": "currency", "scale_at": 0.8, "kill_at": 1.5},
    "cpa":            {"label": "CPA (custo por venda)",      "better": "lower",  "format": "currency", "scale_at": 0.8, "kill_at": 1.5},
    "roas":           {"label": "ROAS",                        "better": "higher", "format": "ratio",    "scale_at": 0.8, "kill_at": 1.5},
    "cost_per_msg":   {"label": "Custo por mensagem",          "better": "lower",  "format": "currency", "scale_at": 0.8, "kill_at": 1.5},
    "cpm":            {"label": "CPM",                         "better": "lower",  "format": "currency", "scale_at": 0.8, "kill_at": 1.5},
    "ctr":            {"label": "CTR (taxa de clique)",        "better": "higher", "format": "percent",  "scale_at": 0.8, "kill_at": 1.5},
    "cpc":            {"label": "CPC",                         "better": "lower",  "format": "currency", "scale_at": 0.8, "kill_at": 1.5},
    "frequency":      {"label": "Frequência",                  "better": "lower",  "format": "ratio",    "scale_at": 0.8, "kill_at": 1.5},
    "cost_per_install":{"label":"Custo por instalação",        "better": "lower",  "format": "currency", "scale_at": 0.8, "kill_at": 1.5},
}


def ask_multi(prompt, options):
    print(f"\n{prompt}")
    for i, (k, label) in enumerate(options, 1):
        print(f"  [{i}] {label}")
    raw = input("\nDigite os números separados por vírgula (ex: 1,3): ").strip()
    chosen = []
    for tok in raw.split(","):
        tok = tok.strip()
        if not tok:
            continue
        try:
            idx = int(tok) - 1
            if 0 <= idx < len(options):
                chosen.append(options[idx][0])
        except ValueError:
            pass
    return chosen


def ask_kpis():
    print("\n" + "=" * 60)
    print("MÉTRICAS-CHAVE — quais você usa para julgar performance?")
    print("=" * 60)
    catalog_list = [(k, v["label"]) for k, v in KPIS_CATALOG.items()]
    keys = ask_multi("Selecione múltiplas:", catalog_list)
    if not keys:
        print("❌ Selecione pelo menos 1 KPI")
        return ask_kpis()

    kpis = []
    for key in keys:
        meta = KPIS_CATALOG[key].copy()
        meta["key"] = key
        print(f"\n→ {meta['label']}")
        while True:
            target_raw = input(f"   Sua meta numérica (ex: 25 para R$25, 2.0 para ROAS): ").strip()
            try:
                meta["target"] = float(target_raw)
                break
            except ValueError:
                print("   Valor inválido. Digite só o número.")
        kpis.append(meta)
    return kpis


def ask_decide_strategy(kpis):
    print("\n" + "=" * 60)
    print("ESTRATÉGIA decide() — quando matar/manter/escalar?")
    print("=" * 60)
    print("\nDefaults inteligentes (recomendado para a maioria):")
    print("  SCALE quando o KPI atinge 80% da sua meta na direção certa")
    print("  KILL  quando o KPI passa de 150% da sua meta na direção errada")
    print()
    use_default = input("Usar defaults? [S/n]: ").strip().lower()
    if use_default in ("", "s", "sim", "y", "yes"):
        return kpis, True

    for kpi in kpis:
        print(f"\n→ {kpi['label']} ({'menor é melhor' if kpi['better']=='lower' else 'maior é melhor'})")
        try:
            sc = input(f"   SCALE quando atinge X% da meta (default 0.8): ").strip()
            if sc:
                kpi["scale_at"] = float(sc)
            kl = input(f"   KILL quando passa de X% da meta (default 1.5): ").strip()
            if kl:
                kpi["kill_at"] = float(kl)
        except ValueError:
            print("   Valor inválido — mantendo default")
    return kpis, True


def ask_primary_kpi(kpis):
    if len(kpis) == 1:
        return kpis[0]["key"]
    print("\n" + "=" * 60)
    print("KPI PRIMÁRIO — qual decide primeiro em caso de conflito?")
    print("=" * 60)
    for i, k in enumerate(kpis, 1):
        print(f"  [{i}] {k['label']}")
    while True:
        raw = input("\nEscolha (1-{}): ".format(len(kpis))).strip()
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(kpis):
                return kpis[idx]["key"]
        except ValueError:
            pass
        print("Inválido")


def ask_windows():
    print("\n" + "=" * 60)
    print("JANELAS DE ANÁLISE")
    print("=" * 60)
    raw = input("Janelas (dias) separadas por vírgula [default 4,7,14,30]: ").strip()
    if not raw:
        return [4, 7, 14, 30]
    try:
        return sorted({int(x.strip()) for x in raw.split(",") if x.strip()})
    except ValueError:
        return [4, 7, 14, 30]


def read_ad_account():
    if META_ENV.exists():
        for line in META_ENV.read_text().splitlines():
            if line.startswith("META_AD_ACCOUNT_ID="):
                return line.split("=", 1)[1].strip()
    return ""


def show_summary(perfil):
    print("\n" + "=" * 60)
    print("RESUMO DO SEU PERFIL")
    print("=" * 60)
    print(f"\n📌 Conta: {perfil.get('ad_account_id') or '(preenche depois)'}")
    print(f"📌 Objetivos: {', '.join(perfil['objectives'])}")
    print(f"\n📊 KPIs configurados:")
    for k in perfil["kpis"]:
        meta_fmt = f"R${k['target']}" if k['format'] == 'currency' else (f"{k['target']}%" if k['format'] == 'percent' else f"{k['target']}")
        print(f"   • {k['label']:30s} meta {meta_fmt:>10s}  scale@{k['scale_at']}  kill@{k['kill_at']}")
    print(f"\n🎯 KPI primário: {perfil['primary_kpi']}")
    print(f"🔁 decide() ativo: {'sim' if perfil['decide_enabled'] else 'não'}")
    print(f"📅 Janelas: {perfil['windows']} dias")
    print("=" * 60)


def main():
    if not OPERACAO.exists():
        print("❌ Rode setup_base_s6.py primeiro.")
        sys.exit(1)

    print("\n📋 Etapa 2 — Questionário Perfil de Campanhas")
    print("Vou perguntar sobre suas campanhas para personalizar todo o setup.\n")

    objectives = ask_multi(
        "OBJETIVOS — quais campanhas você roda hoje? (multi-select)",
        OBJECTIVES,
    )
    if not objectives:
        print("❌ Selecione pelo menos 1 objetivo")
        sys.exit(1)

    kpis = ask_kpis()
    kpis, decide_enabled = ask_decide_strategy(kpis)
    primary = ask_primary_kpi(kpis)
    windows = ask_windows()
    ad_account = read_ad_account()

    perfil = {
        "objectives": objectives,
        "kpis": kpis,
        "primary_kpi": primary,
        "decide_enabled": decide_enabled,
        "windows": windows,
        "ad_account_id": ad_account,
    }

    show_summary(perfil)
    confirm = input("\nSalvar este perfil? [S/n]: ").strip().lower()
    if confirm in ("n", "no", "nao", "não"):
        print("Cancelado. Re-execute para refazer.")
        sys.exit(0)

    PERFIL.parent.mkdir(parents=True, exist_ok=True)
    PERFIL.write_text(json.dumps(perfil, indent=2, ensure_ascii=False))
    print(f"\n✅ Perfil salvo em {PERFIL}")
    print("Pronto para a Etapa 3 (instalar skills).")


if __name__ == "__main__":
    main()
