import pytest
import io
from unittest.mock import patch, MagicMock
from api.openAI_api import generate_summary,download_file,extract_text
from database.models import Notes,User
from types import SimpleNamespace


class TestSummarizeText:
    def test_returns_nonempty_string(self):
        # call generate_summary with a sample note and assert a non-empty string is returned
        note = MagicMock()
        note.file_path = "lectures/states.pdf"
        with patch('api.openAI_api.client') as mock_client, \
             patch('api.openAI_api.download_file', return_value=(b'bytes', 'pdf')), \
             patch('api.openAI_api.extract_text', return_value='Solids have a definite shape and a definite volume.'):
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Summary of states of matter."))]
            mock_client.chat.completions.create.return_value = mock_response

            result = generate_summary(note)
            print("\n--- Test 1 Result Output ---")
            print(result)

            assert result["success"] is True
            assert len(result["summary"]) > 0

    def test_empty_input_raises_or_returns_empty(self):
        # call generate_summary with None and assert it raises ValueError or returns error
        result = generate_summary(None)
        print("\n--- Test 2 Result Output ---")
        print(result)

        assert result.get("status") is False or result.get("success") is False
        assert "error" in result

    def test_calls_openai_api(self):
        # patch the OpenAI client and assert generate_summary calls it exactly once
        note = MagicMock()
        note.file_path = "lectures/liquids.pdf"
        with patch('api.openAI_api.client') as mock_client, \
             patch('api.openAI_api.download_file', return_value=(b'bytes', 'pdf')), \
             patch('api.openAI_api.extract_text', return_value='Liquids take the shape of their container but have fixed volume.'):
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Liquid summary."))]
            mock_client.chat.completions.create.return_value = mock_response

            result = generate_summary(note)
            print("\n--- Test 3 Result Output ---")
            print(result)

            mock_client.chat.completions.create.assert_called_once()

    def test_api_error_raises_runtime_error(self):
        # patch the OpenAI client to throw an exception and assert generate_summary handles it
        note = MagicMock()
        note.file_path = "lectures/gases.pdf"
        with patch('api.openAI_api.client') as mock_client, \
             patch('api.openAI_api.download_file', return_value=(b'bytes', 'pdf')), \
             patch('api.openAI_api.extract_text', return_value='Gases expand completely to fill any container size.'):
            mock_client.chat.completions.create.side_effect = Exception("API Error")

            result = generate_summary(note)
            print("\n--- Test 4 Result Output ---")
            print(result)

            assert result["success"] is False
            assert "API Error" in result["error"]



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
        with patch('api.openAI_api.client') as mock_client,\
            patch('api.openAI_api.extract_text') as mock_extract,\
            patch('api.openAI_api.download_file') as mock_download:

            mock_download.return_value = (b"%PDF-1.4 FINAL TEST FAKE FAKE FAKE","pdf")
            mock_extract.return_value = "DUMMY TEXT EXTARCTED TEXT"

            mock_response = MagicMock()
            mock_response.choices[0].message.content = "SUMMARY GENERATED HOORAY"
            mock_client.chat.completions.create.return_value = mock_response

            note = MagicMock()
            note.file_path = "homework/data_structures.pdf"
            result = generate_summary(note)
            
            print("\n---Generate summary test 3--")
            print(result.get("error"))
            assert result['success'] == True
            assert result['summary'] == "SUMMARY GENERATED HOORAY"
            mock_client.chat.completions.create.assert_called_once_with(
                model="gpt-4o-mini",
            temperature = 0.2,
            messages = [
                {"role": "system",
                "content": "Summarize the following docuemnt, with no hallucianations and only user information in the actual document"
                },
                
                {"role": "user", "content": "DUMMY TEXT EXTARCTED TEXT"}
            ]
        )
            

            
        







    
        


