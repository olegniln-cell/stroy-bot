# scripts/check_models_vs_db.py

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect
from config import DATABASE_URL
from models import Base

IGNORED_TABLES = {"alembic_version"}


def main():
    engine = create_engine(DATABASE_URL.replace("+asyncpg", ""))
    inspector = inspect(engine)

    # Получаем и фильтруем таблицы БД
    db_tables = set(inspector.get_table_names()) - IGNORED_TABLES
    model_tables = set(Base.metadata.tables.keys())

    print("📊 Таблицы в БД:", db_tables)
    print("📦 Таблицы в моделях:", model_tables)

    missing_in_db = model_tables - db_tables
    missing_in_models = db_tables - model_tables

    if missing_in_db:
        print("⚠️ Нет в БД:", missing_in_db)
    if missing_in_models:
        print("⚠️ Нет в моделях:", missing_in_models)

    if not missing_in_db and not missing_in_models:
        print("✅ Все таблицы согласованы!")


if __name__ == "__main__":
    main()
