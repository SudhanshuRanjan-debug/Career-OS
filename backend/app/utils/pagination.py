"""
Pagination helper functions for SQLAlchemy queries.
"""

from math import ceil
from typing import Any, Sequence
from app.schemas.common import PaginatedResponse


def paginate_sequence(
    items: Sequence[Any],
    total: int,
    page: int,
    page_size: int,
) -> PaginatedResponse:
    """Construct a PaginatedResponse envelope."""
    total_pages = ceil(total / page_size) if page_size > 0 else 0
    return PaginatedResponse(
        items=list(items),
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
