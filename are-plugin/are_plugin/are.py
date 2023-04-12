import sys

if sys.modules.get('netskope'):
    from netskope.integrations.grc.plugin_base import (
        PluginBase,
        ValidationResult,
        PushResult)
    from netskope.integrations.grc.models.configuration import (
        TargetMappingFields,
        MappingType)
else:
    from are_plugin.netskope_mock.are import (
        PluginBase,
        ValidationResult,
        PushResult,
        TargetMappingFields,
        MappingType)

__all__ = 'PluginBase ValidationResult PushResult TargetMappingFields MappingType'.split()
