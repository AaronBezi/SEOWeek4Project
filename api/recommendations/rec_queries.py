import os
import io
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




