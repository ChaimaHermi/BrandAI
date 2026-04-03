from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class BrandIdentityCreate(BaseModel):
    status: str = "done"
    """Méta seule (branding_status, agent_errors, …) si colonnes séparées fournies."""
    result_json: Optional[Any] = None
    result_names: Optional[Any] = None
    result_slogans: Optional[Any] = None
    result_logo: Optional[Any] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BrandIdentityOut(BaseModel):
    id: int
    idea_id: int
    status: str
    """Vue fusionnée (rétrocompatible) : méta + noms + slogans + logo."""
    result_json: Optional[Any] = None
    result_names: Optional[Any] = None
    result_slogans: Optional[Any] = None
    result_logo: Optional[Any] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
