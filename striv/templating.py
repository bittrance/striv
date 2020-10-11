import io
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
            buf.write('"%s"' % value)
    buf.write('}')


def materialize_layer(name, params):
    'Convert a params dict to a jsonnet snippet.'
    tree = {}
    for (key, value) in params.items():
        _collate(tree, key.split('.'), value)
    buf = io.StringIO()
    _write_jsonnet(buf, tree)
    return (name, buf.getvalue())


class ValidationError(Exception):
    'Error thrown when validating jsonnet templates'


def _validate(layer, *layers):
    name1, snippet1 = layer
    try:
        _jsonnet.evaluate_snippet(name1, snippet1)
    except RuntimeError as exc:
        raise ValidationError(  # pylint: disable = raise-missing-from
            snippet1, *exc.args)
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
    return _jsonnet.evaluate_snippet('template', snippet)
