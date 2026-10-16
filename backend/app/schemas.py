"""Shapes of the JSON the API sends and receives (Pydantic models).

FastAPI checks every request and response against these, and shows them on
the /docs page. Hot file: tell the team before you edit it.
"""

from pydantic import BaseModel


class HealthOut(BaseModel):
    """Answer of GET /health."""

    status: str
