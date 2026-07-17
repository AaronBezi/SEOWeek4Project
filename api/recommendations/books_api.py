import os
import io
from api.openAI_api import download_file, extract_text
from dotenv import load_dotenv
from openai import OpenAI
from typing import Literal
from pydantic import BaseModel, Field  #This allows us to get correctly formatted json responses back
from database.models import DocumentAnalysis,create_Doc_Analysis
from database.database import db



load_dotenv()
open_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
books_client = os.getenv("BOOKS_KEY")

#provides the structure for the output of the open ai response.
class DocumentAnalysisResponse(BaseModel):
    subject: str = Field(description="The academic subject discussed in the document")
    topics: list[str] = Field(min_length=1,max_length=10,description = "The major concepts described in the document")
    keywords: list[str] = Field(min_length=1,max_length=15,description="Important technical terms discussed in the document")
    academic_level: Literal[
        "high_school","undergraduate", "graduate", "unknown"
    ]
    summary: str=Field(description="A concise summary of the document's academic content")


#--------------------------------------------PHASE 1: PARSING DOCUMENTS FOR METADATA FOR GOOGLE BOOKS API---------------------------
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
            response_format =DocumentAnalysisResponse,
        )
        message = response.choices[0].message
        if message.parsed is None:
            return {"success": False, "error": "Document could not be analyzed"}
        
        return {"success": True, "result": message.parsed.model_dump()}

    except Exception as e:
        return {"success": False, "error": str(e)}
    


#Saves document analysis for users/groups notes to database
def save_document_analysis(note,analysis):
    if not note:
        return {"success": False, "error": "Note is empty"}

    if not isinstance(analysis,dict):
        return {"success": False, "error": "Invalid analysis result"}
    #analysis failed or is empty
    if not analysis or not analysis.get("success"):
        return {"success": False, "error": analysis.get("error","Document analysis failed")}
    
    metadata = analysis.get("result")

    if not metadata:
        return {"success": False, "error": "metadata is empty"}

    try:
        if not note.notes_id:
            return {"success": False, "result": "Notes ID is not correct"}
        analysis_exist = DocumentAnalysis.query.filter_by(note_id = note.notes_id).first()

        #anlysis for this note exist just add the existing data
        if analysis_exist:
            analysis_exist.subject = metadata['subject']
            analysis_exist.topics = metadata['topics']
            analysis_exist.keywords = metadata['keywords']
            analysis_exist.academic_level = metadata['academic_level']
            analysis_exist.summary = metadata['summary']
        else:
            analysis_exist = create_Doc_Analysis(note.notes_id,metadata)
        
            db.session.add(analysis_exist)
        db.session.commit()
        
        return {"success": True, "analysis_id": analysis_exist.analysis_id}
    
    except KeyError as error:
        db.session.rollback()
        return {"success": False, "error": f"Missing analysis field: {error.args[0]}"}
    
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}


def analyze_and_save_analysis(note):
    #Generate an analysis for a given note then save the analysis to the database
    analysis = analyze_document(note)
    #if analysi sfailed return the error message
    if not analysis.get("success"):
        return analysis
    
    return save_document_analysis(note,analysis)

            

    

