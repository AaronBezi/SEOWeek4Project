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


load_dotenv()
open_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
books_client = os.getenv("BOOKS_KEY")
GOOGLE_BOOKS_URL = os.getenv("BOOKS_URL")


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
             #if empty skip to the next book
             if not item.get("id") or not volume.get("title"):
                continue
                 
             books.append({
                  "book_id": item.get("id"),
                  "title": volume.get("title"),
                  "authors": volume.get("authors",[]),
                  "description": volume.get("description",""),
                  "categories": volume.get("categories", []),
                  "preview_link": volume.get("previewLink")
             })
        
        return {"success": True, "books": books}
    except requests.RequestException as e:
         return {"success": False, "error": str(e)}
    except ValueError:
         return {"success": False, "error": "Invalid JSON returned by Books api"}

    
     


