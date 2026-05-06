#!/usr/bin/env python3
"""
Setup 6 — Etapa 9: LaunchAgents (macOS)
Instala 2 plists em ~/Library/LaunchAgents e dá launchctl load.
Substitui placeholders {HOME} e {PYTHON} no template.
"""
import platform
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLIST_SRC = REPO_ROOT / "launchagents"
LAUNCH_DST = Path.home() / "Library" / "LaunchAgents"

PLISTS = [
    "com.zxlab.meta-fetch.plist",
    "com.zxlab.meta-dashboard-server.plist",
]


def main():
    if platform.system() != "Darwin":
        print(f"⚠️  LaunchAgents é macOS-only. Você está em {platform.system()}.")
        print("   Pule esta etapa. No Linux/Windows, use cron ou Task Scheduler manualmente.")
        sys.exit(0)

    LAUNCH_DST.mkdir(parents=True, exist_ok=True)
    home = str(Path.home())
    python = sys.executable

    for name in PLISTS:
        src = PLIST_SRC / name
        dst = LAUNCH_DST / name
        if not src.exists():
            print(f"❌ Plist faltando: {src}")
            sys.exit(1)

        content = src.read_text().replace("{HOME}", home).replace("{PYTHON}", python)
        dst.write_text(content)
        print(f"✅ {dst.name}")

        # unload (silent) então load
        subprocess.run(["launchctl", "unload", str(dst)], capture_output=True)
        result = subprocess.run(["launchctl", "load", str(dst)], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"   ⚠️  load retornou: {result.stderr.strip()}")

    print("\n📋 Validando jobs ativos...")
    result = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    active = [l for l in result.stdout.splitlines() if "zxlab.meta" in l]
    for line in active:
        print(f"   {line}")

    if len(active) >= 2:
        print(f"\n✅ {len(active)} jobs ativos.")
    else:
        print(f"\n⚠️  Esperava 2, encontrou {len(active)}. Rode `launchctl list | grep zxlab.meta` manualmente.")

    print("\nPronto para a Etapa 10 (auditoria + finalização).")


if __name__ == "__main__":
    main()
