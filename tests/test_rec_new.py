import pytest
import io
from unittest.mock import patch, MagicMock
from api.openAI_api import generate_summary,download_file,extract_text
from database.models import Notes,User, DocumentAnalysis, create_Doc_Analysis
from types import SimpleNamespace
from api.recommendations.books_api import analyze_document, DocumentAnalysisResponse, get_or_create_analysis, get_books_query, get_or_fetch_books, recommend


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

class TestGetBooksQuery:
    def test_get_books(self):
        analysis = MagicMock(subject="Linear Algebra", keywords = ["eigenvalues", "vector spaces", "transformations", "DONT"])
        query = get_books_query(analysis)

        print(query)
        assert 'subject:"Linear Algebra"' in query
        assert '"eigenvalues"' in query
        assert '"vector spaces"' in query
        assert '"transformations"' in query
        assert '"DONT"' not in query
    
    def test_empty_analysis(self):
        result = get_books_query(None)
        print(result)
        assert result == {"success": False, "error": "DocumentAnalysis is empty"}

class TestGetOrFetchBooks:
    def test_cached_books_no_api_call(self):
        #test that a cached book is returned instead of calling the api to generate new books
        analysis = MagicMock(subject="Calculus")
        result = {"success": True, "analysis": analysis}
        cached_books = [MagicMock(), MagicMock()]

        with patch("api.recommendations.books_api.get_books_query", return_value='subject: "Algebra"'), \
            patch("api.recommendations.books_api.Book") as mock_book, \
            patch("api.recommendations.books_api.search_books") as mock_search, \
            patch("api.recommendations.books_api.get_embedding") as mock_get_embedding,\
            patch("api.recommendations.books_api.db") as mock_db:

            mock_book.query.filter.return_value.limit.return_value.all.return_value = cached_books
            output = get_or_fetch_books(result)

        mock_search.assert_not_called()
        mock_get_embedding.assert_not_called()
        mock_db.session.commit.assert_not_called()
        assert output == {"success": True, "books": cached_books}

    def test_no_cache(self):
        #test books api is called and new books generated
        analysis = MagicMock(subject="History")
        result = {"success": True, "analysis": analysis}

        data = {
            "book_id": "hello12",
            "title": "History 1010",
            "authors": ["Pink Panthres"],
            "description": "History Textbook.",
            "categories": ["History"],
            "preview_link": "https://example.com/preview"
        }
        with patch("api.recommendations.books_api.get_books_query", return_value='subject: "History"'), \
            patch("api.recommendations.books_api.Book") as mock_book, \
            patch("api.recommendations.books_api.search_books", return_value ={"success": True, "books": [data]}) as mock_search, \
            patch("api.recommendations.books_api.get_embedding", return_value = [0.1,0.4,0.32]) as mock_get_embedding,\
            patch("api.recommendations.books_api.db") as mock_db:

            mock_book.query.filter.return_value.limit.return_value.all.return_value = []
            mock_book.query.filter_by.return_value.first.return_value = None

            output = get_or_fetch_books(result)
        
        mock_search.assert_called_once_with('subject: "History"')
        mock_get_embedding.assert_called_once_with("History 1010 History Textbook. ['History']")
        mock_db.session.add.assert_called_once()
        mock_db.session.commit.assert_called_once()
        assert output["success"] is True
        assert len(output["books"]) == 1
    
    def test_failed_analysis_no_api_call(self):
        result = {"success": False, "error": "analysis failed"}

        with patch("api.recommendations.books_api.search_books") as mock_search:
            output = get_or_fetch_books(result)
        
        mock_search.assert_not_called()
        assert output["success"] is False
    
class TestRecommend:
    def test_recommend_success(self):
        #Integtration test between all recommend building blocks used on a valid input.
        note = MagicMock()
        analysis = MagicMock(embedding=[0.1, 0.2, 0.3])
        analysis_result = {"success": True, "analysis": analysis}

        # 6 candidate books so we can confirm only top 5 are returned
        books = [MagicMock(embedding=[i, i, i]) for i in range(6)]
        books_result = {"success": True, "books": books}

        # similarity scores designed so ordering is fully determined and last book is dropped
        similarity_scores = [0.5, 0.9, 0.1, 0.7, 0.3, 0.05]

        with patch("api.recommendations.books_api.get_or_create_analysis", return_value=analysis_result), \
            patch("api.recommendations.books_api.get_or_fetch_books", return_value=books_result), \
            patch("api.recommendations.books_api.cosine_similarity", side_effect=similarity_scores) as mock_cos:

            actual_result = recommend(note)

        assert actual_result["success"] is True
        assert len(actual_result["books"]) == 5
        # highest score (0.9 -> books[1]) should be first
        assert actual_result["books"][0] == books[1]
        # lowest score (0.05 -> books[5]) should be excluded entirely
        assert books[5] not in actual_result["books"]
        assert mock_cos.call_count == 6

    def test_fetch_book_fail(self):
        note = MagicMock()
        analysis = MagicMock(embeddings=[-0.34,0.23,1.2])
        analysis_result = {"success":True, "analysis": analysis}

        with patch("api.recommendations.books_api.get_or_create_analysis", return_value=analysis_result), \
            patch("api.recommendations.books_api.get_or_fetch_books", return_value={"success":False,"error":"books api down"}) as mock_books, \
            patch("api.recommendations.books_api.cosine_similarity") as mock_cos:

            actual_result = recommend(note)
        
        mock_books.assert_called_once_with(analysis_result)
        mock_cos.assert_not_called()
        assert actual_result == {"success": False, "error": "books api down"}
    
    
    def test_analysis_failiure(self):
        #test failure message is returned when analyze_document function call fails
        note = MagicMock()
        with patch("api.recommendations.books_api.get_or_create_analysis", return_value={"success": False, "error":"could not analyze"}) as mock_analysis, \
            patch("api.recommendations.books_api.get_or_fetch_books") as mock_books:

            actual_result = recommend(note)

        mock_books.assert_not_called()
        assert actual_result == {"success": False, "error": "could not analyze"}
        

        





