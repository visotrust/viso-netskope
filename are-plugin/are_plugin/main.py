from are_plugin.are import (
    PluginBase,
    ValidationResult,
    PushResult,
    TargetMappingFields,
    MappingType)


class VTPluginARE(PluginBase):
    def get_target_fields(self, plugin_id, plugin_params):
        return [
            TargetMappingFields(
                label="Company Name",
                type=MappingType.STRING,
                value="name",
            )
        ]
