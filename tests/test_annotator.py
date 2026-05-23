"""Tests for sqlmigrate_audit.annotator."""

import pytest

from sqlmigrate_audit.annotator import (
    Annotation,
    add_annotation,
    annotate_in_registry,
    get_annotations,
)
from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry


@pytest.fixture()
def base_record() -> MigrationRecord:
    return MigrationRecord(
        migration_id="m001",
        description="Create users table",
        status=MigrationStatus.APPLIED,
        applied_at="2024-01-10T12:00:00",
        author="alice",
        tags=["core"],
    )


@pytest.fixture()
def populated_registry(base_record: MigrationRecord) -> MigrationRegistry:
    reg = MigrationRegistry()
    reg.register(base_record)
    extra = MigrationRecord(
        migration_id="m002",
        description="Add email column",
        status=MigrationStatus.PENDING,
        author="bob",
    )
    reg.register(extra)
    return reg


# --- add_annotation ---

def test_add_annotation_encodes_as_tag(base_record):
    updated = add_annotation(base_record, "bob", "Reviewed OK", "2024-03-01T09:00:00")
    assert any(t.startswith("note:bob:2024-03-01T09:00:00:") for t in updated.tags)


def test_add_annotation_does_not_mutate_original(base_record):
    add_annotation(base_record, "bob", "Reviewed", "2024-03-01T09:00:00")
    assert all(not t.startswith("note:") for t in base_record.tags)


def test_add_annotation_preserves_existing_tags(base_record):
    updated = add_annotation(base_record, "bob", "LGTM", "2024-03-01T10:00:00")
    assert "core" in updated.tags


def test_add_annotation_empty_author_raises(base_record):
    with pytest.raises(ValueError, match="author"):
        add_annotation(base_record, "", "note", "2024-01-01T00:00:00")


def test_add_annotation_empty_note_raises(base_record):
    with pytest.raises(ValueError, match="note"):
        add_annotation(base_record, "alice", "", "2024-01-01T00:00:00")


def test_add_annotation_empty_created_at_raises(base_record):
    with pytest.raises(ValueError, match="created_at"):
        add_annotation(base_record, "alice", "some note", "")


# --- get_annotations ---

def test_get_annotations_returns_empty_for_plain_tags(base_record):
    assert get_annotations(base_record) == []


def test_get_annotations_parses_encoded_tag(base_record):
    updated = add_annotation(base_record, "carol", "Needs review", "2024-04-01T08:00:00")
    annotations = get_annotations(updated)
    assert len(annotations) == 1
    ann = annotations[0]
    assert ann.author == "carol"
    assert ann.note == "Needs review"
    assert ann.created_at == "2024-04-01T08:00:00"


def test_get_annotations_handles_colon_in_note(base_record):
    updated = add_annotation(base_record, "dave", "See: PR#42", "2024-05-01T00:00:00")
    annotations = get_annotations(updated)
    assert annotations[0].note == "See: PR#42"


def test_get_annotations_multiple(base_record):
    r1 = add_annotation(base_record, "alice", "First note", "2024-01-01T00:00:00")
    r2 = add_annotation(r1, "bob", "Second note", "2024-01-02T00:00:00")
    assert len(get_annotations(r2)) == 2


# --- annotate_in_registry ---

def test_annotate_in_registry_updates_correct_record(populated_registry):
    new_reg = annotate_in_registry(
        populated_registry, "m001", "eve", "Checked", "2024-06-01T00:00:00"
    )
    updated = new_reg.get("m001")
    assert updated is not None
    assert len(get_annotations(updated)) == 1


def test_annotate_in_registry_does_not_affect_other_records(populated_registry):
    new_reg = annotate_in_registry(
        populated_registry, "m001", "eve", "Checked", "2024-06-01T00:00:00"
    )
    other = new_reg.get("m002")
    assert other is not None
    assert get_annotations(other) == []


def test_annotate_in_registry_missing_id_raises(populated_registry):
    with pytest.raises(KeyError, match="m999"):
        annotate_in_registry(
            populated_registry, "m999", "eve", "Oops", "2024-06-01T00:00:00"
        )
