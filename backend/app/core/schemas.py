"""Shared Pydantic base model.

API responses use camelCase (matching the frontend), while Python stays
snake_case.
"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
