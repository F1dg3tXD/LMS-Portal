import os
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import HumanMessage, AIMessage

MEMORY_DIR = "memory"
MEMORY_FILE = os.path.join(MEMORY_DIR, "context.txt")

# Ensure memory folder exists
os.makedirs(MEMORY_DIR, exist_ok=True)


def load_memory():
    messages = []
    if not os.path.exists(MEMORY_FILE):
        return messages

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    role = None
    content = []
    for line in lines:
        line = line.strip()
        if line.startswith("User:"):
            if role and content:
                messages.append(_msg_from(role, "\n".join(content)))
            role = "user"
            content = [line[5:].strip()]
        elif line.startswith("Assistant:"):
            if role and content:
                messages.append(_msg_from(role, "\n".join(content)))
            role = "assistant"
            content = [line[10:].strip()]
        else:
            content.append(line)

    if role and content:
        messages.append(_msg_from(role, "\n".join(content)))

    return messages


def save_to_memory(user_msg, assistant_msg):
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"User: {user_msg.strip()}\n")
        f.write(f"Assistant: {assistant_msg.strip()}\n")


def _msg_from(role, content):
    if role == "user":
        return HumanMessage(content=content)
    elif role == "assistant":
        return AIMessage(content=content)
    else:
        raise ValueError(f"Unknown role: {role}")


def search_duckduckgo(query):
    try:
        search = DuckDuckGoSearchRun()
        result = search.run(query)
        return result
    except Exception as e:
        return f"LangChain search error: {e}"
