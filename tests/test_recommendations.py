import pytest
import io
from unittest.mock import patch, MagicMock
from api.openAI_api import generate_summary,download_file,extract_text
from database.models import Notes,User, DocumentAnalysis, create_Doc_Analysis
from types import SimpleNamespace
from api.recommendations.books_api import analyze_document, DocumentAnalysisResponse, save_document_analysis, analyze_and_save_analysis, get_group_doc_analyses, get_user_doc_analyses, build_study_profile
from api.recommendations.rec_queries import gen_books, search_books, retrieve_books, rank_books, generate_recommendations

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
    def test_analyze_and_save_analysis(self):
        #reccomendation engine
        note = MagicMock()
        analysis = { "success": True,
        "result": {
                "subject": "Calc2",
                "topics": ["Series", "Sequences"],
                "keywords": ["ratio test", "divergence"],
                "academic_level" :"undergraduate",
                "summary" :"Notes the ratio test and divergence test"
        }}

        expected_result = {"success": True, "analysis_id": 21}

        with patch("api.recommendations.books_api.analyze_document") as mock_analyze, \
        patch("api.recommendations.books_api.save_document_analysis") as mock_save:
            
            mock_analyze.return_value = analysis
            mock_save.return_value = expected_result

            actual_result = analyze_and_save_analysis(note)

            assert actual_result == {"success": True, "analysis_id": 21}
            mock_analyze.assert_called_once_with(note)
            mock_save.assert_called_once_with(note,analysis)
    

    def test_get_user_doc_analyses(self):
        user_id = 1
        expected_analyses = [MagicMock(), MagicMock()]

        with patch("api.recommendations.books_api.db") as mock_db:
            mock_query = mock_db.session.query.return_value
            mock_join = mock_query.join.return_value
            mock_filter = mock_join.filter.return_value
            mock_order = mock_filter.order_by.return_value
            mock_limit = mock_order.limit.return_value

            mock_limit.all.return_value = expected_analyses

            result = get_user_doc_analyses(user_id)

            assert result == {"success": True, "analyses": expected_analyses}
            mock_db.session.query.assert_called_once_with(DocumentAnalysis)
            mock_limit.all.assert_called_once()

    def test_get_group_doc_analyses(self):
        group_id = 1
        expected_analyses = [MagicMock(), MagicMock(), MagicMock()]

        with patch("api.recommendations.books_api.db") as mock_db:
            mock_query = mock_db.session.query.return_value
            mock_join = mock_query.join.return_value
            mock_filter = mock_join.filter.return_value
            mock_order = mock_filter.order_by.return_value
            mock_limit = mock_order.limit.return_value

            mock_limit.all.return_value = expected_analyses

            result = get_group_doc_analyses(group_id)

            assert result == {"success": True, "analyses": expected_analyses}
            mock_db.session.query.assert_called_once_with(DocumentAnalysis)
            mock_limit.all.assert_called_once()
    
    def test_build_study_profile(self):
        analysis1 = MagicMock()
        analysis1.subject = "Calculus"
        analysis1.topics = ["Limits","Derivatives"]
        analysis1.keywords = ["limit","chain rule"]
        analysis1.academic_level = "undergraduate"

        analysis2 = MagicMock()
        analysis2.subject = "Calculus"
        analysis2.topics = ["Integrals","Derivatives"]
        analysis2.keywords = ["integration","chain rule"]
        analysis2.academic_level = "undergraduate"

        analysis3 = MagicMock()
        analysis3.subject = "Linear Algebra"
        analysis3.topics = ["Matrices"]
        analysis3.keywords = ["Matrix"]
        analysis3.academic_level = "undergraduate"

        analyses_result = {"success": True, "analyses": [analysis1,analysis2,analysis3]}
        actual_result = build_study_profile(analyses_result)
        expected_result = {"success": True, "profile":{
            "subjects": ["calculus", "linear algebra"],
            "topics": ["derivatives", "limits", "integrals", "matrices"],
            "keywords":["chain rule","limit", "integration", "matrix"],
            "academic_level": "undergraduate",
            "document_count": 3
        }}

        assert actual_result == expected_result

        
class TestBooksGeneration():
    def test_gen_books(self):
        study_profile = {"success": True, "profile":{
            "subjects": ["calculus", "linear algebra"],
            "topics": ["derivatives", "limits", "integrals", "matrices"],
            "keywords":["chain rule","limit", "integration", "matrix"],
            "academic_level": "undergraduate",
            "document_count": 5
        }}
        
        parsed_response = MagicMock()
        parsed_response.queries = [
            "undergraduate calculus textbook",
            "calculus derivatives textbook"
        ]

        with patch("api.recommendations.rec_queries.open_client") as mock_client:
            mock_response = MagicMock()
            mock_response.choices[0].message.parsed = parsed_response
            mock_response.choices[0].message.refusal = None
            mock_client.chat.completions.parse.return_value = mock_response

            actual_result = gen_books(study_profile)
            expected_result = {"success": True,"result": ["undergraduate calculus textbook","calculus derivatives textbook"]}
            print(actual_result)
            print(expected_result)
            assert actual_result == expected_result
            mock_client.chat.completions.parse.assert_called_once()




