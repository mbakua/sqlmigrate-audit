"""Tests for sqlmigrate_audit.tagger module."""

import pytest
from datetime import datetime, timezone
from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.tagger import (
    add_tag,
    remove_tag,
    list_all_tags,
    tag_counts,
    apply_tag_to_registry,
)


@pytest.fixture
def base_record():
    return MigrationRecord(
        migration_id="m001",
        description="Initial schema",
        status=MigrationStatus.APPLIED,
        applied_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        tags=["core", "schema"],
    )


@pytest.fixture
def populated_registry():
    reg = MigrationRegistry()
    reg.register(MigrationRecord(
        migration_id="m001", description="First",
        status=MigrationStatus.APPLIED, tags=["core", "v1"]
    ))
    reg.register(MigrationRecord(
        migration_id="m002", description="Second",
        status=MigrationStatus.PENDING, tags=["v1"]
    ))
    reg.register(MigrationRecord(
        migration_id="m003", description="Third",
        status=MigrationStatus.PENDING, tags=[]
    ))
    return reg


def test_add_tag_appends_new_tag(base_record):
    updated = add_tag(base_record, "hotfix")
    assert "hotfix" in updated.tags
    assert "core" in updated.tags


def test_add_tag_no_duplicate(base_record):
    updated = add_tag(base_record, "core")
    assert updated.tags.count("core") == 1


def test_add_tag_does_not_mutate_original(base_record):
    add_tag(base_record, "hotfix")
    assert "hotfix" not in base_record.tags


def test_remove_tag_removes_existing(base_record):
    updated = remove_tag(base_record, "core")
    assert "core" not in updated.tags
    assert "schema" in updated.tags


def test_remove_tag_noop_for_missing(base_record):
    updated = remove_tag(base_record, "nonexistent")
    assert updated.tags == base_record.tags


def test_list_all_tags_sorted(populated_registry):
    tags = list_all_tags(populated_registry)
    assert tags == ["core", "v1"]


def test_list_all_tags_empty_registry():
    empty = MigrationRegistry()
    assert list_all_tags(empty) == []


def test_tag_counts(populated_registry):
    counts = tag_counts(populated_registry)
    assert counts["v1"] == 2
    assert counts["core"] == 1


def test_apply_tag_to_registry(populated_registry):
    new_reg = apply_tag_to_registry(populated_registry, "release", ["m001", "m003"])
    assert "release" in new_reg.get("m001").tags
    assert "release" not in new_reg.get("m002").tags
    assert "release" in new_reg.get("m003").tags


def test_apply_tag_preserves_existing_tags(populated_registry):
    new_reg = apply_tag_to_registry(populated_registry, "release", ["m001"])
    assert "core" in new_reg.get("m001").tags
    assert "v1" in new_reg.get("m001").tags
