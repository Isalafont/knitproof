"""Point d’entrée `knitproof` : sous-commande `verify`, codes de sortie."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from knitproof.app.beanie import calc_beanie
from knitproof.app.errors import InputFileError
from knitproof.app.verification import verify_pattern
from knitproof.cli.report import render, render_calc

EXIT_NO_FINDING = 0
EXIT_FINDINGS = 1
EXIT_INVALID_FILE = 3


def main(argv: Sequence[str] | None = None) -> int:
    """Lance la commande ; renvoie le code de sortie."""
    args = _parser().parse_args(argv)
    try:
        if args.command == "calc":
            return _calc(args.request)
        report = verify_pattern(args.pattern)
    except InputFileError as error:
        print(f"knitproof : {error}", file=sys.stderr)
        return EXIT_INVALID_FILE
    print(render(report))
    return EXIT_FINDINGS if report.entries else EXIT_NO_FINDING


def _calc(request: Path) -> int:
    """Code 1 : questions en attente, pas de plan ; les avis ne changent pas le code."""
    calc = calc_beanie(request)
    print(render_calc(calc))
    pending = calc.report.questions or calc.report.result is None
    return EXIT_FINDINGS if pending else EXIT_NO_FINDING


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="knitproof")
    commands = parser.add_subparsers(dest="command", required=True)
    verify = commands.add_parser("verify", help="vérifier les comptes d’un patron YAML")
    verify.add_argument("pattern", type=Path, help="fichier de patron YAML")
    calc = commands.add_parser("calc", help="calculer un bonnet depuis une demande YAML")
    calc.add_argument("request", type=Path, help="fichier de demande YAML")
    return parser
