import os
import io
import json
from markitdown import MarkItDown
from dotenv import load_dotenv
from openai import OpenAI
from storage import get_supabase

load_dotenv()
supabase = get_supabase()
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
md = MarkItDown()

def download_file(note):
    #downloads file from supabase storage
    ext = note.file_path.rsplit(".",1)[-1].lower()
    return supabase.storage.from_("notes").download(note.file_path),ext


def extract_text(file,extension):
    #read file returned from supabase and get the text with markdown
    result = md.convert_stream(io.BytesIO(file),file_extension=f".{extension}")
    return result.text_content



def generate_summary(note):
    #combines both functions and prompts open ai to summarize the document
    if not note:
        return {"status": False, "error": "No notes found."}

    file_bytes,ext= download_file(note)
    text = extract_text(file_bytes,ext)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature = 0.2,
            messages = [
                {"role": "system",
                "content": "Summarize the following docuemnt, with no hallucianations and only user information in the actual document"
                },
                
                {"role": "user", "content": text}
            ]
        )
        return {"success": True, "summary": response.choices[0].message.content}

    except Exception as e:
        return {"success": False, "error": str(e)}


import json


def generate_quiz_from_summary(summary_text):
    """
    Takes the generated summary and creates a 10-question quiz
    (Multiple Choice and True/False) based strictly on that text.
    """
    if not summary_text:
        return {"success": False, "error": "No summary content provided."}

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,

            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Create a 10-question practice quiz based strictly "
                        "on the provided summary text. Mix multiple-choice and true/false questions. "
                        "Do not include any external information or hallucinations.\n\n"
                        "Return the quiz as a JSON object matching this exact structure:\n"
                        "{\n"
                        '  "quiz": [\n'
                        "    {\n"
                        '      "question_number": 1,\n'
                        '      "type": "multiple_choice", # or "true_false"\n'
                        '      "question": "The question text here?",\n'
                        '      "options": ["Option A", "Option B", "Option C", "Option D"], # for true_false use ["True", "False"]\n'
                        '      "correct_answer": "Option A"\n'
                        "    }\n"
                        "  ]\n"
                        "}"
                    )
                },
                {"role": "user", "content": f"Summary Text:\n\n{summary_text}"}
            ]
        )

        # Parsing the JSON response from OpenAI
        quiz_data = json.loads(response.choices[0].message.content)
        return {"success": True, "quiz_data": quiz_data}

    except Exception as e:
        return {"success": False, "error": str(e)}
