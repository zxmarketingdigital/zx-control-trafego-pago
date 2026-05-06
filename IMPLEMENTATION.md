# IMPLEMENTATION.md

## v0.1.0 — Lançamento inicial (2026-05-06)

Setup 6 do ZX Control 2.0 Growth — Tráfego Pago Meta ADS.

### Componentes entregues

- `CLAUDE.md` student-facing modelado em `zx-control-semana3` (header guard + boas-vindas + 8 regras + 10 etapas + finalização com CTA ZX Control)
- 9 setup scripts Python (`setup/setup_*.py`)
- 6 skills (`skills/{agente-trafego-pago,meta-*}/SKILL.md`)
- 3 scripts core (`scripts/fetch_metrics.py`, `paid_traffic_dashboard.py`, `start_dashboard.sh`)
- 1 dashboard HTML template (`docs/paid-traffic-dashboard-template.html`)
- 2 LaunchAgents (`launchagents/com.zxlab.meta-{fetch,dashboard-server}.plist`)

### Decisões técnicas

- MCP único = `mcp__meta-official__*` (sem fallback `meta_ads__*`)
- Skills todas `sonnet/high`
- Dashboard adapta colunas dinamicamente conforme `meta_perfil.json` do aluno
- decide() configurável por aluno (limiares `scale_at` e `kill_at` por KPI)
- Sem aulas teóricas — só mentoria de instalação técnica
