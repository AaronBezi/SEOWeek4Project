import os
import io
from api.openAI_api import download_file, extract_text
from dotenv import load_dotenv
from openai import OpenAI
from typing import Literal
from pydantic import BaseModel, Field  #This allows us to get correctly formatted json responses back

load_dotenv()
open_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
books_client = "abc"

class DocumentAnalysis(BaseModel):
    subject: str = Field(description="The academic subject discussed in the document")
    topics: list[str] = Field(min_length=1,max_length=10,description = "The major concepts described in the document")
    keywords: list[str] = Field(min_length=1,max_length=15,description="Important technical terms discussed in the document")
    academic_level: Literal[
        "high_school","undergraduate", "graduate", "unknown"
    ]
    summary: str=Field(description="A concise summary of the document's academic content")



#Takes a note from supabase storage extracts its contents and pass into openai api to get metadata for books api
def analyze_document(note):
    if not note:
        return {"success": False, "error": "Note is empty"}
    
    try:
        file_bytes,ext= download_file(note)
        document_text = extract_text(file_bytes,ext)
        if not document_text or not document_text.strip():  #protects aganist empty documents
            return {"success": False, "error": "No document found to analyze."}
        response = open_client.chat.completions.parse(
            model="gpt-4o-mini",
            temperature = 0.2,
            messages = [
                {
                "role": "system",
                "content": (
                    "You are an analyzer that analyzes academic documents for a textbook    "
                    "recommendation system. Extract only information supported by the provided document. "
                "Do not recommend any books and do not hallucinate any missing information"),
                },
                
                {"role": "user", "content": (
                    "Analyze the following academic document provided:\n\n"
                                                f"{document_text}"
                        )}
            ],
            response_format =DocumentAnalysis,
        )
        message = response.choices[0].message
        if message.parsed is None:
            return {"success": False, "error": "Document could not be analyzed"}
        
        return {"success": True, "result": message.parsed.model_dump()}

    except Exception as e:
        return {"success": False, "error": str(e)}
