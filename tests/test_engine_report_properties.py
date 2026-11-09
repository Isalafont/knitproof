"""Propriétés de `build_report` : déterminisme, ordre, conservation (CLA-69)."""

from hypothesis import given
from hypothesis import strategies as st

from knitproof.domain.report import DecidedBy, ReportEntry, ReportStatus
from knitproof.engine.report import build_report

ENTRIES = st.builds(
    ReportEntry,
    status=st.sampled_from(ReportStatus),
    code=st.text(min_size=1, max_size=8),
    round=st.none() | st.integers(min_value=1, max_value=200),
    lines=st.lists(st.text(max_size=20), max_size=3).map(tuple),
    decided_by=st.sampled_from(DecidedBy),
)


@given(st.lists(ENTRIES, max_size=12))
def test_same_input_gives_the_same_report(entries: list[ReportEntry]) -> None:
    assert build_report(entries) == build_report(list(entries))


@given(st.lists(ENTRIES, max_size=12))
def test_the_order_of_entry_is_kept(entries: list[ReportEntry]) -> None:
    assert build_report(entries).entries == tuple(entries)


@given(st.lists(ENTRIES, max_size=12))
def test_no_entry_is_lost(entries: list[ReportEntry]) -> None:
    assert len(build_report(entries).entries) == len(entries)
