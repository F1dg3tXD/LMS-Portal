from langchain_community.tools import DuckDuckGoSearchRun

def search_duckduckgo(query):
    try:
        search = DuckDuckGoSearchRun()
        result = search.run(query)
        return result
    except Exception as e:
        return f"LangChain search error: {e}"
