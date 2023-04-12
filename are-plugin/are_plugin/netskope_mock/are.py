from typing import Optional, Mapping, Any, Iterable
from pydantic import BaseModel

from enum import Enum
import logging

from netskope_model import Application

class _Result(BaseModel):
    success: bool
    message: str


class ValidationResult(_Result):
    pass


class PushResult(_Result):
    pass


class MappingType(str, Enum):
    STRING  = 'string'
    # there are also INTEGERs, but nobody uses them.


class TargetMappingFields(BaseModel):
    label: str
    type:  MappingType
    value: str


class PluginBase:
    ssl_validation = True
    proxies = ()

    def __init___(self, logger=logging, config=None):
        self.logger = logger
        self.configuration = config or {}

    def push(self, apps: Iterable[Application], mapping) -> Optional[PushResult]:
        return None

    def get_target_fields(self, plugin_id, plugin_params) -> Iterable[TargetMappingFields]:
        return []

    def validate(self, config: Mapping[str, Any]) -> Optional[ValidationResult]:
        return None
