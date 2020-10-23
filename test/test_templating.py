# pylint: disable = missing-function-docstring

import json

from hamcrest import *  # pylint: disable = unused-wildcard-import
from striv import templating


def _compact_json(payload):
    return json.dumps(json.loads(payload))


def test_materialize_layer_makes_named_snippet():
    layer = templating.materialize_layer('ze-layer', {'prip': 'prop'})
    assert layer == ('ze-layer', '{prip: "prop"}')


def test_materialize_layer_nests_on_dot():
    layer = templating.materialize_layer('ze-layer', {
        'prap.prep.prup': 'prop',
        'prap.pryp': 'prip',
    })
    assert layer == (
        'ze-layer',
        '{prap: {prep: {prup: "prop"}, pryp: "prip"}}'
    )


def test_merge_layers_uses_jsonnet_inheritance():
    snippet1 = '{prip: "prop"}'
    snippet2 = '{prup: self.prip + "prap"}'
    merged = templating.merge_layers(
        ('layer1', snippet1),
        ('layer2', snippet2)
    )
    assert merged == '%s + %s' % (snippet1, snippet2)


def test_merge_layers_complains_on_invalid_first_layer():
    snippet1 = '{prip: "prop}'
    snippet2 = '{prup: self.prip + "prap"}'
    assert_that(
        calling(templating.merge_layers)
        .with_args(('layer1', snippet1), ('layer2', snippet2)),
        raises(templating.ValidationError,
               pattern='layer1.*unterminated string')
    )


def test_merge_layers_complains_on_invalid_second_layer():
    snippet1 = '{prip: "prop"}'
    snippet2 = '{prup: self.prip + "prap}'
    assert_that(
        calling(templating.merge_layers)
        .with_args(('layer1', snippet1), ('layer2', snippet2)),
        raises(templating.ValidationError,
               pattern='layer2.*unterminated string')
    )


def test_evaluate():
    template = '{prip: params.prip + 1}'
    param_snippet = '{prip: 1}'
    payload = templating.evaluate(template, param_snippet)
    assert _compact_json(payload) == '{"prip": 2}'


def test_evaluate_compains_on_invalid_snippet():
    template = '{prip: "}'
    assert_that(
        calling(templating.evaluate)
        .with_args(template, '{}'),
        raises(templating.ValidationError,
               matching=has_properties(
                   source=matches_regexp('prip'),
                   message=matches_regexp('unterminated string')))
    )
