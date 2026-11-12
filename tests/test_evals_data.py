"""Les données d’évaluation livrées se chargent (CLA-126, CA2)."""

from knitproof.evals.manifest import Split, load_eval_sets


def test_the_shipped_data_loads() -> None:
    sets = load_eval_sets()
    assert [case.id for case in sets[Split.DEV]] == ["exemple-bonnet-3-ans"]
    assert sets[Split.TEST] == ()
