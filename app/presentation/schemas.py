"""Cuerpos de los pedidos y las respuestas."""

from pydantic import BaseModel, Field

from app.application.entities import ConfigEntry


class EntryCreate(BaseModel):
    key: str
    value: str


class EntryUpdate(BaseModel):
    value: str
    index: int | None = Field(default=None, ge=0)


class EntryOut(BaseModel):
    key: str
    value: str
    index: int

    @classmethod
    def from_entry(cls, entry: ConfigEntry) -> "EntryOut":
        return cls(key=entry.key, value=entry.value, index=entry.index)


class EntryList(BaseModel):
    entries: list[EntryOut]
    total: int


class Health(BaseModel):
    status: str
