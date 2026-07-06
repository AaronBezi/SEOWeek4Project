import pytest
from unittest.mock import patch
from summarize import summarize_text # to be determined


class TestSummarizeText:
    def test_returns_nonempty_string(self):
        # call summarize_text (tbd) with a sample paragraph and assert a non-empty string is returned
        pass

    def test_empty_input_raises_or_returns_empty(self):
        # call summarize_text (tbd) with an empty string and assert it raises ValueError or returns ""
        pass

    def test_calls_openai_api(self):
        # patch the OpenAI client and assert summarize_text (tbd) calls it exactly once
        pass

    def test_api_error_raises_runtime_error(self):
        # patch the OpenAI client to throw an exception and assert summarize_text (tbd) raises RuntimeError
        pass
