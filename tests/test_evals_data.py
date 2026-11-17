"""Les données d’évaluation livrées se chargent (CLA-126, CA2)."""

from importlib.resources import files

from knitproof.app.eval_cases import Split, load_eval_sets

DATA = files("knitproof") / "evals" / "data"


def test_the_shipped_data_loads() -> None:
    sets = load_eval_sets(DATA)
    assert [case.id for case in sets[Split.DEV]] == ["exemple-bonnet-3-ans"]
    assert sets[Split.TEST] == ()
