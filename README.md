# VISO TRUST Netskope ARE Plugin

## Developing

``` sh
$ pre-commit install
```

For commit message conventions (enforced by `pre-commit` hooks), see [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0-beta.2/#summary).

## API Client Library

[datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator)
is used to generate [pydantic](https://docs.pydantic.dev/) models
(see [model.py](are_plugin/client/model.py)) from the schemas in the webapp's OpenAPI
JSON.  The resulting Python module is significantly smaller than the OpenAPI
specification, however it'll need updating whenever the webapp API changes.
It's generated like so:

```sh
$ datamodel-codegen --input openapi.json --output client/model.py
```

## Testability

This package includes an `are` module, from which the plugin is expected to
import the following Netskope GRC[^1] (ARE) classes:

 - `PluginBase`
 - `ValidationResult`
 - `PushResult`
 - `TargetMappingFields`
 - `MappingType`

If the `are` module is being evaluated within a Netskope instance, it will
expose the versions of these classes from below `netskope.integrations.grc` &mdash;
otherwise, it'll provide versions from the `netskope_mock` package.

[^1]: Netskope either uses GRC as an umbrella term for some of its products,
    including ARE, or, more likely, used to refer to the ARE product as GRC.
