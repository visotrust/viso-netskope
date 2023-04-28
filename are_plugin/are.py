import sys

if sys.modules.get('netskope'):
    from netskope.integrations.grc.models.configuration import (
        MappingType,
        TargetMappingFields,
    )
    from netskope.integrations.grc.plugin_base import (
        PluginBase,
        PushResult,
        ValidationResult,
    )
else:
    from .netskope_mock.are import (
        MappingType,
        PluginBase,
        PushResult,
        TargetMappingFields,
        ValidationResult,
    )

    def add_user_agent(d):
        return d


__all__ = (
    'PluginBase ValidationResult PushResult TargetMappingFields MappingType'.split()
)
