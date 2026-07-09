import os
from dotenv import load_dotenv
from openai import OpenAI
from storage import get_supabase

load_dotenv()
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
supabase = get_supabase()

def extract_text(note):
    #get raw file bytes from supabase storage so openai api key can understand the format
    file_bytes = supabase.storage.from_("notes").download(note.file_path)
    file_name = note.file_path.split("/")[-1]
    return file_bytes,file_name


def generate_summary(note):
    if not note:
        return {"status": False, "error": "No notes found."}

    #upload OpenAI's files API
    try:
        file_bytes,file_name = extract_text(note)
        uploaded_file = client.files.create(file=(file_name,file_bytes),purpose="user_data")

        #Model summarization
        response = client.responses.create(
            model="gpt-4.1",
            temperature = 0.2,
            input=[
                {"role":"user",
                "content":[
                    {"type":"input_file",
                     "file_id": uploaded_file.id
                    },
                        
                    {"type": "input_text",
                     "text": "Summarize this document, using only the content in the document"
                     "do not imagine or infer anything about the content, only correct notes if they are wrong"},
                ],
                }],
        )
        return response.output_text
    except Exception:
        return {"success": False, "error": "Could not generate summary right now."}




        
    
    





# def generate_summary(notes_list):

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