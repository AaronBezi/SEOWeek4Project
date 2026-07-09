import pytest
from unittest.mock import patch, MagicMock
from api.openAI_api import generate_summary
from database.models import Notes,User
from types import SimpleNamespace


class TestSummarizeText:
    def test_returns_nonempty_string(self):
        # call generate_summary with a sample list and assert a non-empty string is returned
        sample_notes = ["Solids have a definite shape and a definite volume."]
        with patch('api.openAI_api.OpenAI') as mock_openai:  # Updated patch path
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Summary of states of matter."))]
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            result = generate_summary(sample_notes)
            print("\n--- Test 1 Result Output ---")
            print(result)

            assert result["success"] is True
            assert len(result["summary"]) > 0

    def test_empty_input_raises_or_returns_empty(self):
        # call generate_summary with an empty string and assert it raises ValueError or returns ""
        result = generate_summary([])
        print("\n--- Test 2 Result Output ---")
        print(result)

        assert result.get("status") is False or result.get("success") is False
        assert "error" in result

    def test_calls_openai_api(self):
        # patch the OpenAI client and assert generate_summary calls it exactly once
        with patch('api.openAI_api.OpenAI') as mock_openai:  # Updated patch path
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            result = generate_summary(["Liquids take the shape of their container but have fixed volume."])
            print("\n--- Test 3 Result Output ---")
            print(result)

            mock_client.chat.completions.create.assert_called_once()

    def test_api_error_raises_runtime_error(self):
        # patch the OpenAI client to throw an exception and assert generate_summary raises RuntimeError
        with patch('api.openAI_api.OpenAI') as mock_openai:  # Updated patch path
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_openai.return_value = mock_client

            result = generate_summary(["Gases expand completely to fill any container size."])
            print("\n--- Test 4 Result Output ---")
            print(result)

            assert result["success"] is False
            assert "Could not generate summary" in result["error"]



#new summary test with new api changes with file implementation
class TestGenSummaryNew:
    def test_generate_summary(mock_supabase,mock_openai):
        with patch("storage.supabase") as mock_supabase,\
            patch("api.openAI_api.OpenAI") as mock_openai:

            mock_supabase.storage.from_.return_value.download.return_value = b"%PDF MOCK PDF BYTES"

            #fake open ai upload
            mock_uploaded_file = MagicMock()
            mock_uploaded_file.id = "file_namefake"
            mock_openai.files.create.return_value = mock_uploaded_file

            #Fake openai response
            mock_response = MagicMock()
            mock_response.output_text = "TESTING FAKE SUMMARY PLEASE WORK"
            mock_openai.responses.create.return_value = mock_response

            #generate fake note object
            fake_note = SimpleNamespace(file_path="lectures/calc.pdf")
            result = generate_summary(fake_note)

            print("\n--- Test 1 Result Output ---")
            print(result)

            assert result == "TESTING FAKE SUMMARY PLEASE WORK"



