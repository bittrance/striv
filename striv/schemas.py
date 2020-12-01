from marshmallow import Schema, fields, validate

dimension_name_validation = validate.Regexp('^[a-z_][a-z0-9_]*$')

ParamsDefinition = fields.Dict(
    keys=fields.String(validate=validate.Regexp('^[A-Za-z_][A-Za-z0-9_.]*$'))
)


class DimensionValueDefinition(Schema):  # pylint: disable = missing-class-docstring
    params = ParamsDefinition


class Dimension(Schema):
    '''
    One dimension including all its possible value definitions.
    '''
    priority = fields.Number(required=True)
    values = fields.Dict(
        keys=fields.String(validate=dimension_name_validation),
        values=fields.Nested(DimensionValueDefinition)
    )


class Execution(Schema):
    '''
    One conceptual model for how to execute tasks or services on a
    particular backend.
    '''
    name = fields.String(required=True)
    driver = fields.String(required=True, validate=validate.OneOf(['nomad']))
    logstore = fields.String(required=True, validate=validate.OneOf(['nomad']))
    driver_config = fields.Dict()
    default_params = ParamsDefinition
    payload_template = fields.String(required=True)


class Job(Schema):
    '''
    A job defines one task or service to install in the backends.
    '''
    name = fields.String(required=True)
    execution = fields.String(required=True)
    dimensions = fields.Dict(
        keys=fields.String(validate=dimension_name_validation)
    )
    params = ParamsDefinition
    modified_at = fields.String()


class State(Schema):
    '''
    A collection of entities (dimensions and executions). Used to dump
    or load the full state.
    '''
    dimensions = fields.Dict(
        keys=fields.String(),
        values=fields.Nested(Dimension)
    )
    executions = fields.Dict(
        keys=fields.String(),
        values=fields.Nested(Execution)
    )
