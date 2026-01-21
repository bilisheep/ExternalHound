"""
Plugin metadata schema.
"""

from pydantic import BaseModel, Field


class PluginInfo(BaseModel):
    name: str = Field(..., description="Plugin name")
    version: str = Field(..., description="Plugin version")
    entrypoint: str = Field(..., description="Entrypoint reference")
    supported_formats: list[str] = Field(..., description="Supported formats")
    priority: int = Field(..., description="Priority")
    description: str | None = Field(None, description="Description")
    vendor: str | None = Field(None, description="Vendor")
