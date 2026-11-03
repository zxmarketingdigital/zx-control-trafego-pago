#!/usr/bin/env python3
"""
Setup 6 — Etapa 0: Diagnóstico da Base
Verifica Python/gh (sem exigir nenhum setup anterior), garante config.json mínimo, cria estrutura de pastas, mostra plano das 10 etapas.
"""
import json
import os
import platform
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

OPERACAO = Path.home() / ".operacao-ia"
CONFIG = OPERACAO / "config" / "config.json"

REQUIRED_DIRS = [
    OPERACAO / "config",
    OPERACAO / "scripts" / "meta",
    OPERACAO / "dashboards",
    OPERACAO / "leads",
    OPERACAO / "logs",
]

ETAPAS = [
    "E0  Boas-vindas + Diagnóstico",
    "E1  Conectar MCP oficial Meta (OAuth)",
    "E2  Questionário: Perfil de Campanhas",
    "E3  Instalar Skills + Agente Orquestrador",
    "E4  Primeira coleta de métricas",
    "E5  Dashboard local (localhost:8888)",
    "E6  Skill: Criar Campanha",
    "E7  Skill: Briefing Criativo",
    "E8  Skills: Analyzer + Budget Optimizer",
    "E9  LaunchAgents (fetch 3x/dia + server)",
    "E10 Auditoria técnica + Finalização",
]


def check_python():
    if sys.version_info < (3, 9):
        print(f"❌ Python 3.9+ requerido. Você tem {sys.version_info.major}.{sys.version_info.minor}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True


def check_gh():
    if shutil.which("gh"):
        print("✅ gh CLI instalado")
        return True
    print("⚠️  gh CLI não encontrado (opcional, mas recomendado)")
    return True  # não bloqueia


class ConfigBackupError(OSError):
    """Nao foi possivel guardar copia de seguranca do config; o original NAO foi tocado."""


def backup_config_copy(path):
    """Copia (copy2) o config para <nome>.bak-<AAAAmmdd-HHMMSS>[-N], sem sobrescrever backup existente.

    Confere que o destino existe com o mesmo tamanho. Em falha, o original fica intacto
    e levanta ConfigBackupError (so entao o chamador pode recriar o config).
    """
    path = Path(path)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = None
    try:
        n = 0
        while backup is None:
            candidate = path.with_name("%s.bak-%s%s" % (path.name, stamp, "-%d" % n if n else ""))
            try:
                # O_EXCL: a criação é atômica; se outro processo pegou o nome, tenta o próximo sufixo.
                fd = os.open(str(candidate), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                n += 1
                continue
            backup = candidate
            with os.fdopen(fd, "wb") as dst, open(str(path), "rb") as src:
                shutil.copyfileobj(src, dst)
            os.chmod(str(backup), 0o600)  # backup nunca herda permissao aberta do original
        if not backup.is_file() or backup.stat().st_size != path.stat().st_size:
            raise OSError("copia de seguranca incompleta")
    except OSError as e:
        try:
            if backup is not None and backup.is_file():
                backup.unlink()
        except OSError:
            pass
        msg = (f"Não consegui salvar uma cópia de segurança de {path}: {e}. "
               "Verifique a permissão da pasta e rode de novo.")
        print(f"❌ {msg}")
        raise ConfigBackupError(msg) from e
    return backup


def parse_phase(value):
    """Interpreta phase_completed de forma tolerante: 5, 5.0, "5", "week5", "semana 5", "phase5". Invalido = 0."""
    if isinstance(value, bool):
        return 0
    try:
        number = float(value)
    except OverflowError:
        number = float("inf") if value > 0 else 0.0  # inteiro gigante: maior que qualquer fase, nunca sobrescreve
    except (TypeError, ValueError):
        achou = re.search(r"\d+(?:\.\d+)?", str(value))
        number = float(achou.group()) if achou else 0
    if number != number or number == float("-inf"):
        return 0
    return number


def write_config_atomic(cfg):
    """Grava o config.json por arquivo temporario no mesmo diretorio + os.replace (nunca deixa truncado)."""
    destino = os.path.realpath(str(CONFIG))
    tmp = "%s.tmp-%d" % (destino, os.getpid())
    try:
        try:
            os.unlink(tmp)  # sobra de execucao interrompida
        except FileNotFoundError:
            pass
        with os.fdopen(os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w", encoding="utf-8") as f:
            f.write(json.dumps(cfg, indent=2, ensure_ascii=False))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, destino)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def check_config():
    """Garante um config.json utilizavel. Este setup nao exige nenhum setup anterior.

    - Ausente: cria o minimo ({"phase_completed": 0}).
    - Corrompido: guarda copia em config.json.bak-<timestamp> e recria o minimo.
    - Valido (instalacao anterior): aproveita como esta, sem alterar.
    """
    try:
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        if not CONFIG.exists():
            try:
                fd = os.open(str(CONFIG), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                fd = None  # criado em paralelo por outra execucao: cai na leitura abaixo
            if fd is not None:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(json.dumps({"phase_completed": 0}, indent=2, ensure_ascii=False) + "\n")
                print("✅ Primeira instalação — config.json mínimo criado")
                return True
    except OSError as oe:
        print(f"❌ Não consegui criar o config.json ({oe}). Verifique a permissão da pasta {CONFIG.parent} e rode de novo.")
        return False
    try:
        cfg = json.loads(CONFIG.read_text())
        if not isinstance(cfg, dict):
            raise ValueError("config.json não é um objeto JSON")
    except Exception as e:
        try:
            backup = backup_config_copy(CONFIG)  # ConfigBackupError: original fica intacto
            print(f"⚠️  config.json inválido ({e}) — cópia guardada em {backup.name}")
            write_config_atomic({"phase_completed": 0})
            print("✅ config.json mínimo recriado")
        except ConfigBackupError:
            return False  # mensagem ja impressa; config original intacto
        except OSError as oe:
            print(f"❌ Não consegui recriar o config.json ({oe}). O original e a cópia de segurança foram preservados; verifique a permissão/espaço em disco e rode de novo.")
            return False
        return True
    print(f"✅ Instalação anterior encontrada (phase_completed={cfg.get('phase_completed', 0)}) — aproveitando o que for válido")
    return True


def create_dirs():
    for d in REQUIRED_DIRS:
        d.mkdir(parents=True, exist_ok=True)
    print(f"✅ Estrutura criada em {OPERACAO}/")


def show_plan():
    print("\n" + "=" * 60)
    print("PLANO DAS 10 ETAPAS — Setup 6 Tráfego Pago Meta ADS")
    print("=" * 60)
    for e in ETAPAS:
        print(f"  {e}")
    print("=" * 60)


def main():
    print(f"\n🔍 Diagnóstico inicial — {platform.system()} {platform.release()}\n")
    ok = all([check_python(), check_gh(), check_config()])
    if not ok:
        sys.exit(1)
    create_dirs()
    show_plan()
    print("\n✅ Etapa 0 concluída. Pronto para a Etapa 1 (Conectar MCP Meta).")


if __name__ == "__main__":
    main()
