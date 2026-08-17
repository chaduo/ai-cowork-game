from sqlalchemy import inspect


def test_c14_schema_contains_human_review_and_restore_provenance(isolated_database) -> None:
    inspector = inspect(isolated_database)
    assert "human_play_reviews" in inspector.get_table_names()
    candidate_columns = {column["name"] for column in inspector.get_columns("build_candidates")}
    assert "source_playable_version_id" in candidate_columns
