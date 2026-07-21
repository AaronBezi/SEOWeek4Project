import os
import re
import requests


def clean_query(query: str) -> str:
    # 1. Remove file extensions anywhere in the query string
    cleaned = re.sub(r'\.(pdf|docx|doc|txt)\b', '', query, flags=re.IGNORECASE)
    # 2. Replace non-alphanumeric characters with spaces
    cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
    # 3. Collapse multiple spaces and strip leading/trailing whitespace
    cleaned = " ".join(cleaned.split())

    # 4. Limit to first 6 terms to keep search requests structured and valid
    words = cleaned.split()[:6]
    return " ".join(words)


def search_books(query: str):
    if not query or not query.strip():
        return {"success": False, "error": "Search Query is empty"}

    cleaned_q = clean_query(query)

    if not cleaned_q:
        cleaned_q = "textbook study guide"

    url = os.getenv("BOOKS_URL", "https://www.googleapis.com/books/v1/volumes")
    api_key = os.getenv("BOOKS_KEY")

    params = {
        "q": cleaned_q,
        "maxResults": 5,
        "printType": "books",
        "langRestrict": "en"
    }

    if api_key:
        params["key"] = api_key

    try:
        response = requests.get(url, params=params, timeout=10)

        # Handle rate limits
        if response.status_code == 429:
            return {
                "success": False,
                "error": "Google Books API rate limit reached. Please wait a moment and try again."
            }

        # Handle temporary Google outage/maintenance (503 Service Unavailable)
        if response.status_code in (500, 502, 503, 504):
            return {
                "success": False,
                "error": "Google Books service is temporarily unavailable. Please try again in a few seconds."
            }

        response.raise_for_status()
        data = response.json()
        books = []

        for item in data.get("items", []):
            volume = item.get("volumeInfo", {})
            if not item.get("id") or not volume.get("title"):
                continue

            books.append({
                "book_id": item.get("id"),
                "title": volume.get("title"),
                "authors": volume.get("authors", ["Unknown Author"]),
                "description": volume.get("description", "No description available."),
                "categories": volume.get("categories", []),
                "preview_link": volume.get("previewLink")
            })

        return {"success": True, "books": books}

    except requests.RequestException as e:
        return {"success": False, "error": f"Network error: {str(e)}"}
    except ValueError:
        return {"success": False, "error": "Invalid JSON returned by Books API"}