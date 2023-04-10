from are import (
    PluginBase,
    ValidationResult,
    PushResult,
    TargetMappingFields,
    MappingType)


class LoggingPluginARE(PluginBase):
    """
    Netskope evaluates all plugins and partitions them by type according to
    their base class.  That's how the UI filters them by component.
    """
    def push(self, apps, mapping):
        """
        C{apps} is a generator containing items like:

          Application(applicationId=1063,
                      applicationName='Hanzo',
                      vendor='Hanzo Archives Ltd',
                      cci=29,
                      ccl=<CloudCofidenceLevel.POOR: 'poor'>,
                      categoryName='Business Process Management',
                      deepLink='https://alliances.eu.goskope.com/ns#/app_index_detail/index/1063',
                      users=['leeroy.jenkins@storosta.com'],
                      customTags=['Unsanctioned', 'Departmental'],
                      discoveryDomains=['hanzoarchives.com', 'hanzo.co'],
                      steeringDomains=['hanzoarchives.com'],
                      createdTime=datetime.datetime(2023, 4, 7, 9, 24, 25, 446000),
                      updatedTime=datetime.datetime(2023, 4, 7, 9, 45, 13, 144000),
                      firstSeen=datetime.datetime(2023, 4, 7, 9, 24, 25, 446000),
                      lastSeen=datetime.datetime(2023, 4, 7, 9, 24, 25, 446000))

        The less said about C{mapping}, the better.  It's some crazy Mongo thing.
        """
        self.logger.info(f"{self.__class__.__name__}.push() invoked: {list(apps)}, {mapping}")
        return PushResult(success=True, message="Push sucessful.")

    def get_target_fields(self, plugin_id, plugin_params):
        """
        You have to return something here, which means someone has to deal with
        this in the UI, even though it does nothing in this case.
        """
        return [
            TargetMappingFields(
                label="Company Name",
                type=MappingType.STRING,
                value="name",
            )
        ]

    def validate(self, configuration):
        """
        We can block here if we want, e.g. remotely validating the API key.
        """
        self.logger.info(f"{self.__class__.__name__}.validate() invoked: {configuration}")
        return ValidationResult(success=True, message="Validation successful.")
