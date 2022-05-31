import unittest
import planet.auth.util as auth_util


class ContentTypeParserTest(unittest.TestCase):

    def test_simple(self):
        result = auth_util.parse_content_type('application/json')
        self.assertEqual({'content-type': 'application/json'}, result)

        result = auth_util.parse_content_type('\tapplication/json ')
        self.assertEqual({'content-type': 'application/json'}, result)

    def test_none(self):
        result = auth_util.parse_content_type(None)
        self.assertEqual({'content-type': None}, result)

    def test_blank(self):
        result = auth_util.parse_content_type('')
        self.assertEqual({'content-type': None}, result)

        result = auth_util.parse_content_type('   ')
        self.assertEqual({'content-type': None}, result)

    def test_extra_fields_1(self):
        result = auth_util.parse_content_type(
            'application/json; charset=utf-8')
        self.assertEqual(
            {
                'content-type': 'application/json', 'charset': 'utf-8'
            }, result)

        result = auth_util.parse_content_type(
            '\tapplication/json  ;;; charset = utf-8\t')
        self.assertEqual(
            {
                'content-type': 'application/json', 'charset': 'utf-8'
            }, result)

    def test_extra_fields_2(self):
        result = auth_util.parse_content_type('application/json; extra1')
        self.assertEqual({
            'content-type': 'application/json', 'extra1': None
        },
                         result)

        result = auth_util.parse_content_type(
            '\tapplication/json  ;;; extra1\t')
        self.assertEqual({
            'content-type': 'application/json', 'extra1': None
        },
                         result)
