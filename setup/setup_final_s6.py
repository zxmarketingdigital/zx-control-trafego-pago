#!/usr/bin/env python3
"""
Setup 6 — Etapa 10 (parte 2): Finalização
Marca phase_completed=6, reabre dashboard, mostra mensagem final.
"""
import json
import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from setup_base_s6 import ConfigBackupError, backup_config_copy, parse_phase, write_config_atomic  # noqa: E402

OPERACAO = Path.home() / ".operacao-ia"
CONFIG = OPERACAO / "config" / "config.json"
PERFIL = OPERACAO / "config" / "meta_perfil.json"
META_ENV = OPERACAO / "config" / "meta.env"


def read_ad_account():
    if not META_ENV.exists():
        return "(não configurado)"
    for line in META_ENV.read_text().splitlines():
        if line.startswith("META_AD_ACCOUNT_ID="):
            return line.split("=", 1)[1].strip() or "(não configurado)"
    return "(não configurado)"


def fmt_target(k):
    if k["format"] == "currency":
        return f"R${k['target']}"
    if k["format"] == "percent":
        return f"{k['target']}%"
    return f"{k['target']}"


def main():
    if not PERFIL.exists():
        print("❌ meta_perfil.json não existe (rode E2)")
        sys.exit(1)

    # Este setup não exige nenhum setup anterior: config.json ausente/corrompido é recriado.
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    cfg = None
    if CONFIG.exists():
        try:
            cfg = json.loads(CONFIG.read_text())
            if not isinstance(cfg, dict):
                raise ValueError("config.json não é um objeto JSON")
        except Exception:
            try:
                backup = backup_config_copy(CONFIG)
            except ConfigBackupError:
                sys.exit(1)  # mensagem ja impressa; config original intacto
            print(f"⚠️  config.json inválido — cópia guardada em {backup.name}")
            cfg = None
    if cfg is None:
        cfg = {}
    anterior = parse_phase(cfg.get("phase_completed", 0))
    if anterior < 6 and "setup6" not in cfg:
        # guarda o valor ORIGINAL (ex.: "week5"), para o uninstall restaurar exatamente
        cfg["setup6"] = {"phase_before": cfg.get("phase_completed", 0)}
    if anterior < 6:  # nunca reduz um valor existente maior
        cfg["phase_completed"] = 6
    write_config_atomic(cfg)
    print(f"✅ phase_completed = {cfg['phase_completed']}")

    perfil = json.loads(PERFIL.read_text())
    ad_account = read_ad_account()
    kpis_lista = ", ".join(k["key"] for k in perfil["kpis"])
    metas_resumo = " | ".join(f"{k['label']} {fmt_target(k)}" for k in perfil["kpis"])

    url = "http://localhost:8888/paid-traffic-dashboard-7d.html"
    try:
        webbrowser.open(url)
    except Exception:
        pass

    print(f"""
Setup 6 concluido!

O que voce tem agora:
- MCP oficial Meta conectado a conta {ad_account}
- 6 skills instaladas (5 especialistas + 1 agente orquestrador)
- Dashboard rodando em http://localhost:8888 (atualiza 8h/13h/19h)
- Estrategia decide() ativa nos KPIs: {kpis_lista}
- Metas configuradas: {metas_resumo}

Comandos do dia a dia:
/agente-trafego-pago        menu completo
/meta-campaign-launcher     criar nova campanha
/meta-creative-brief        gerar briefing
/meta-metrics-fetcher       atualizar dashboard agora
/meta-performance-analyzer  analise da semana
/meta-budget-optimizer      plano de realocacao

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Voce acabou de plugar trafego pago direto no Claude Code.
Conheca o ZX Control completo — mentoria semanal + todos os setups:
👉 https://zxlab.com.br/mission-control

Nos vemos no proximo setup!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


if __name__ == "__main__":
    main()
