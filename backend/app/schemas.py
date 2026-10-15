from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ItemType = Literal["LOST", "FOUND"]
Category = Literal["ELECTRONICS", "ID_CARD", "BOOKS", "BOTTLE", "CLOTHING", "OTHER"]
Status = Literal["OPEN", "CLAIMED", "RETURNED"]


class ItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = ""
    type: ItemType
    category: Category = "OTHER"
    location: str = Field(min_length=1, max_length=120)
    reported_by: str = Field(min_length=1, max_length=80)
    contact: str = Field(default="", max_length=120)


class ItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    type: ItemType | None = None
    category: Category | None = None
    location: str | None = Field(default=None, min_length=1, max_length=120)
    reported_by: str | None = Field(default=None, min_length=1, max_length=80)
    contact: str | None = Field(default=None, max_length=120)
    status: Status | None = None


class ItemOut(ItemCreate):
    id: int
    status: Status
    created_at: datetime
    resolved_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class StatsOut(BaseModel):
    total: int
    open_lost: int
    open_found: int
    claimed: int
    returned: int
    by_category: dict[str, int]
