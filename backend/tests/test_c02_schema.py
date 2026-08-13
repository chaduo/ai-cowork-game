from sqlalchemy import inspect


def test_c02_migration_creates_lifecycle_tables(isolated_database) -> None:
    table_names = set(inspect(isolated_database).get_table_names())

    assert {
        "projects",
        "game_designs",
        "game_spec_revisions",
        "builds",
        "build_candidates",
        "playable_versions",
        "releases",
    }.issubset(table_names)

    project_columns = {column["name"] for column in inspect(isolated_database).get_columns("projects")}
    assert {"id", "current_playable_version_id", "active_build_id", "archived_at"}.issubset(project_columns)

    indexes = inspect(isolated_database).get_unique_constraints("game_spec_revisions")
    assert any(
        set(index["column_names"]) == {"project_id", "revision_number"}
        for index in indexes
    )
