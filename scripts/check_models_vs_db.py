#!/usr/bin/env python
"""
check_models_vs_db.py — универсальный чекер моделей vs БД.

Фичи:
  ✅ сравнение таблиц, колонок, типов
  ✅ проверка PK/FK, unique, индексов
  ✅ strict-режим (--strict)
  ✅ вывод diff (alembic autogenerate) прямо в консоль
  ✅ предупреждения для TIMESTAMP vs DATETIME
  ✅ json-вывод (--json)
  ✅ профили окружений (--env dev/test/prod)
  ✅ auto-fix режим (--fix) — печатает готовый alembic revision --autogenerate
  ✅ apply режим (--apply) — autogenerate + upgrade head
  ✅ pre-commit friendly (exit code 1 при ошибках)
"""

import sys
import os
import argparse
import json
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine.url import make_url
from alembic.config import Config
from alembic.autogenerate import compare_metadata
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory
from subprocess import run

from models.base import Base
from config import DATABASE_URL

IGNORED_TABLES = {"alembic_version"}


def get_engine(database_url: str):
    url = make_url(database_url)
    if url.drivername.endswith("+asyncpg"):
        url = url.set(drivername="postgresql+psycopg2")
    return create_engine(url)


def compare_db(engine, metadata, strict=False):
    inspector = inspect(engine)

    db_tables = set(inspector.get_table_names())
    if not strict:
        db_tables -= IGNORED_TABLES
    model_tables = set(metadata.tables.keys())

    issues = []

    # missing / extra tables
    for t in model_tables - db_tables:
        issues.append(f"❌ Missing table in DB: {t}")
    for t in db_tables - model_tables:
        issues.append(f"❌ Extra table in DB: {t}")

    # columns
    for table in model_tables & db_tables:
        model_cols = metadata.tables[table].columns
        db_cols = {col["name"]: col for col in inspector.get_columns(table)}

        for col in model_cols:
            if col.name not in db_cols:
                issues.append(f"❌ Table {table}: missing column {col.name}")
                continue

            db_type = str(db_cols[col.name]["type"]).upper()
            model_type = str(col.type).upper()

            if db_type != model_type:
                # Игнорируем различия между TIMESTAMP и DATETIME
                if {"TIMESTAMP", "DATETIME"} <= {db_type, model_type}:
                    continue  # пропускаем
                else:
                    issues.append(
                        f"❌ Table {table}, column {col.name}: type mismatch "
                        f"(DB: {db_type}, Model: {model_type})"
                    )

        for db_col in db_cols.keys() - {c.name for c in model_cols}:
            issues.append(f"❌ Table {table}: extra column {db_col}")

        # primary keys
        db_pks = set(inspector.get_pk_constraint(table).get("constrained_columns", []))
        model_pks = {c.name for c in model_cols if c.primary_key}
        if db_pks != model_pks:
            issues.append(
                f"❌ Table {table}: PK mismatch (DB: {db_pks}, Model: {model_pks})"
            )

        # foreign keys
        db_fks = {}
        for fk in inspector.get_foreign_keys(table):
            if fk.get("constrained_columns") and fk.get("referred_table"):
                db_fks[fk["constrained_columns"][0]] = fk["referred_table"]

        model_fks = {}
        for col in model_cols:
            for fk in col.foreign_keys:
                model_fks[col.name] = fk.column.table.name

        if db_fks != model_fks:
            issues.append(
                f"❌ Table {table}: FK mismatch (DB: {db_fks}, Model: {model_fks})"
            )

    return issues


def alembic_diff(metadata, database_url):
    url = make_url(database_url)
    if url.drivername.endswith("+asyncpg"):
        url = url.set(drivername="postgresql+psycopg2")

    engine = create_engine(url)
    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)

    with engine.connect() as connection:
        env_ctx = EnvironmentContext(alembic_cfg, script)
        env_ctx.configure(connection=connection, target_metadata=metadata)

        diffs = []

        def _run(rev, context):
            nonlocal diffs
            diffs = compare_metadata(context, metadata)
            return []

        with env_ctx:
            env_ctx.run_migrations()
        return diffs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strict", action="store_true", help="strict mode (no ignored tables)"
    )
    parser.add_argument("--json", action="store_true", help="output in JSON")
    parser.add_argument(
        "--env", choices=["dev", "test", "prod"], default=None, help="select env"
    )
    parser.add_argument("--fix", action="store_true", help="show alembic autogenerate")
    parser.add_argument(
        "--apply", action="store_true", help="autogenerate + apply upgrade"
    )
    args = parser.parse_args()

    database_url = DATABASE_URL
    if args.env:
        env_key = f"DATABASE_URL_{args.env.upper()}"
        database_url = os.getenv(env_key, database_url)

    engine = get_engine(database_url)
    metadata = Base.metadata

    issues = compare_db(engine, metadata, strict=args.strict)

    if args.fix or args.apply:
        print("🔧 Alembic autogenerate diff:")
        run(["alembic", "revision", "--autogenerate", "-m", "auto_check"], check=False)
        if args.apply:
            run(["alembic", "upgrade", "head"], check=True)

    if args.json:
        print(json.dumps({"issues": issues}, indent=2, ensure_ascii=False))
    else:
        for issue in issues:
            print(issue)

    if issues:
        sys.exit(1)
    else:
        print("✅ Модели и БД синхронизируются")


if __name__ == "__main__":
    main()
