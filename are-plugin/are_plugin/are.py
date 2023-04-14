import sys

if sys.modules.get('netskope'):
    from netskope.integrations.grc.plugin_base import (
        PluginBase,
        ValidationResult,
        PushResult)
    from netskope.integrations.grc.models.configuration import (
        TargetMappingFields,
        MappingType)
    from netskope.common.utils import add_user_agent
else:
    from .netskope_mock.are import (
        PluginBase,
        ValidationResult,
        PushResult,
        TargetMappingFields,
        MappingType)
    def add_user_agent(d):
        return d

__all__ = 'PluginBase ValidationResult PushResult TargetMappingFields MappingType'.split()
