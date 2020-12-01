# pylint: disable = missing-function-docstring

import json
from striv.templating import ValidationError

import pytest
from hamcrest import *  # pylint: disable = unused-wildcard-import
from striv import templating


@pytest.fixture()
def value_parsers():
    return {
        'string': lambda v: v,
        'object': lambda v: v['value'],
    }


def _compact_json(payload):
    return json.dumps(json.loads(payload))


class TestMaterializeLayer:
    @pytest.mark.parametrize('input,snippet', [
        ({'prip': 'prop'}, '{prip: "prop"}'),
        ({'prip': True}, '{prip: true}'),
        ({'prip': 4}, '{prip: 4}'),
        ({'prip': 'pr"op'}, '{prip: "pr\\"op"}'),
        ({'prip': 'prop\\'}, '{prip: "prop\\\\"}'),
    ])
    def test_makes_named_snippet(self, input, snippet, value_parsers):
        layer = templating.materialize_layer('ze-layer', input, value_parsers)
        assert layer == ('ze-layer', snippet)

    def test_nests_on_dot(self, value_parsers):
        layer = templating.materialize_layer('ze-layer', {
            'prap.prep.prup': 'prop',
            'prap.pryp': 'prip',
        }, value_parsers)
        assert layer == (
            'ze-layer',
            '{prap: {prep: {prup: "prop"}, pryp: "prip"}}'
        )

    def test_applies_value_parsers(self, value_parsers):
        layer = templating.materialize_layer(
            'ze-layer',
            {'prip': {'type': 'object', 'value': 'object-value'}},
            value_parsers
        )
        assert layer == ('ze-layer', '{prip: "object-value"}')

    def test_applies_value_parsers_nestedly(self, value_parsers):
        layer = templating.materialize_layer(
            'ze-layer',
            {'prip.prup': {'type': 'object', 'value': 'object-value'}},
            value_parsers
        )
        assert layer == ('ze-layer', '{prip: {prup: "object-value"}}')

    def test_complains_about_missing_type(self, value_parsers):
        value = {'prip': {'value': 'object-value'}}
        assert_that(
            calling(templating.materialize_layer)
            .with_args('ze-layer', value, value_parsers),
            raises(ValidationError, pattern='missing object')
        )

    def test_complains_about_missing_type(self, value_parsers):
        value = {'prip': {'type': 'unknown', 'value': 'object-value'}}
        assert_that(
            calling(templating.materialize_layer)
            .with_args('ze-layer', value, value_parsers),
            raises(ValidationError, pattern='no parser')
        )

    def test_wraps_parser_exception(self, value_parsers):
        def boom(_):
            raise KeyError('boom')
        value_parsers['string'] = boom
        assert_that(
            calling(templating.materialize_layer)
            .with_args('ze-layer', {'prip': 'prop'}, value_parsers),
            raises(ValidationError)
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
