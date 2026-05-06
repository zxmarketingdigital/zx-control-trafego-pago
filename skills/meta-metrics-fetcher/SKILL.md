---
name: meta-metrics-fetcher
description: "Coleta métricas das campanhas Meta ADS via MCP oficial e atualiza o JSON do dashboard local. Lê o perfil do aluno (~/.operacao-ia/config/meta_perfil.json) para puxar APENAS os KPIs configurados (CPL, CPA, ROAS, custo/msg, CPM, CTR, etc.) — nada genérico, nada hardcoded. Use SEMPRE que o aluno disser: atualizar metricas meta, sync metricas, baixar metricas meta, atualizar dashboard meta, refresh meta, refresh dashboard, fetch meta, atualizar trafego pago."
model: sonnet
effort: high
---

# Meta Metrics Fetcher

Coleta métricas Meta ADS adaptadas ao perfil do aluno e atualiza JSON do dashboard.

## Pré-requisitos

- `~/.operacao-ia/config/meta_perfil.json` existe
- MCP `mcp__meta-official__*` autenticado

## Fluxo

1. Leia `meta_perfil.json` → extraia `kpis`, `windows`, `ad_account_id`, `objectives`
2. Para cada janela em `windows` (ex: 4, 7, 14, 30 dias):
   - Calcule `time_range = {since: hoje-N, until: hoje}`
   - Determine os campos `fields` necessários (mapeamento abaixo)
   - Chame `mcp__meta-official__ads_insights_*` com `level=ad`, `time_range`, `fields`, `filtering=[{field:'effective_status',operator:'IN',value:['ACTIVE','PAUSED']}]`
   - Se `objectives` inclui `LEAD_GENERATION`, também chame `ads_get_ad_entities` para enriquecer com leads
3. Calcule cada KPI por ad usando o mapeamento (abaixo)
4. Aplique `decide()` por ad (lê `scale_at`/`kill_at` de cada KPI no perfil)
5. Agregue: ad → adset → campaign → conta
6. Calcule `kpis_summary` no topo (média ponderada por spend, comparação vs target, status verde/amarelo/vermelho)
7. Grave `~/.operacao-ia/dashboards/paid-traffic-{N}d.json` por janela
8. Reporte ao aluno: linhas processadas, status por KPI, próxima execução automática

## Mapeamento KPI → fields da API + cálculo

| KPI key | Campos pedidos | Cálculo |
|---|---|---|
| `cpl` | `spend`, `actions{type:lead}` | `spend / leads` |
| `cpa` | `spend`, `actions{type:purchase}` | `spend / purchases` |
| `roas` | `spend`, `action_values{type:purchase}` | `purchase_value / spend` |
| `cost_per_msg` | `spend`, `actions{type:onsite_conversion.messaging_conversation_started_7d}` | `spend / msgs` |
| `cpm` | `cpm` | direto |
| `ctr` | `ctr` | direto |
| `cpc` | `cpc` | direto |
| `frequency` | `frequency` | direto |
| `cost_per_install` | `spend`, `actions{type:mobile_app_install}` | `spend / installs` |

## decide() por ad

Dado KPI primário do perfil:
- **better=lower**: SCALE se `value ≤ target × scale_at` AND `spend ≥ target × 1.2`; KILL se `value > target × kill_at` OR (`spend > target × 3` AND zero conversões); senão KEEP
- **better=higher**: SCALE se `value ≥ target × (2 - scale_at)`; KILL se `value < target × (2 - kill_at)`; senão KEEP

Inclua `decide_reason` legível ("CPL 28% abaixo da meta + amostra suficiente").

## Schema de saída

Ver PLAN.md → seção "Schema paid-traffic-{N}d.json".

## Output ao aluno

```
✅ Métricas atualizadas

Janelas: 4d, 7d, 14d, 30d
Conta: act_xxxxx
Ads ativos: 23

Status geral (janela 7d):
  CPL:           R$20,40  (meta R$25)   🟢 -18,4%
  Custo/Msg:     R$12,50  (meta R$10)   🔴 +25,0%
  CTR:            1,70%   (meta 1,5%)   🟢 +13,3%

Próxima atualização automática: hoje 19h05 BRT

Abra o dashboard: http://localhost:8888/paid-traffic-dashboard-7d.html
```

## Erros

- MCP não autenticado → oriente "rode `python3 setup/setup_meta_oauth.py` para reconectar"
- `meta_perfil.json` não existe → "rode Etapa 2 do Setup primeiro"
- Conta sem dados na janela → JSON com `campaigns:[]` e mensagem "sem campanhas ativas na janela"
