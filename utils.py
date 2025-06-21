import requests

def search_duckduckgo(query):
    try:
        resp = requests.get("https://api.duckduckgo.com/", params={
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        })
        data = resp.json()
        abstract = data.get("Abstract", "")
        heading = data.get("Heading", "")
        url = data.get("AbstractURL", "")

        if abstract:
            return f"🔍 {heading}: {abstract}\n{url}"
        else:
            return "No summary found, but you can try: https://duckduckgo.com/?q=" + query
    except Exception as e:
        return f"Search error: {e}"
