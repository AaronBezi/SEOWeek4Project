import os
import io
from api.openAI_api import download_file, extract_text
from dotenv import load_dotenv
from openai import OpenAI
from typing import Literal
from pydantic import BaseModel, Field  #This allows us to get correctly formatted json responses back
from database.models import DocumentAnalysis,create_Doc_Analysis, Notes
from database.database import db
from .embed import get_embedding, build_embedding_text
from collections import Counter
from api.hashing import content_hash



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
#Takes a extarcted note text from supabase storage extracts its contents and pass into openai api to get metadata for books api
#This function is ony called if an analysis for the note doesnt exist already
def analyze_document(document_text):
    
    try:
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
    


#------------------------------------PHASE 2: SAVE DOCUMENT ANALYSIS TO DATABASE-----------------------------------------
#If existing analysis already exist just return, if it doesn't exist create object and save to database. Tkaes in a note object from the user
def get_or_create_analysis(note):
    if not note:
        return {"success": False, "error": "Note is empty"}
    
    file_bytes,ext = download_file(note)
    document_text = extract_text(file_bytes,ext)
    content_h = content_hash(document_text) #creates the hash for the text

    #new chnange: query by hash instead so we dont analyze notes with similar contents
    try:
        analysis_exist = DocumentAnalysis.query.filter_by(content_hash= content_h).first()

        #anlysis for this note exist just add the existing data(to avoid naming errors)
        if analysis_exist:
            linked = create_Doc_Analysis(note.notes_id,analysis_exist,content_h,analysis_exist.embedding)
            db.session.add(linked)
            db.session.commit()
            return linked

        #if analysis doesnt exist already create one then add to database
            
        metadata = analyze_document(document_text)   #returns document response format
        if not metadata.get("success"):
            return {"success": False, "error": metadata.get("error")}
        if not metadata.get("result"):
            return {"success": False, "error": "analysis is empty"}
        
        #build and store the vector embedding for the new docuemnt analysis
        result = metadata.get("result")
        embedding = get_embedding(build_embedding_text(result))
        analysis = create_Doc_Analysis(note.notes_id,metadata.get("result"),content_h,embedding)
        db.session.add(analysis)
        db.session.commit()
        
        return {"success": True, "analysis": analysis}  #return type: DocumentAnalysis Object
    
    except KeyError as error:
        db.session.rollback()
        return {"success": False, "error": f"Missing analysis field: {error.args[0]}"}
    
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}









#-----------------------------PHASE 3: COMBINE ANALYZE AND SAVE DOCUEMNTS-------------------------
# def analyze_and_save_analysis(note):
#     #Generate an analysis for a given note then save the analysis to the database
#     analysis = analyze_document(note)
#     #if analysi sfailed return the error message
#     if not analysis.get("success"):
#         return analysis
    
#     return save_document_analysis(note,analysis)


# #------------------------PHASE 4: Combine the document analysis for a user or gorup study pool to use as a study profile-----
# #get analyses for notes without a analysis
# def gen_missing_analyses(notes):
#     if not notes:
#         return {"success": False, "error": "No notes provided"}
#     try:
#         for note in notes:
#             #get analysis for each note if nothing returned create one
#             analysis = DocumentAnalysis.query.filter_by(note_id=note.notes_id).first()
#             if not analysis:
#                 analysis_result = analyze_document(note)
                
#                 #if note has no analysis create one and save to the database
#                 if analysis_result.get("success"):
#                     save_result = save_document_analysis(note,analysis_result)
#                     if not save_result.get("success"):continue
#         return {"success": True}
#     except Exception as e:
#       return {"success": False, "error":str(e)}




def get_user_doc_analyses(user_id):
    if not user_id: return {"success": False, "error": "User ID is missing"}

    try:
        #generate users 10 most recent uploads to use for reccomendation
        user_analyses = db.session.query(DocumentAnalysis
                                         ).join(Notes,DocumentAnalysis.note_id == Notes.notes_id
                                                ).filter(Notes.user_id == user_id,Notes.group_id.is_(None)
                                                         ).order_by(Notes.time_uploaded.desc()).limit(10).all()
        #if empty retr=urn error
        if not user_analyses:
            return {"success": False, "error": "No analyzed notes found for the user"}
        
        return {"success": True, "analyses": user_analyses}
    except Exception as e:
        return {"success": False, "error": str(e)}
    

def get_group_doc_analyses(group_id):
    if not group_id:
        return {"success": False, "error": "Group ID does not exist"}

    try:
        #generate users 10 most recent uploads to use for recommendation
        group_analyses = db.session.query(DocumentAnalysis
                                         ).join(Notes,DocumentAnalysis.note_id == Notes.notes_id
                                                ).filter(Notes.group_id== group_id
                                                         ).order_by(Notes.time_uploaded.desc()).limit(10).all()
        #if empty retr=urn error
        if not group_analyses:
            return {"success": False, "error": "No analyzed notes found for this group"}
        
        return {"success": True, "analyses": group_analyses}
    except Exception as e:
        return {"success": False, "error": str(e)}


#Combine the queries for the users documents to build a profile for the reccomendation
def build_study_profile(analyses_result):
    if not analyses_result:
        return {"success": False, "error": "Could not retrieve document analyses"}
    
    if not analyses_result.get("success"):
        return {"success": False, "error": analyses_result.get("error","Could not retrieve document analyses")}
    
    analyses = analyses_result.get("analyses")

    if not analyses:
        return {"success": False, "error": "No document analyses were provided"}
    
    #idea: we do a similarity between the data for each note counting them to build the weights
    subject_count = Counter()
    topic_count = Counter()
    keyword_count = Counter()
    academic_level_count = Counter()

    for analysis in analyses:
        subject_count[analysis.subject.strip().lower()]+=1
        topic_count.update(topic.strip().lower() for topic in analysis.topics)
        keyword_count.update(keyword.strip().lower() for keyword in analysis.keywords)
        academic_level_count[analysis.academic_level.strip().lower()]+=1
    
    profile = {
        #We get the top k most common ocunts for each attribute
        "subjects": [subject for subject,_ in subject_count.most_common(5)],
        "topics": [topic for topic,_ in topic_count.most_common(7)],
        "keywords": [keyword for keyword,_ in keyword_count.most_common(15)],
        "academic_level": (academic_level_count.most_common(1)[0][0]),
        "document_count": len(analyses)
    }

    return {"success": True, "profile": profile}

#Combine the functions and create a study profile for the books api
def create_user_study_profile(user_id):
    analyses_result = get_user_doc_analyses(user_id)
    if not analyses_result.get("success"):
        return analyses_result
    
    return build_study_profile(analyses_result)

def create_group_study_profile(group_id):
    analyses_result = get_group_doc_analyses(group_id)
    if not analyses_result.get("success"):
        return analyses_result
    return build_study_profile(analyses_result)




            

    

