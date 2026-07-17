import pytest
import io
from unittest.mock import patch, MagicMock
from api.openAI_api import generate_summary,download_file,extract_text
from database.models import Notes,User, DocumentAnalysis, create_Doc_Analysis
from types import SimpleNamespace
from api.recommendations.books_api import analyze_document, DocumentAnalysisResponse, save_document_analysis, analyze_and_save_analysis

#Test for recommendation workflow: Unit test + Integration Test
#Note to self: When using mocks mock the function where it is called not defined.
class TestRecommendations:
    #simple test with valid inputs of a Note object
    def test_analyze_document(self):
        note = MagicMock()
        note.file_path = "users/calc_notes.pdf"

        parsed_analysis = DocumentAnalysisResponse(
            subject = "Calc1",
            topics = ["Derivatives", "Limits"],
            keywords=["derivative", "approaching 0"],
            academic_level="undergraduate",
            summary="Notes covering derivatives and limits"
        )

        with patch("api.recommendations.books_api.open_client") as mock_client, \
            patch("api.recommendations.books_api.download_file") as mock_download, \
            patch("api.recommendations.books_api.extract_text") as mock_extract:

            mock_download.return_value = (b"%PDF-1.4 FINAL TEST FAKE FAKE FAKE","pdf")
            mock_extract.return_value = "Calc1, the limit definition of the derivative"
            mock_response = MagicMock()
            mock_response.choices[0].message.parsed = parsed_analysis
            mock_response.choices[0].message.refusal = None
            
            mock_client.chat.completions.parse.return_value = mock_response
            result = analyze_document(note)

            print(result)
            assert result['success'] is True
            assert result['result'] == {
                "subject": "Calc1",
                "topics": ["Derivatives", "Limits"],
                "keywords": ["derivative", "approaching 0"],
                "academic_level" :"undergraduate",
                "summary" :"Notes covering derivatives and limits"
            }

            mock_download.assert_called_once_with(note)
            mock_extract.assert_called_once_with(b"%PDF-1.4 FINAL TEST FAKE FAKE FAKE","pdf")
            mock_client.chat.completions.parse.assert_called_once()


    def test_analyze_document_whitespace(self):
    #Tests calling with blank documents: should not be able to parse
        note = MagicMock()
        note.file_path = "templates/calc.png"

        with patch("api.recommendations.books_api.open_client") as mock_client, \
        patch("api.recommendations.books_api.download_file") as mock_download, \
        patch("api.recommendations.books_api.extract_text") as mock_extract:

            mock_download.return_value = (b"%PDF-1.4 FINAL TEST FAKE FAKE FAKE","png")
            mock_extract.return_value = "            "
        
            result = analyze_document(note)

            #inputting with empty whitespace should output No document found
            print(result)
            assert result == {
                "success": False,
                "error": "No document found to analyze."
            }
            mock_client.chat.completions.parse.assert_not_called()

    
    
    def test_analyze_document_no_parsed_metadata(self):
    #parsed metadata isnt returned, since document could not be read correctly
        note = MagicMock()
        note.file_path = "templates/calc.png"

        with patch("api.recommendations.books_api.open_client") as mock_client, \
        patch("api.recommendations.books_api.download_file") as mock_download, \
        patch("api.recommendations.books_api.extract_text") as mock_extract:

            mock_download.return_value = (b"%PDF-1.4 FINAL TEST FAKE FAKE FAKE","jpg")
            mock_extract.return_value = "Depth First search and topological Sort for DSA class"
        
            mock_response = MagicMock()
            mock_response.choices[0].message.parsed = None
            mock_response.choices[0].message.refusal = None
            mock_client.chat.completions.parse.return_value = mock_response

            #inputting with empty whitespace should output No document found
            result = analyze_document(note)
            assert result == {
                "success": False,
                "error": "Document could not be analyzed"
            }
            mock_client.chat.completions.parse.assert_called_once()
    
    def test_save_analysis_valid(self):
        note = MagicMock()
        note.notes_id = 4

        analysis = { "success": True,
        "result": {
                "subject": "Calc2",
                "topics": ["Series", "Sequences"],
                "keywords": ["ratio test", "divergence"],
                "academic_level" :"undergraduate",
                "summary" :"Notes the ratio test and divergence test"
        }}

        with patch("api.recommendations.books_api.DocumentAnalysis") as mock_analysis, \
        patch("api.recommendations.books_api.create_Doc_Analysis") as mock_create, \
        patch("api.recommendations.books_api.db") as mock_db:

            mock_analysis.query.filter_by.return_value.first.return_value = None
            created_analysis = MagicMock()
            created_analysis.analysis_id = 67

            mock_create.return_value = created_analysis
            result = save_document_analysis(note,analysis)

            assert result == {"success": True, "analysis_id": 67}

            mock_create.assert_called_once_with(note.notes_id,analysis['result'])
            mock_db.session.add.assert_called_once_with(created_analysis)
            mock_db.session.commit.assert_called_once()




    #Integration test with analyze document then saving it to the database
    def test_save_analysis_invalid_input(self):
        #reccomendation engine 
        
        
