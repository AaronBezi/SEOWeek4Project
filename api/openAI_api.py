import os
from dotenv import load_dotenv
from openai import OpenAI

def generate_summary(notes_list):
    load_dotenv()
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

    if not notes_list:
        return {"status": False, "error": "No notes found."}

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
            # makes AI response more factual and straigh foward to avoid random responses
            temperature=0.2

        )
        return {"success": True, "summary": response.choices[0].message.content}

    except Exception:
        return {"success": False, "error": "Could not generate summary right now."}