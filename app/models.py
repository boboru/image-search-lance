import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


# shared properties
class SearchBase(SQLModel):
    query: str
    image_uri: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    is_good: bool | None = None


# database model, database table inferred from class name
class Search(SearchBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class SearchCreate(SQLModel):
    query: str


class SearchUpdate(SQLModel):
    is_good: bool


class Image(SQLModel):
    uri: str
