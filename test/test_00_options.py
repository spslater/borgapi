"""Test the Options module"""
import unittest

from borgapi import CommonOptions, ExclusionOptions
from borgapi.options import OptionsBase


class OptionsTests(unittest.TestCase):
    """Tests for the Options Dataclasses"""

    def test_convert(self):
        """Converting the name adds the dashes to the front and replaces underscores with dashes"""
        name = "test_name"
        converted = OptionsBase.convert_name(name)
        self.assertEqual(
            converted,
            "--test-name",
            "Name conversion does not produce expected ouput",
        )

    # pylint: disable=no-member,protected-access
    def test_defaults(self):
        """Defaults returns all the dataclass fields"""
        common = CommonOptions._defaults()
        exclusion = ExclusionOptions._defaults()
        self.assertEqual(
            len(common),
            len(CommonOptions.__dataclass_fields__.keys()),
            "Number of Common Options does not match expected number",
        )
        self.assertEqual(
            len(exclusion),
            len(ExclusionOptions.__dataclass_fields__.keys()),
            "Number of Exclusion Options does not match expected number",
        )

    def test_parse(self):
        """Parsing produces formatted args list from class instance"""
        expected_args = ["--warning", "--progress", "--log-json"]
        common_args = CommonOptions(warning=True, progress=True, log_json=True).parse()
        self.assertListEqual(
            common_args,
            expected_args,
            "Parsing boolean flags does not produce expected list output",
        )

        expected_args = [
            "--exclude",
            "foo",
            "--exclude",
            "bar",
            "--pattern",
            "baz",
            "--patterns-from",
            "spam/milk",
        ]
        exclusion_args = ExclusionOptions(
            exclude=["foo", "bar"],
            pattern="baz",
            patterns_from="spam/milk",
        ).parse()
        self.assertListEqual(
            exclusion_args,
            expected_args,
            "Parsing string flags does not produce expected output",
        )


if __name__ == "__main__":
    unittest.main()
