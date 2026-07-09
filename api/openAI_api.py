import os
from dotenv import load_dotenv
from openai import OpenAI
from io import BytesIO
from storage import get_supabase

load_dotenv()
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
supabase = get_supabase()


def get_note_file(note):
    #converts note from supabase storage to raw bytes to treat as local file for gemni to read
    file_bytes = supabase.storage.from_("notes").download(note.file_path)   #downloads file from supabase storage

    #convert Bytes into file-like object
    file_name = getattr(note,"note_name",None) or os.path.basename(note.file_path)
    file_obj = BytesIO(file_bytes)
    file_obj.name = file_name
    return file_obj



def generate_summary(note):

    if not note:
        return {"status": False, "error": "No notes found."}
    

    try:
        file_obj = get_note_file(note)
        uploaded_file = client.files.create(file=file_obj,purpose="user_data")
        response = client.responses.create(
            model="gpt-4o-mini",
            # makes AI response more factual and straight foward to avoid random responses
            temperature = 0.2,
            input=[
                {
                    "role": "system",
                    # enforcing it solely retrieve and summarize notes
                    "content":[
                           {
                                "type": "input_text",
                                "text": ("You are an assistant expert that summarizes user documents."
                                         "This is a factual summarization tool. Do not assume or input ideas or concepts."
                                        "Turn the provided notes into a clear 2 page markdown summmary without "
                                    "unecessary information, intros, fillers, or outros."
                                    "Strictly summarize the user's provided notes using only the facts present in the text."
                                )
                                        
                            }
                        ]
                    },
                    {
                           "role": "user",
                           "content": [
                                  {
                                         "type": "input_text",
                                         "text": "Summarize the key points of this document"
                                  },
                                    {
                                         "type": "input_file",
                                         "file_id": uploaded_file.id
                                    }
                            ]
                    }
                ],
            )
        return {"success": True, "summary": response.output_text}

    except Exception:
        return {"success": False, "error": "Could not generate summary right now."}
