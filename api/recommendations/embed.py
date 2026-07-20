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

load_dotenv()
open_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
books_client = os.getenv("BOOKS_KEY")
GOOGLE_BOOKS_URL = os.getenv("BOOKS_URL")


#converts the document Analysis object into full string text to convert to a vector embedding
def build_embedding_text(analysis: DocumentAnalysis):
    return (
        f"Subject: {analysis.subject}"
        f"Topics: {analysis.topics}"
        f"Keywords: {analysis.keywords}"
        f"academic_level: {analysis.academic_level}"
        f"Summary: {analysis.summary}"
    )

#Takes the text returned from build_embedding_text and converts into a vector embedding. return: vector
def get_embedding(text: str):
    response = open_client.embeddings.create(model="text-embedding-3-small", input=text)
    return response.data[0].embedding


