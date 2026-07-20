import pytest
import io
from unittest.mock import patch, MagicMock
from api.openAI_api import generate_summary,download_file,extract_text
from database.models import Notes,User, DocumentAnalysis, create_Doc_Analysis
from types import SimpleNamespace
from api.recommendations.books_api import analyze_document, DocumentAnalysisResponse, get_or_create_analysis
from api.recommendations.rec_queries import gen_books, search_books, retrieve_books, rank_books, generate_recommendations


class TestRec:
    def test_analyze_document(self):
        #succesful call to analyze document assuming correct inputs
        parsed_analysis = DocumentAnalysisResponse(
            subject = "Calc1",
            topics = ["Derivatives", "Limits"],
            keywords=["derivative", "approaching 0"],
            academic_level="undergraduate",
            summary="Notes covering derivatives and limits"
        )


        with patch("api.recommendations.books_api.open_client") as mock_client:
            mock_response = MagicMock()
            mock_response.choices[0].message.parsed = parsed_analysis
            mock_client.chat.completions.parse.return_value = mock_response

            result = analyze_document("Calc1, the limit definition of the derivative")

            print(result)
            assert result['success'] is True
            assert result['result'] == {
                "subject": "Calc1",
                "topics": ["Derivatives", "Limits"],
                "keywords": ["derivative", "approaching 0"],
                "academic_level" :"undergraduate",
                "summary" :"Notes covering derivatives and limits"
            }

            mock_client.chat.completions.parse.assert_called_once()
    def test_get_or_build(self):
        note = MagicMock(notes_id=1)
        existing_analysis = MagicMock(embedding=[0.1, 0.2, 0.3])
        linked_analysis = MagicMock()

        with patch("api.recommendations.books_api.download_file", return_value=(b"bytes", "pdf")), \
             patch("api.recommendations.books_api.extract_text", return_value="some extracted text"), \
             patch("api.recommendations.books_api.content_hash", return_value="hash123"), \
             patch("api.recommendations.books_api.DocumentAnalysis") as mock_doc_analysis_model, \
             patch("api.recommendations.books_api.create_Doc_Analysis", return_value=linked_analysis) as mock_create, \
             patch("api.recommendations.books_api.analyze_document") as mock_analyze, \
             patch("api.recommendations.books_api.get_embedding") as mock_get_embedding, \
             patch("api.recommendations.books_api.db") as mock_db:

            mock_doc_analysis_model.query.filter_by.return_value.first.return_value = existing_analysis

            result = get_or_create_analysis(note)

            mock_analyze.assert_not_called()
            mock_get_embedding.assert_not_called()
            mock_create.assert_called_once_with(note.notes_id, existing_analysis, "hash123", existing_analysis.embedding)
            mock_db.session.add.assert_called_once_with(linked_analysis)
            mock_db.session.commit.assert_called_once()
            assert result == linked_analysis
        

    def test_get_or_build_new(self):
        note = MagicMock(notes_id=2)
        parsed_result = {
            "subject": "Chemistry",
            "topics": ["Organic Reactions"],
            "keywords": ["reagent"],
            "academic_level": "undergraduate",
            "summary": "Covers organic reaction mechanisms.",
        }
        new_analysis_obj = MagicMock()
        with patch("api.recommendations.books_api.download_file", return_value=(b"bytes", "pdf")), \
             patch("api.recommendations.books_api.extract_text", return_value="organic chem notes"), \
             patch("api.recommendations.books_api.content_hash", return_value="hash456"), \
             patch("api.recommendations.books_api.DocumentAnalysis") as mock_doc_analysis_model, \
             patch("api.recommendations.books_api.create_Doc_Analysis", return_value=new_analysis_obj) as mock_create, \
             patch("api.recommendations.books_api.analyze_document", return_value={"success": True, "result": parsed_result}) as mock_analyze, \
             patch("api.recommendations.books_api.build_embedding_text", return_value="embedding text") as mock_build_text, \
             patch("api.recommendations.books_api.get_embedding", return_value=[0.4, 0.5, 0.6]) as mock_get_embedding, \
             patch("api.recommendations.books_api.db") as mock_db:
            
            
            mock_doc_analysis_model.query.filter_by.return_value.first.return_value = None

            result = get_or_create_analysis(note)

            mock_analyze.assert_called_once_with("organic chem notes")
            mock_build_text.assert_called_once_with(parsed_result)
            mock_get_embedding.assert_called_once_with("embedding text")
            mock_create.assert_called_once()
            mock_db.session.add.assert_called_once_with(new_analysis_obj)
            mock_db.session.commit.assert_called_once()
            assert result == {"success": True, "analysis": new_analysis_obj}
                


