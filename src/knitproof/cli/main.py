"""Point d’entrée `knitproof` : sous-commandes `calc`, `verify` et `eval`, codes de sortie."""

import argparse
import datetime
import os
import sys
import time
from collections.abc import Sequence
from importlib.resources import files
from pathlib import Path

from knitproof.app.baseline import BaselineError, run_baseline, write_result
from knitproof.app.beanie import calc_beanie
from knitproof.app.errors import InputFileError
from knitproof.app.eval_cases import Split
from knitproof.app.verification import verify_pattern
from knitproof.cli.report import render, render_baseline, render_calc

EXIT_NO_FINDING = 0
EXIT_FINDINGS = 1
EXIT_INVALID_FILE = 3


def main(argv: Sequence[str] | None = None) -> int:
    """Lance la commande ; renvoie le code de sortie."""
    args = _parser().parse_args(argv)
    if args.command == "eval":
        return _eval(args.split, args.models, args.results)
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


def _eval(split: str, models: str, results: Path) -> int:
    """Code 3 : configuration invalide, erreur du fournisseur ou résultat déjà écrit."""
    names = [name.strip() for name in models.split(",")]
    try:
        result = run_baseline(
            Split(split),
            files("knitproof") / "evals" / "data",
            names,
            os.environ,
            clock=time.monotonic,
            now=_now,
        )
        written = write_result(result, results)
    except BaselineError as error:
        print(f"knitproof : {error}", file=sys.stderr)
        return EXIT_INVALID_FILE
    print(render_baseline(result, written))
    return EXIT_NO_FINDING


def _now() -> datetime.datetime:
    return datetime.datetime.now().astimezone()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="knitproof")
    commands = parser.add_subparsers(dest="command", required=True)
    verify = commands.add_parser("verify", help="vérifier les comptes d’un patron YAML")
    verify.add_argument("pattern", type=Path, help="fichier de patron YAML")
    calc = commands.add_parser("calc", help="calculer un bonnet depuis une demande YAML")
    calc.add_argument("request", type=Path, help="fichier de demande YAML")
    measure = commands.add_parser("eval", help="mesurer la ligne de base « LLM seul »")
    measure.add_argument("--split", choices=[split.value for split in Split], required=True)
    measure.add_argument("--models", required=True, help="fournisseurs séparés par des virgules")
    measure.add_argument(
        "--results", type=Path, default=Path("evals/results"), help="dossier des résultats"
    )
    return parser
