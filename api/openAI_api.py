import os
import io
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
    #combines both functions and promots open ai to summarize the docuement/
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
                "content": "Summarize the following docuemnt, with no hallucianations and only user information inthe actual document"
                },
                
                {"role": "user", "content": text}
            ]
        )
        return {"success": True, "summary": response.choices[0].message.content}

    except Exception as e:
        return {"success": False, "error": str(e)}




    










#def generate_summary(notes_list):
#     client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

#     if not notes_list:
#         return {"status": False, "error": "No notes found."}

#     try:
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {
#                     "role": "system",
#                     # enforcing it solely retrieve and summarize notes
#                     "content": (
#                         "This is a factual summarization tool. Do not assume or input ideas or concepts."
#                         "Turn the provided notes into a clear 2 page markdown summmary without "
#                         "unecessary information, intros, fillers, or outros."
#                         "Strictly summarize the user's provided notes using only the facts present in the text."

#                     )
#                 },
#                 {"role":"user", "content": f"Summarize these notes: \n\n{chr(10).join(notes_list)}"}
#             ],
#             # makes AI response more factual and straigh foward to avoid random responses
#             temperature=0.2

#         )
#         return {"success": True, "summary": response.choices[0].message.content}

#     except Exception:
#         return {"success": False, "error": "Could not generate summary right now."}