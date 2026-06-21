#!/usr/bin/env python3
"""Carimba lotes novos de criativos na linha do tempo.

Varre render_out/ por pastas de lote ainda nao indexadas, descobre a data e a
"alteracao que veio antes" (ultimo commit git antes do mtime da pasta) e cria
um atalho numerado NN-apos-<slug>-<DDmes>/ -> ../<pasta>, atualizando 00-MAPA.md.

Idempotente: rodar de novo nao duplica nada. Seguro: so cria symlinks, nunca
move/apaga. Uso:
    python3 _atualizar.py                  # auto-detecta e carimba o que faltar
    python3 _atualizar.py <pasta> "rotulo" # forca um lote com rotulo manual
"""
import os, re, sys, subprocess, datetime, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)              # render_out/
MAPA = os.path.join(HERE, "00-MAPA.md")

# pastas que NAO sao lotes de criativos (eval/infra/rascunho)
EXCLUI = {
    "_LINHA-DO-TEMPO", "golden", "best-of", "refvision-ab", "artifacts",
    "tests-e2e", "out", "_scratch", "__pycache__", "saidas-antigas",
}
MESES = ["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"]


def slug(txt):
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode()
    txt = re.sub(r"[^a-zA-Z0-9]+", "-", txt).strip("-").lower()
    return txt[:40] or "lote"


def commit_antes(ts):
    """Subject do ultimo commit antes do timestamp ts (epoch)."""
    iso = datetime.datetime.fromtimestamp(ts).isoformat()
    try:
        out = subprocess.run(
            ["git", "-C", ROOT, "log", "-1", f"--before={iso}",
             "--pretty=format:%s"],
            capture_output=True, text=True, check=True).stdout.strip()
        # tira o prefixo "feat(x): " / "fix: " etc.
        return re.sub(r"^[a-z]+(\([^)]*\))?:\s*", "", out) or "alteracao"
    except Exception:
        return "alteracao"


def ja_indexados():
    """Conjunto de basenames de pasta ja apontados por algum atalho."""
    alvos = set()
    for dirpath, dirs, _ in os.walk(HERE):
        for d in dirs + [f for f in os.listdir(dirpath)]:
            p = os.path.join(dirpath, d)
            if os.path.islink(p):
                alvos.add(os.path.basename(os.path.realpath(p)))
    return alvos


def proximo_n():
    n = 0
    for nome in os.listdir(HERE):
        m = re.match(r"(\d{2})-", nome)
        if m:
            n = max(n, int(m.group(1)))
    return n + 1


def lotes_candidatos():
    out = []
    for nome in sorted(os.listdir(ROOT)):
        p = os.path.join(ROOT, nome)
        if not os.path.isdir(p) or nome in EXCLUI or nome.startswith("."):
            continue
        out.append((nome, os.path.getmtime(p)))
    out.sort(key=lambda x: x[1])  # cronologico
    return out


def carimba(nome, rotulo=None):
    p = os.path.join(ROOT, nome)
    ts = os.path.getmtime(p)
    dt = datetime.datetime.fromtimestamp(ts)
    rotulo = rotulo or commit_antes(ts)
    n = proximo_n()
    data = f"{dt.day:02d}{MESES[dt.month-1]}"
    link = f"{n:02d}-apos-{slug(rotulo)}-{data}"
    dest = os.path.join(HERE, link)
    os.symlink(os.path.join("..", nome), dest)
    print(f"+ {link}/ -> ../{nome}   (apos: {rotulo})")
    with open(MAPA, "a", encoding="utf-8") as f:
        f.write(f"| {n:02d} | `{link}/` | `{nome}/` | {dt.day:02d}/{MESES[dt.month-1]} "
                f"| Apos: {rotulo} |\n")
    return link


def main():
    if len(sys.argv) >= 2:  # modo manual
        carimba(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
        return
    indexados = ja_indexados()
    novos = [(n, t) for n, t in lotes_candidatos() if n not in indexados]
    if not novos:
        print("Nada novo — linha do tempo ja esta em dia.")
        return
    for nome, _ in novos:
        carimba(nome)


if __name__ == "__main__":
    main()
