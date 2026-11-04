"""Check canonical imports and compatibility after the file-only refactor."""
import importlib
import pkgutil
import unittest
import flowbridge_analysis as package
from flowbridge_analysis import models


class ModuleOrganizationTests(unittest.TestCase):
    def test_every_package_module_imports(self):
        for item in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
            with self.subTest(module=item.name):
                importlib.import_module(item.name)

    def test_legacy_components_share_canonical_implementations(self):
        for old, new in package._LEGACY_MODULES.items():
            with self.subTest(module=old):
                self.assertIs(importlib.import_module(f'flowbridge_analysis.{old}'),
                              importlib.import_module(f'flowbridge_analysis.{new}'))

    def test_model_exports_are_canonical_classes(self):
        for name in models.__all__:
            item = getattr(models, name)
            if isinstance(item, type):
                with self.subTest(model=name):
                    module = importlib.import_module(f'flowbridge_analysis.models.{name}')
                    self.assertIs(item, getattr(module, name))

    def test_feature_validator_compatibility(self):
        from flowbridge_analysis.FeatureValidator import FeatureValidator, FeatureValidationResult
        from flowbridge_analysis import validator
        self.assertIs(validator.FeatureValidator, FeatureValidator)
        self.assertIs(validator.FeatureValidationResult, FeatureValidationResult)
