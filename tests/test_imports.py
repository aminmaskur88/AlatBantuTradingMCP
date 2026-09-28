import unittest
import os
import sys

class TestModuleImports(unittest.TestCase):
    def setUp(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        src_path = os.path.join(project_root, "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

    def test_import_core_modules(self):
        modules = [
            "ai_analyzer",
            "stockbit_client",
            "financial_data_processor",
            "enhanced_chart_generator",
            "chart_bridge",
            "projection_bridge",
            "idx_data_service",
            "news_scraper",
            "scraper",
            "bing_search_tool",
            "yahoo_finance_tool",
            "formatter",
            "utils"
        ]
        for mod in modules:
            with self.subTest(module=mod):
                __import__(mod)

if __name__ == "__main__":
    unittest.main()
