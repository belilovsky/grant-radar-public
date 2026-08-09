from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    select,
)

from core.run_recorder_adapter import RunRecorder


def _runs_table(engine):
    metadata = MetaData()
    runs = Table(
        "runs",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("source", String(255), nullable=False),
        Column("started_at", DateTime(timezone=True), nullable=False),
        Column("finished_at", DateTime(timezone=True)),
        Column("status", String(32), nullable=False),
        Column("items_seen", Integer, nullable=False, default=0),
        Column("items_new", Integer, nullable=False, default=0),
        Column("items_dup", Integer, nullable=False, default=0),
        Column("error", Text),
    )
    metadata.create_all(engine)
    return runs


def test_start_reconciles_only_orphaned_runs_from_same_source():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    runs = _runs_table(engine)

    old_worker_id = RunRecorder(engine=engine, source="worker").start()
    source_id = RunRecorder(engine=engine, source="source-a").start()
    new_worker_id = RunRecorder(engine=engine, source="worker").start()

    assert old_worker_id is not None
    assert source_id is not None
    assert new_worker_id is not None

    with engine.connect() as connection:
        rows = {
            row.id: row
            for row in connection.execute(select(runs).order_by(runs.c.id)).mappings()
        }

    assert rows[old_worker_id]["status"] == "error"
    assert rows[old_worker_id]["finished_at"] is not None
    assert "stopped uncleanly" in rows[old_worker_id]["error"]
    assert rows[source_id]["status"] == "running"
    assert rows[new_worker_id]["status"] == "running"


def test_finish_keeps_replacement_run_auditable():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    runs = _runs_table(engine)
    recorder = RunRecorder(engine=engine, source="worker")
    run_id = recorder.start()

    assert run_id is not None
    recorder.finish(run_id, processed=7, status="ok")

    with engine.connect() as connection:
        row = (
            connection.execute(select(runs).where(runs.c.id == run_id)).mappings().one()
        )

    assert row["status"] == "ok"
    assert row["items_seen"] == 7
    assert row["items_new"] == 7
    assert row["finished_at"] is not None
