# VT Netskope ARE Plugin

## Developing

``` sh
$ pre-commit install
```

For commit message conventions (enforce by pre-commit hooks), see [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0-beta.2/#summary)

## API Client Library

The main awkwardness around the client library was how much was going to be
generated from the OpenAPI JSON, and whether we were going to embed the OpenAPI
JSON in this repository, or include the code generated from it. I am not a fan
of committing generated code, however using a GH action to standup the webapp,
authenticate, then retrieve the OpenAPI JSON, then modify it in order to
indicate that it requires authentication would have been onerous. Having looked
at the Python generators for OpenAPI, I opted instead to use
[datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator)
to generate [pydantic](https://docs.pydantic.dev/) models ([client/model.py])
for the domain types, and to hand-write a client which accepts them.  The generated
model file is significantly smaller than the OpenAPI specification, however
will be needed to be updated whenever the webapp API changes.  It is generated like so:

```sh
$ datamodel-codegen --input openapi.json --output client/model.py
```

### Pre-processing of openapi.json

Note that we're currently making the `RelationshipCreateUpdateInput.id` field
optional via something like:

``` sh
jq 'del(.components.schemas.RelationshipCreateUpdateInput.required[] | select(. == "id"))'
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
expose the versions of these classes from below `netskope.integrations.grc` ---
otherwise, it'll provide versions from the `netskope_mock` package.

[^1]: Netskope either uses GRC as an umbrella term for some of its products,
    including ARE, or, more likely, used to refer to the ARE product as GRC.
