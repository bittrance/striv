import io
import json
import _jsonnet


def _collate(tree, path, value):
    if len(path) == 1:
        tree[path[0]] = value
    else:
        child = tree.setdefault(path[0], {})
        _collate(child, path[1:], value)


def _write_jsonnet(buf, tree):
    buf.write('{')
    first_pass = True
    for (key, value) in tree.items():
        if first_pass:
            buf.write('%s: ' % key)
            first_pass = False
        else:
            buf.write(', %s: ' % key)

        if isinstance(value, dict):
            _write_jsonnet(buf, value)
        else:
            json.dump(value, buf)
    buf.write('}')


def _find_parser(value, value_parsers):
    if isinstance(value, dict) and value.get('_striv_type'):
        typ = value['_striv_type']
    else:
        typ = 'default'
    parser = value_parsers.get(typ)
    if not parser:
        raise ValidationError(value, 'no parser found for type %s' % typ)
    return parser


def materialize_layer(name, params, value_parsers):
    '''
    Convert a params dict to a jsonnet snippet, evaluating any value
    objects as per the provided parsers.
    '''
    tree = {}
    for (key, value) in params.items():
        parser = _find_parser(value, value_parsers)
        try:
            parsed = parser(value)
        except Exception as exc:
            raise ValidationError(value, 'value parser failed') from exc
        _collate(tree, key.split('.'), parsed)
    buf = io.StringIO()
    _write_jsonnet(buf, tree)
    return (name, buf.getvalue())


class ValidationError(Exception):
    'Error thrown when validating jsonnet templates'

    def __init__(self, source, message):
        super(ValidationError, self).__init__(message)
        self.source = source
        self.message = message


def _evaluate(name, snippet):
    try:
        return _jsonnet.evaluate_snippet(name, snippet)
    except RuntimeError as exc:
        raise ValidationError(  # pylint: disable = raise-missing-from
            snippet, *exc.args)


def _validate(layer, *layers):
    name1, snippet1 = layer
    _evaluate(name1, snippet1)
    if len(layers) > 0:
        name2, snippet2 = layers[0]
        _validate((name2, '%s + %s' % (snippet1, snippet2)), *layers[1:])


def merge_layers(*layers):
    '''
    Produce a merged and validated param snippet from a list of (name, snippet)
    tuples. Raises ValidationError pointing to the snippet which failed
    evaluation.
    '''
    _validate(*layers)
    return ' + '.join([snippet for (_, snippet) in layers])


def evaluate(template, params_snippet):
    '''
    Evaluate a template against some params. Returns a json string.
    '''
    snippet = '(function(params) %s)(%s)' % (template, params_snippet)
    return _evaluate('payload_template', snippet)
