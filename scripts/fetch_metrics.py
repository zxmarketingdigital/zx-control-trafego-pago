#!/usr/bin/env python3
"""
fetch_metrics.py — coleta métricas Meta ADS adaptadas ao perfil do aluno.

Como funciona:
- Lê ~/.operacao-ia/config/meta_perfil.json (KPIs, metas, janelas, conta)
- Lê access token do MCP oficial Meta em ~/.claude.json
- Para cada janela, chama Meta Graph API v21.0 (level=ad)
- Calcula KPIs configurados, aplica decide() conforme limiares do perfil
- Grava ~/.operacao-ia/dashboards/paid-traffic-{N}d.json

Modos:
  --check   : só valida config, não chama API
  (default) : roda fetch completo
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

OPERACAO = Path.home() / ".operacao-ia"
PERFIL = OPERACAO / "config" / "meta_perfil.json"
META_ENV = OPERACAO / "config" / "meta.env"
DASH_DIR = OPERACAO / "dashboards"
LOG = OPERACAO / "logs" / "meta-fetch.log"

GRAPH_BASE = "https://graph.facebook.com/v21.0"
BRT = timezone(timedelta(hours=-3))

KPI_FIELDS = {
    "cpl":             ["spend", "actions"],
    "cpa":             ["spend", "actions"],
    "roas":            ["spend", "action_values"],
    "cost_per_msg":    ["spend", "actions"],
    "cpm":             ["cpm"],
    "ctr":             ["ctr"],
    "cpc":             ["cpc"],
    "frequency":       ["frequency"],
    "cost_per_install":["spend", "actions"],
}

ACTION_TYPE_MAP = {
    "cpl":              "lead",
    "cpa":              "purchase",
    "roas":             "purchase",
    "cost_per_msg":     "onsite_conversion.messaging_conversation_started_7d",
    "cost_per_install": "mobile_app_install",
}


def log(msg):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(BRT).isoformat(timespec="seconds")
    line = f"[{ts}] {msg}\n"
    LOG.write_text((LOG.read_text() if LOG.exists() else "") + line)


def read_env(key):
    if not META_ENV.exists():
        return ""
    for line in META_ENV.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return ""


def read_token():
    """Lê access_token do MCP oficial Meta em ~/.claude.json."""
    cj = Path.home() / ".claude.json"
    if not cj.exists():
        return None
    try:
        data = json.loads(cj.read_text())
    except Exception:
        return None
    # Procura em mcpServers.meta-official.* — formato pode variar
    for key in ("mcpServers", "mcp_servers", "mcp"):
        block = data.get(key, {}) if isinstance(data, dict) else {}
        for name, cfg in (block or {}).items():
            if "meta" in name.lower():
                token = (cfg.get("access_token")
                         or cfg.get("token")
                         or cfg.get("env", {}).get("META_ACCESS_TOKEN"))
                if token:
                    return token
    # Fallback: env var direta
    return os.environ.get("META_ACCESS_TOKEN") or read_env("META_ACCESS_TOKEN")


def graph_get(path, params, token):
    params = {**params, "access_token": token}
    url = f"{GRAPH_BASE}/{path.lstrip('/')}?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "zx-control-trafego-pago/0.1"})
    try:
        with urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Graph API {e.code}: {body[:300]}")


def fetch_window(account_id, kpis, days, token):
    until = datetime.now(BRT).date()
    since = until - timedelta(days=days - 1)

    field_set = {"ad_id", "ad_name", "adset_id", "adset_name",
                 "campaign_id", "campaign_name", "objective",
                 "spend", "impressions", "clicks", "reach"}
    for k in kpis:
        for f in KPI_FIELDS.get(k["key"], []):
            field_set.add(f)

    params = {
        "level": "ad",
        "fields": ",".join(sorted(field_set)),
        "time_range": json.dumps({"since": since.isoformat(), "until": until.isoformat()}),
        "filtering": json.dumps([{"field": "ad.effective_status",
                                  "operator": "IN",
                                  "value": ["ACTIVE", "PAUSED"]}]),
        "limit": 500,
    }
    rows = []
    next_url = f"act_{account_id}/insights" if not str(account_id).startswith("act_") else f"{account_id}/insights"
    page = graph_get(next_url, params, token)
    rows.extend(page.get("data", []))
    while page.get("paging", {}).get("next"):
        url = page["paging"]["next"]
        req = Request(url, headers={"User-Agent": "zx-control-trafego-pago/0.1"})
        with urlopen(req, timeout=60) as r:
            page = json.loads(r.read().decode("utf-8"))
        rows.extend(page.get("data", []))
    return rows


def get_action_value(actions, action_type, value_field="value"):
    if not actions:
        return 0.0
    for a in actions:
        if a.get("action_type") == action_type:
            try:
                return float(a.get(value_field, 0) or 0)
            except (ValueError, TypeError):
                return 0.0
    return 0.0


def calc_kpi(row, kpi_key):
    spend = float(row.get("spend") or 0)
    if kpi_key == "cpm":
        return float(row.get("cpm") or 0)
    if kpi_key == "ctr":
        return float(row.get("ctr") or 0)
    if kpi_key == "cpc":
        return float(row.get("cpc") or 0)
    if kpi_key == "frequency":
        return float(row.get("frequency") or 0)

    action_type = ACTION_TYPE_MAP.get(kpi_key)
    if not action_type:
        return None

    if kpi_key == "roas":
        rev = get_action_value(row.get("action_values"), action_type)
        return (rev / spend) if spend > 0 else 0
    count = get_action_value(row.get("actions"), action_type)
    return (spend / count) if count > 0 else None


def decide(value, kpi_meta, spend):
    if value is None:
        return "KEEP-amostra", "amostra insuficiente"
    target = kpi_meta["target"]
    scale_at = kpi_meta.get("scale_at", 0.8)
    kill_at = kpi_meta.get("kill_at", 1.5)
    better = kpi_meta.get("better", "lower")
    min_spend = max(target * 1.2, 30)

    if spend < min_spend:
        return "KEEP-amostra", f"spend {spend:.2f} < min {min_spend:.2f}"

    if better == "lower":
        if value <= target * scale_at:
            return "SCALE", f"{kpi_meta['key']} {value:.2f} ≤ {target*scale_at:.2f} ({100*(target-value)/target:.0f}% abaixo da meta)"
        if value > target * kill_at:
            return "KILL", f"{kpi_meta['key']} {value:.2f} > {target*kill_at:.2f} ({100*(value-target)/target:.0f}% acima da meta)"
        return "KEEP", f"{kpi_meta['key']} {value:.2f} dentro da banda"
    else:
        if value >= target * (2 - scale_at):
            return "SCALE", f"{kpi_meta['key']} {value:.2f} ≥ {target*(2-scale_at):.2f} (acima da meta)"
        if value < target * (2 - kill_at):
            return "KILL", f"{kpi_meta['key']} {value:.2f} < {target*(2-kill_at):.2f} (muito abaixo)"
        return "KEEP", f"{kpi_meta['key']} {value:.2f} dentro da banda"


def status_color(value, kpi_meta):
    if value is None:
        return "gray"
    target = kpi_meta["target"]
    better = kpi_meta.get("better", "lower")
    delta = (value - target) / target if target else 0
    if better == "lower":
        if delta < -0.10:
            return "green"
        if delta < 0.10:
            return "yellow"
        return "red"
    else:
        if delta > 0.10:
            return "green"
        if delta > -0.10:
            return "yellow"
        return "red"


def aggregate(rows, perfil):
    """Agrupa rows ad → adset → campaign e calcula totais."""
    primary_kpi = perfil["primary_kpi"]
    kpi_meta_map = {k["key"]: k for k in perfil["kpis"]}
    primary_meta = kpi_meta_map[primary_kpi]

    # Por ad
    ads_by_campaign = {}
    for row in rows:
        cid = row.get("campaign_id")
        cname = row.get("campaign_name", "")
        objective = row.get("objective", "")
        asid = row.get("adset_id")
        asname = row.get("adset_name", "")
        ad = {
            "ad_id": row.get("ad_id"),
            "ad_name": row.get("ad_name", ""),
            "spend": float(row.get("spend") or 0),
            "impressions": int(row.get("impressions") or 0),
            "clicks": int(row.get("clicks") or 0),
            "reach": int(row.get("reach") or 0),
            "metrics": {},
            "daily": [],
        }
        for k in perfil["kpis"]:
            ad["metrics"][k["key"]] = calc_kpi(row, k["key"])

        primary_value = ad["metrics"].get(primary_kpi)
        d, reason = decide(primary_value, primary_meta, ad["spend"])
        ad["decide"] = d
        ad["decide_reason"] = reason

        ads_by_campaign.setdefault(cid, {
            "campaign_id": cid, "name": cname, "objective": objective,
            "spend": 0.0, "adsets": {}
        })
        camp = ads_by_campaign[cid]
        camp["spend"] += ad["spend"]
        adset = camp["adsets"].setdefault(asid, {
            "adset_id": asid, "name": asname, "spend": 0.0, "ads": []
        })
        adset["spend"] += ad["spend"]
        adset["ads"].append(ad)

    # Convert adsets dict → list
    campaigns = []
    for cid, camp in ads_by_campaign.items():
        adset_list = list(camp["adsets"].values())
        # decide() na campanha = pior decisão dos seus ads
        ads_decisions = [a["decide"] for adset in adset_list for a in adset["ads"]]
        if "KILL" in ads_decisions:
            cdec = "KILL"
        elif "SCALE" in ads_decisions:
            cdec = "SCALE"
        elif "KEEP" in ads_decisions:
            cdec = "KEEP"
        else:
            cdec = "KEEP-amostra"
        camp_metrics = {}
        for k in perfil["kpis"]:
            vals = [a["metrics"].get(k["key"]) for adset in adset_list for a in adset["ads"]
                    if a["metrics"].get(k["key"]) is not None and a["spend"] > 0]
            spends = [a["spend"] for adset in adset_list for a in adset["ads"]
                      if a["metrics"].get(k["key"]) is not None and a["spend"] > 0]
            if not vals:
                camp_metrics[k["key"]] = None
            else:
                # média ponderada por spend
                total_spend = sum(spends)
                camp_metrics[k["key"]] = sum(v * s for v, s in zip(vals, spends)) / total_spend if total_spend else None
        camp["adsets"] = adset_list
        camp["metrics"] = camp_metrics
        camp["decide"] = cdec
        campaigns.append(camp)

    # KPIs summary global
    total_spend = sum(c["spend"] for c in campaigns)
    kpis_summary = {}
    for k in perfil["kpis"]:
        vals = [a["metrics"].get(k["key"])
                for c in campaigns for adset in c["adsets"] for a in adset["ads"]
                if a["metrics"].get(k["key"]) is not None and a["spend"] > 0]
        spends = [a["spend"]
                  for c in campaigns for adset in c["adsets"] for a in adset["ads"]
                  if a["metrics"].get(k["key"]) is not None and a["spend"] > 0]
        if not vals or sum(spends) == 0:
            kpis_summary[k["key"]] = {"value": None, "target": k["target"], "delta_pct": None, "status": "gray"}
        else:
            value = sum(v * s for v, s in zip(vals, spends)) / sum(spends)
            delta = (value - k["target"]) / k["target"] * 100 if k["target"] else 0
            kpis_summary[k["key"]] = {
                "value": round(value, 4),
                "target": k["target"],
                "delta_pct": round(delta, 1),
                "status": status_color(value, k),
            }

    return campaigns, kpis_summary, total_spend


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Só valida config")
    args = parser.parse_args()

    if not PERFIL.exists():
        print("❌ ~/.operacao-ia/config/meta_perfil.json não existe. Rode E2.")
        sys.exit(1)

    perfil = json.loads(PERFIL.read_text())
    ad_account = perfil.get("ad_account_id") or read_env("META_AD_ACCOUNT_ID")
    if not ad_account or "XXXXX" in ad_account:
        print("❌ ad_account_id não configurado. Rode E1 (OAuth) e preencha META_AD_ACCOUNT_ID em meta.env.")
        sys.exit(1)

    token = read_token()
    if not token:
        print("⚠️  Access token Meta não encontrado em ~/.claude.json nem META_ACCESS_TOKEN env var.")
        print("   Reconecte o MCP: rode setup_meta_oauth.py (E1) ou exporte META_ACCESS_TOKEN.")
        if args.check:
            sys.exit(1)
        sys.exit(1)

    if args.check:
        print(f"✅ OK conta {ad_account}, {len(perfil['kpis'])} KPIs, janelas {perfil.get('windows', [])}")
        sys.exit(0)

    DASH_DIR.mkdir(parents=True, exist_ok=True)
    windows = perfil.get("windows", [4, 7, 14, 30])
    log(f"START fetch account={ad_account} windows={windows}")

    for days in windows:
        try:
            log(f"fetch window {days}d")
            rows = fetch_window(ad_account, perfil["kpis"], days, token)
            campaigns, kpis_summary, total_spend = aggregate(rows, perfil)
            out = {
                "generated_at": datetime.now(BRT).isoformat(timespec="seconds"),
                "window_days": days,
                "ad_account_id": ad_account,
                "currency": "BRL",
                "perfil_kpis": [k["key"] for k in perfil["kpis"]],
                "primary_kpi": perfil["primary_kpi"],
                "kpis_summary": kpis_summary,
                "spend_total": round(total_spend, 2),
                "campaigns": campaigns,
            }
            outfile = DASH_DIR / f"paid-traffic-{days}d.json"
            outfile.write_text(json.dumps(out, indent=2, ensure_ascii=False))
            print(f"✅ {outfile.name} — {len(rows)} ads, R${total_spend:.2f}")
            log(f"  -> {outfile.name} OK")
        except Exception as e:
            print(f"❌ janela {days}d falhou: {e}")
            log(f"  -> ERROR {e}")

    log("END")


if __name__ == "__main__":
    main()
