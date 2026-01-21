"""
Import log schemas.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ImportLogRead(BaseModel):
    id: UUID = Field(..., description="Import log id")
    filename: str = Field(..., description="Source file name")
    file_size: int | None = Field(None, description="File size in bytes")
    file_hash: str | None = Field(None, description="File hash")
    file_path: str | None = Field(None, description="Stored file path")
    format: str = Field(..., description="Detected or selected format")
    parser_version: str | None = Field(None, description="Parser version")
    status: str = Field(..., description="Import status")
    progress: int = Field(..., description="Progress percentage")
    records_total: int = Field(..., description="Total records")
    records_success: int = Field(..., description="Successful records")
    records_failed: int = Field(..., description="Failed records")
    error_message: str | None = Field(None, description="Error summary")
    error_details: dict | None = Field(None, description="Error details")
    assets_created: dict = Field(..., description="Created assets summary")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Update time")
    created_by: str | None = Field(None, description="Creator")
    duration_seconds: int | None = Field(None, description="Duration seconds")

    model_config = ConfigDict(from_attributes=True)


class ImportLogList(BaseModel):
    items: list[ImportLogRead]
    total: int
