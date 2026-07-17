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
from .structure import BookRankingResponse,BookSearchQueriesResponse, RankedBook
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
                "Generate textbook search queries for the follwoing  "
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
    
     


