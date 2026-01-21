"""
Relationship API routes package.

Exports relationship management router.
"""

from app.api.v1.relationships.relationship import router as relationship_router

__all__ = ["relationship_router"]
