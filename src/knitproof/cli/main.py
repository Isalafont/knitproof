"""Point d’entrée `knitproof` : sous-commande `verify`, codes de sortie."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from knitproof.app.verification import PatternFileError, verify_pattern
from knitproof.cli.report import render

EXIT_NO_FINDING = 0
EXIT_FINDINGS = 1
EXIT_INVALID_FILE = 3


def main(argv: Sequence[str] | None = None) -> int:
    """Lance la commande ; renvoie le code de sortie."""
    args = _parser().parse_args(argv)
    try:
        findings = verify_pattern(args.pattern)
    except PatternFileError as error:
        print(f"knitproof : {error}", file=sys.stderr)
        return EXIT_INVALID_FILE
    print(render(findings))
    return EXIT_FINDINGS if findings else EXIT_NO_FINDING


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="knitproof")
    commands = parser.add_subparsers(dest="command", required=True)
    verify = commands.add_parser("verify", help="vérifier les comptes d’un patron YAML")
    verify.add_argument("pattern", type=Path, help="fichier de patron YAML")
    return parser
