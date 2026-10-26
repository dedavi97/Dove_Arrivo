"""Commit e push del solo file dati."""
import subprocess


def _git(radice, *argomenti):
    return subprocess.run(["git", *argomenti], cwd=radice, capture_output=True, text=True, encoding="utf-8")


def messaggio_commit(data):
    return f"data: aggiornamento rete {data:%d/%m/%Y}"


def pubblica(radice, file_dati, data):
    """Restituisce (riuscito, spiegazione)."""
    relativo = file_dati.relative_to(radice).as_posix()
    if _git(radice, "remote", "get-url", "origin").returncode != 0:
        return False, "il collegamento a GitHub (remote 'origin') non è ancora configurato."
    passi = [
        ("preparazione", ("add", "--", relativo)),
        ("salvataggio (commit)", ("commit", "--only", "-m", messaggio_commit(data), "--", relativo)),
        ("invio a GitHub (push)", ("push",)),
    ]
    for nome, argomenti in passi:
        esito = _git(radice, *argomenti)
        if esito.returncode != 0:
            return False, f"{nome} non riuscito:\n{(esito.stderr or esito.stdout).strip()}"
    return True, "pubblicato. Il sito si aggiorna entro qualche minuto."
