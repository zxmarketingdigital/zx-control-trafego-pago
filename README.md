# ZX Control — Setup 6: Tráfego Pago Meta ADS

Setup oficial da Semana 6 do ZX Control 2.0 Growth. Instala operação técnica completa de tráfego pago Meta ADS direto no Claude Code do aluno.

## Pré-requisitos

- macOS (Linux/Windows funcionam parcialmente — sem LaunchAgents)
- Setup 5 do ZX Control concluído (`phase_completed >= 5` em `~/.operacao-ia/config/config.json`)
- Python 3.9+
- Claude Code com MCP oficial Meta disponível (`mcp__meta-official__*`)
- Conta Meta Business + Ad Account ativa

## Instalação

```bash
git clone https://github.com/zxmarketingdigital/zx-control-trafego-pago
cd zx-control-trafego-pago
claude
```

Ao abrir o Claude, ele vai aguardar você digitar **`INICIAR SETUP SEMANA 6`** para começar.

A partir daí o setup é guiado — 10 etapas, cada uma com explicação + execução + validação.

## O que será instalado

- **MCP oficial Meta** conectado via OAuth
- **5 skills + 1 agente orquestrador** em `~/.claude/skills/`:
  - `agente-trafego-pago` (orquestrador)
  - `meta-campaign-launcher`
  - `meta-creative-brief`
  - `meta-metrics-fetcher`
  - `meta-performance-analyzer`
  - `meta-budget-optimizer`
- **Perfil de campanhas personalizado** (`~/.operacao-ia/config/meta_perfil.json`) — métricas, metas e estratégia decide() escolhidas pelo aluno
- **Dashboard local** em `http://localhost:8888` com KPIs do perfil
- **2 LaunchAgents** (macOS) — fetch 3x/dia + dashboard server keep-alive

## Estrutura

```
zx-control-trafego-pago/
├─ CLAUDE.md            # roteiro de instalação (lido pelo Claude Code)
├─ setup/               # 9 scripts Python das etapas
├─ skills/              # 6 SKILL.md
├─ scripts/             # fetch_metrics, dashboard generator, server starter
├─ docs/                # template HTML do dashboard
└─ launchagents/        # 2 plists macOS
```

## Comandos pós-instalação

```
/agente-trafego-pago        menu completo
/meta-campaign-launcher     criar nova campanha
/meta-creative-brief        gerar briefing criativo
/meta-metrics-fetcher       atualizar dashboard agora
/meta-performance-analyzer  análise da semana
/meta-budget-optimizer      plano de realocação
```

## Limitações conhecidas

- **MCP oficial Meta com rollout gradual**: nem toda conta tem `is_ads_mcp_enabled=true`. Setup detecta e oferece fallback via System User Token (`setup_meta_oauth.py --renew`).
- **LaunchAgents só macOS**: Linux/Windows precisam de cron/Task Scheduler manual. Etapa 9 detecta SO e pula automaticamente.
- **Pixel ZX LAB hardcoded em demo**: aluno deve substituir pelo pixel próprio em E1 — setup pergunta.
- **Conflito com creative-roas-dashboard**: se aluno tem outro fetcher Meta rodando, E9 detecta e oferece pular meta-fetch.plist (evita duplicar chamadas API).
- **Decide() exige amostra ≥1.2× da meta**: ads com gasto baixo aparecem como "amostra insuficiente". Espere 24-72h pra acumular dados antes de decidir.
- **Token Meta persiste em `~/.operacao-ia/config/meta.env` (chmod 600)**: System User Tokens não expiram automaticamente. Se token for invalidado (troca de senha, desautorização), rode `python3 setup/setup_meta_oauth.py --renew`.
- **Uninstall disponível**: `python3 setup/setup_uninstall.py` reverte o setup. Opção [A] preserva skills, [B] remove tudo.

## Suporte

Mentoria semanal ZX Control: https://zxlab.com.br/mission-control
