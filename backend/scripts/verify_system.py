import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import app.models  # noqa: F401
from app.main import app as fastapi_app
from app.db.base import Base
from app.core.config import settings
from app.storage import get_storage_backend

def main():
    print("=== 1. FastAPI OpenAPI Verification ===")
    openapi = fastapi_app.openapi()
    print(f"Title: {openapi.get('info', {}).get('title')}")
    print(f"Version: {openapi.get('info', {}).get('version')}")
    print(f"Total paths: {len(openapi.get('paths', {}))}")
    for path in sorted(openapi.get('paths', {}).keys()):
        print(f"  - {path}")

    print("\n=== 2. SQLAlchemy Metadata Verification ===")
    print(f"Total tables: {len(Base.metadata.tables)}")

    print("\n=== 3. Settings Verification ===")
    print(f"Environment: {settings.APP_ENV}")
    print(f"Storage backend: {settings.STORAGE_BACKEND}")
    print(f"Database URL configured: {bool(settings.DATABASE_URL)}")

    print("\n=== 4. Storage Factory Verification ===")
    backend = get_storage_backend()
    print(f"Storage backend class: {backend.__class__.__name__}")

if __name__ == "__main__":
    main()
