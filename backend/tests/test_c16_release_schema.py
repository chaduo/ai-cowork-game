from sqlalchemy import inspect


def test_c16_release_snapshot_and_extraction_batch_schema(isolated_database) -> None:
    inspector = inspect(isolated_database)

    release_columns = {column["name"] for column in inspector.get_columns("releases")}
    assert {
        "name",
        "description",
        "game_design_revision_id",
        "gamespec_revision_id",
        "artifact_path",
        "artifact_checksum",
    } <= release_columns

    assert "resource_extraction_batches" in inspector.get_table_names()
    batch_columns = {column["name"] for column in inspector.get_columns("resource_extraction_batches")}
    assert {
        "id",
        "release_id",
        "status",
        "candidate_count",
        "error_code",
        "error_message",
        "created_at",
        "updated_at",
    } <= batch_columns

    unique_constraints = inspector.get_unique_constraints("resource_extraction_batches")
    assert any(set(item["column_names"]) == {"release_id"} for item in unique_constraints)
