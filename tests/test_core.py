import pytest

from motionguru.core import kept_intervals, make_silence_proposals, validate_proposals


def test_no_proposals_keeps_whole_video():
    assert kept_intervals({"duration": 10, "proposals": []}) == [(0.0, 10.0)]


def test_approved_cut_keeps_before_and_after():
    doc = {"duration": 10, "proposals": [
        {"id": "cut-001", "start": 3, "end": 5, "decision": "cut"},
    ]}
    assert kept_intervals(doc) == [(0, 3.0), (5.0, 10.0)]


def test_pending_cut_blocks_export():
    doc = {"duration": 10, "proposals": [
        {"id": "cut-001", "start": 3, "end": 5, "decision": "pending"},
    ]}
    with pytest.raises(ValueError, match="Unreviewed"):
        kept_intervals(doc)


def test_kept_proposal_does_not_cut():
    doc = {"duration": 10, "proposals": [
        {"id": "cut-001", "start": 3, "end": 5, "decision": "keep"},
    ]}
    assert kept_intervals(doc) == [(0.0, 10.0)]


def test_invalid_overlap_rejected():
    doc = {"duration": 10, "proposals": [
        {"id": "a", "start": 1, "end": 5, "decision": "cut"},
        {"id": "b", "start": 4, "end": 6, "decision": "keep"},
    ]}
    with pytest.raises(ValueError, match="non-overlapping"):
        validate_proposals(doc)


def test_silence_proposals_are_pending():
    items = make_silence_proposals([(0, 1), (4, 5.5)], 10)
    assert len(items) == 2
    assert all(item["decision"] == "pending" for item in items)
    assert items[0]["start"] > 0
