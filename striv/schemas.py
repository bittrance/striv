from marshmallow import Schema, fields, validate


class Job(Schema):
    '''
    A job defines one task or service to install in the backends.
    '''
    name = fields.String(required=True)
    execution = fields.String(required=True)
    dimensions = fields.Dict(
        keys=fields.String(
            validate=validate.Regexp('^[a-z_][a-z0-9_]*$')
        )
    )
    params = fields.Dict(
        keys=fields.String(
            validate=validate.Regexp('^[A-Za-z_][A-Za-z0-9_.]*$')
        )
    )
