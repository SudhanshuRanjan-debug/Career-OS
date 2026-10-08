import re
import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db.base import Base
import app.models  # noqa: F401

def main():
    print(f"Base.metadata table count: {len(Base.metadata.tables)}")
    model_tables = set(Base.metadata.tables.keys())

    migration_file = backend_dir / "alembic" / "versions" / "001_initial_schema.py"
    with open(migration_file, "r", encoding="utf-8") as f:
        content = f.read()

    migration_tables = set(re.findall(r"op\.create_table\(\s*['\"](\w+)['\"]", content))
    print(f"Migration table count: {len(migration_tables)}")

    diff_in_models = model_tables - migration_tables
    diff_in_migration = migration_tables - model_tables

    print(f"In models but not migration: {diff_in_models}")
    print(f"In migration but not models: {diff_in_migration}")

if __name__ == "__main__":
    main()
