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
    file_obj = BytesIO(file_bytes)
    file_obj.name = note.file_name
    return file_obj



def generate_summary(note):

    if not note:
        return {"status": False, "error": "No notes found."}
    
    file_obj = get_note_file(note)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    # enforcing it solely retrieve and summarize notes
                    "content": (
                        "This is a factual summarization tool. Do not assume or input ideas or concepts."
                        "Turn the provided notes into a clear 2 page markdown summmary without "
                        "unecessary information, intros, fillers, or outros."
                        "Strictly summarize the user's provided notes using only the facts present in the text."

                    )
                },
                {"role":"user", "content": f"Summarize these notes: \n\n{chr(10).join(notes_list)}"}
            ],
            # makes AI response more factual and straight foward to avoid random responses
            temperature=0.2

        )
        return {"success": True, "summary": response.choices[0].message.content}

    except Exception:
        return {"success": False, "error": "Could not generate summary right now."}
