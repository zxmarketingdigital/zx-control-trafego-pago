#!/usr/bin/env python3
"""
Setup 6 — Etapa 3: Instalar Skills + Agente Orquestrador
Copia 6 SKILL.md (5 especialistas + 1 agente) para ~/.claude/skills/.
"""
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_SRC = REPO_ROOT / "skills"
SKILLS_DST = Path.home() / ".claude" / "skills"

EXPECTED = [
    "agente-trafego-pago",
    "meta-campaign-launcher",
    "meta-creative-brief",
    "meta-metrics-fetcher",
    "meta-performance-analyzer",
    "meta-budget-optimizer",
]


def main():
    if not SKILLS_SRC.exists():
        print(f"❌ Pasta skills/ não encontrada em {SKILLS_SRC}")
        sys.exit(1)

    SKILLS_DST.mkdir(parents=True, exist_ok=True)
    installed = []
    for slug in EXPECTED:
        src = SKILLS_SRC / slug
        dst = SKILLS_DST / slug
        if not src.exists():
            print(f"❌ Skill faltando no repo: {slug}")
            sys.exit(1)
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        installed.append(slug)

    print("\n✅ Skills instaladas em ~/.claude/skills/")
    for slug in installed:
        print(f"   • /{slug}")

    print(f"\n{len(installed)} skills + agente prontos.")
    print("Pronto para a Etapa 4 (primeira coleta de métricas).")


if __name__ == "__main__":
    main()
