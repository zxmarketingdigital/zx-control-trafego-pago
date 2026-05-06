---
name: meta-campaign-launcher
description: "Cria campanha Meta ADS em DRAFT (campaign + ad set + ad) via MCP oficial Meta. Pergunta objetivo (a partir das opções do perfil do aluno), orçamento diário, audiência e criativo. Não publica — deixa em PAUSED para o aluno revisar no Ads Manager. Use SEMPRE que o aluno disser: criar campanha meta, lançar anúncio, novo ad set, subir criativo, campanha facebook, campanha instagram, anúncio meta, criar campanha lead, criar campanha whatsapp, criar campanha venda."
model: sonnet
effort: high
---

# Meta Campaign Launcher

Cria uma campanha Meta ADS em DRAFT (status PAUSED). O aluno publica manualmente depois.

## Pré-requisitos

- `~/.operacao-ia/config/meta_perfil.json` existe (objetivos do aluno)
- MCP `mcp__meta-official__*` autenticado (`ads_get_ad_accounts` retorna conta)

## Fluxo

1. Leia `meta_perfil.json` → liste apenas os `objectives` que o aluno marcou como opções válidas
2. Pergunte: objetivo, nome da campanha, orçamento diário (CBO ou ABO), audiência (interesse/lookalike/custom_audience_id), criativo (URL imagem/video, copy, CTA, link destino)
3. Confirme com o aluno todos os parâmetros antes de criar
4. Chame em sequência:
   - `mcp__meta-official__ads_create_campaign(account_id, name, objective, status="PAUSED", special_ad_categories=[])`
   - `mcp__meta-official__ads_create_ad_set(campaign_id, name, daily_budget, optimization_goal, billing_event, targeting, status="PAUSED")`
   - `mcp__meta-official__ads_create_ad(adset_id, name, creative, status="PAUSED")`
5. Devolva ao aluno: campaign_id, adset_id, ad_id, link direto Ads Manager

## Mapeamento de objetivos (perfil → Meta)

| Perfil aluno | Meta objective | optimization_goal | billing_event |
|---|---|---|---|
| LEAD_GENERATION | `OUTCOME_LEADS` | `LEAD_GENERATION` | `IMPRESSIONS` |
| MESSAGES (WhatsApp/DM) | `OUTCOME_ENGAGEMENT` | `CONVERSATIONS` | `IMPRESSIONS` |
| SALES | `OUTCOME_SALES` | `OFFSITE_CONVERSIONS` | `IMPRESSIONS` |
| AWARENESS | `OUTCOME_AWARENESS` | `REACH` | `IMPRESSIONS` |
| TRAFFIC | `OUTCOME_TRAFFIC` | `LINK_CLICKS` | `LINK_CLICKS` |
| APP_INSTALL | `OUTCOME_APP_PROMOTION` | `APP_INSTALLS` | `IMPRESSIONS` |

## Output

```
✅ Campanha criada em DRAFT (PAUSED)

ID: {campaign_id}
Nome: {name}
Objetivo: {objective}
Orçamento: R${daily_budget}/dia
Status: PAUSED

Ad Set ID: {adset_id}
Ad ID: {ad_id}

Próximo passo:
1. Abra https://business.facebook.com/adsmanager/manage/ads?act={ad_account_id}
2. Localize "{name}" e revise targeting + criativo
3. Mude status para ACTIVE quando estiver pronto

⚠️ Nada começa a gastar até você ativar manualmente.
```

## Erros comuns

- `(#100) Invalid parameter` → audiência inválida ou criativo malformado. Mostre o erro completo e peça para revisar
- `(#200) Permissions error` → reautentique MCP via `mcp__meta-official__authenticate`
- `Ad account suspended` → conta bloqueada, oriente o aluno a abrir suporte Meta
