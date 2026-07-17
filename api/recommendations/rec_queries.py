import os
import io
import requests
from api.openAI_api import download_file, extract_text
from dotenv import load_dotenv
from openai import OpenAI
from typing import Literal
from pydantic import BaseModel, Field  #This allows us to get correctly formatted json responses back
from database.models import DocumentAnalysis,create_Doc_Analysis, Notes
from database.database import db
from collections import Counter
from .structure import BookRankingResponse,BookSearchQueriesResponse
from .books_api import create_user_study_profile, create_group_study_profile

load_dotenv()
open_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
books_client = os.getenv("BOOKS_KEY")
GOOGLE_BOOKS_URL = os.getenv("BOOKS_URL")


def gen_books(study_profile):
    #Based on the users study profile query books from gen ai api: feed into books api to retruve candidate books
    if not study_profile: return {"success": False, "error": "Profile is empty"}
    if not study_profile.get("success"): return {"success": False, "error": "Invalid Profile"}

    profile = study_profile.get("profile")
    if not profile: return {"success": False, "error": profile.get("error","Invalid Profile")}

    try:
        response = open_client.chat.completions.parse(
        model="gpt-4o-mini",
        temperature = 0.2,
        messages = [
            {
            "role": "system",
            "content": (
                "You generate search queries for the Google Books API    "
                "Generate between 1 and 5 textbook search  "
            "queries using only the supplied study profile.  "
            "Do not invent book titles or authors, or halluciante descriptions"
            )
            },
            
            {"role": "user", "content": (
                "Generate textbook search queries for the following "
                        f"study profile: \n\n{profile}"
                    )}
        ],
        response_format = BookSearchQueriesResponse
    )
        message = response.choices[0].message
        if message.parsed is None:
            return {"success": False, "error": message.refusal or "Could not generate search queries"}
        
        return {"success": True, "result": message.parsed.queries}
    except Exception as e:
            return {"success": False, "error": str(e)}

#pass in thw queries generated from open ai api to get the books from books api
def search_books(query):
    if not query or not query.strip(): return {"success": False, "error": "Search Query is empty"}
     
    try:
        response = requests.get(GOOGLE_BOOKS_URL,params={"q":query, "maxResults":10,"printType":"books","langRestrict":"en"}, timeout = 10)
        response.raise_for_status()
        data = response.json()
        books = []
        
        for item in data.get("items",[]):
             volume = item.get("volumeInfo",{})
             books.append({
                  "book_id": item.get("id"),
                  "title": volume.get("title"),
                  "authors": volume.get("authors",[]),
                  "description": volume.get("description",""),
                  "preview_link": volume.get("previewLink")
             })
        
        return {"success": True, "books": books}
    except requests.RequestException as e:
         return {"success": False, "error": str(e)}
    except ValueError:
         return {"success": False, "error": "Invalid JSON returned by Books api"}


#search all generated queries: query_result: result that came from the gen_books function
def retrieve_books(query_result):
    if not query_result:
        return {"success": False,"error":"Empty query"}
    if not query_result.get("success"):
        return query_result

    queries = query_result.get("result")
    if not queries:
         return {"success": False,"error":"No search queries found"}
    
    candidates = {}
    for query in queries:
        result = search_books(query)
        if not result.get("success"):
            continue

        for book in result.get("books"):
             candidates[book["book_id"]] = book

    if not candidates:
        return {"success": False, "error": "No books found"}
    
    return {"success": True, "books": list(candidates.values())}


             


#Send the users/groups study profile + the candiate books to the open ai api for ranking
def rank_books(study_profile,books_retrieved):
    if not study_profile or not study_profile.get("success"):
        return {"success": False, "error": "Invalid study profile"}
    
    if not books_retrieved or not books_retrieved.get("success"):
        return {"success": False, "error": "Invalid books retrieved"}
    
    profile = study_profile.get("profile")
    books = books_retrieved.get("books")

    if not profile:
        return {"success": False, "error": "Study profile is empty"}
    
    if not books:
        return {"success": False, "error": "No books provided for ranking"}
    
    try:
        response = open_client.chat.completions.parse(
        model="gpt-4o-mini",
        temperature = 0.2,
        messages = [
            {
            "role": "system",
            "content": (
                "Rank the supplied Google Books candidates based on   "
                "The inputted academic study profile. Use only the provided books  "
                " Do not invent book IDS, or books.  "
                "Return the five most relevant book IDS with scores. "
            )
            },
            
            {"role": "user", "content": (
                        f"study profile:\n{profile}\n\n"
                        f"Book candidates:\n{books}"
                    )}
        ],
        response_format = BookRankingResponse
    )
        message = response.choices[0].message
        if message.parsed is None:
            return {"success": False, "error": message.refusal or "Could not generate Books"}
        
        #store the books generated by their book_id
        books_by_id = {
            book["book_id"]: book for book in books if book.get("book_id")
        }
        recommendations = []

        for book_id in message.parsed.recommendations:
            book = books_by_id.get(book_id)
            if book:
                recommendations.append(book)
            
        if not recommendations:
            return  {"success": False, "error": "No valid recommendations returned"}
        
    
        return {"success": True, "recommendations": recommendations}
    except Exception as e:
            return {"success": False, "error": str(e)}
        

#FULL RECOMMENDATION PIPELINE IN ONE FUNCTION TO BE USED LATER
def generate_recommendations(study_profile):
    #STEP 1: generate books based on profile with genai api
    queries = gen_books(study_profile)
    #If fail return error message
    if not queries.get("success"):
        return queries
    
    #STEP 2: Send the books openai generated to the BOOks api to find the actual books and link
    books = retrieve_books(queries)
    if not books.get("success"):
        return books
    
    #STEP 3: Pass the books found from the books api to openai api to rank them and provide the recommendations
    return rank_books(study_profile,books)
    
     


