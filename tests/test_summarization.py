import pytest
import io
from unittest.mock import patch, MagicMock
from api.openAI_api import generate_summary,download_file,extract_text
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



class TestSummarizationNew:
    def test_download_return_bytes_ext(self):
        #test verifying donwload returns file bytes
        fake_bytes = b"%PDF-1.4 garbage content"
        with patch('api.openAI_api.supabase') as mock_supabase:
            mock_supabase.storage.from_.return_value.download.return_value = fake_bytes
            note = MagicMock()
            note.file_path = "lectures/calc.pdf"

            result_bytes,result_ext = download_file(note)

            print("\n--- Test 1 Result Output ---")

            assert result_bytes == fake_bytes
            assert result_ext == "pdf"
            mock_supabase.storage.from_.assert_called_once_with("notes")
            mock_supabase.storage.from_.return_value.download.assert_called_once_with("lectures/calc.pdf")

    def test_extract_text_pdf(self):
        with patch('api.openAI_api.md') as mock_md:
            mock_result = MagicMock()
            mock_result.text_content = "PDF TEXT PDF TEST TPDNDJJNDW"
            mock_md.convert_stream.return_value = mock_result

            result = extract_text(b"%PDF-1.4 WORK PLEASE WORK","pdf")
            print("\n--- Test 2 Result Output")
            assert result == "PDF TEXT PDF TEST TPDNDJJNDW"

    def test_generate_summary(self):
        with patch('api.openAI_api.OpenAI') as mock_openai,\
            patch('api.openAI_api.extract_text') as mock_extract,\
            patch('api.openAI_api.download_file') as mock_download:

            mock_download.return_value = (b"%PDF-1.4 FINAL TEST FAKE FAKE FAKE","pdf")
            mock_extract.return_value = "DUMMY TEXT EXTARCTED TEXT"

            mock_client_instance = mock_openai.return_value
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "SUMMARY GENERATED HOORAY"
            mock_client_instance.chat.completions.create.return_value = mock_response

            note = MagicMock()
            note.file_path = "homework/data_structures.pdf"
            result = generate_summary(note)
            
            print("\n---Generate summary test 3--")
            assert result['success'] == True
            assert result['summary'] == "SUMMARY GENERATED HOORAY"
            mock_client_instance.chat.completions.create.assert_called_once_with(
                
            )

            
        







    
        


