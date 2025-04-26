from fastapi import FastAPI
from pydantic import BaseModel
from llama_cpp import Llama
from threading import Lock
import re
import traceback

app = FastAPI()

# Configure your model here
MODEL_PATH = "C:\\Users\\amele\\model\\"
MODEL_FILE = "gemma-2-2b-neogenesis-ita-Q4_K_M.gguf"    # "gemma-3-4b-it-q4_0_s.gguf" #"zephyr-7b-beta.Q4_0.gguf"
CHAT_FORMAT = "gemma"
llm_lock = Lock()

FOURTH_WALL_PREFIXES = [
    'You replied:',
    'You reply:',
    'The NPC replies:',
    'The NPC said:',
    'They respond:',
    'The system says:',
    'Assistant:'
]

INSTRUCTIONS = (
    "You are a character in a fantasy world. You are not an AI or assistant. "
    "You do not describe quests like a designer. "
    "Always respond only with brief in-character first person dialogue of 150 words or less. "
    "Respond in no more than 2 or 3 short paragraphs totaling no more than 150 words. Speak plainly and briefly. "
    "Stay in character as your persona no matter what the player says. "
    "Do not explain your actions. Do not generate meta-commentary. Do not offer suggested follow-ups. "
    "Never structure responses as outlines, lists, or explanations. "
    "Respond only as your character, using only first person dialogue. Never break character. "
    "Never describe yourself as an AI, chatbot, or assistant. "
    "Avoid references to real world people, places or events. "
    "Do not generate harmful or inappropriate content. "
)

QUEST_QUERY = "Convert the quest description into JSON using the defined schema. Do not invent fields. Respond only with JSON.\n"

QUEST_INSTRUCTIONS = (
    "Given a quest description, output a JSON object representing that quest description in the specified JSON format. "
    "Where details are missing from the required format, fill them in with a proposed value consistent with the quest description.\n"
    "Respond ONLY with the defined JSON format in a code block. Do not explain, narrate, or comment. Do not invent new fields.\n"
    "A quest must have a short title, a long description, a list of locations, a list of objects, a list of NPCs and a list of goals.\n"
    "The goals.target field should exactly match the key of a location, object, or NPC defined elsewhere in the quest. "
)

QUEST_JSON = ("Required JSON format: "
    "{"
    "\"title\": \"string\","
    "\"lore\": \"string\","
    "\"locations\": ["
    "{\"key\": \"string\", \"desc\": \"string\"}"
    "],"
    "\"objects\": ["
    "{\"key\": \"string\", \"location\": \"string\", \"desc\": \"string\"}"
    "],"
    "\"npcs\": ["
    "{\"key\": \"string\", \"location\": \"string\", \"dialogue\": [\"string\"]}"
    "],"
    "\"goals\": ["
    "{\n"
    "\"key\": \"Short summary like 'Deliver the package'\","
    "\"desc\": \"In-world description of the goal\","
    "\"type\": \"One of: findlocation, findobject, findnpc, giveto\","
    "\"target\": \"What is being found/given (e.g., room key, object key, npc key)\","
    "\"object\": \"Only for 'giveto' — npc to give 'target' to (optional)\""
    "}"
    "]"
    "}"
)

# Load model
llm = Llama(
    model_path=MODEL_PATH + MODEL_FILE,
    n_ctx=4096,
    n_threads=12,
    n_gpu_layers=35,            # Use your GPU if supported, else set to 0
    chat_format=CHAT_FORMAT
)

# Pydantic models for request parsing
class Message(BaseModel):
    role: str
    content: str

class RequestData(BaseModel):
    mode: str
    persona: str
    messages: list[Message]
    max_tokens: int = 500
    temp: float = 0.7


def assemble_messages(data: RequestData):
    assembled_messages = [] 
    moremessages = []

    if data.mode == "quest":
        assembled_messages.append({"role": "system", "content": QUEST_INSTRUCTIONS + QUEST_JSON})
        assembled_messages.append({"role": "user", "content": data.messages[0].content + QUEST_QUERY + QUEST_JSON})
    else:
        assembled_messages.append({"role": "system", "content": f"Your persona: {data.persona}. {INSTRUCTIONS}. "})
        assembled_messages.append({"role": "user", "content": "Respond to the following as your persona of " + data.persona})
        moremessages = [{"role": msg.role, "content": msg.content} for msg in data.messages]
        assembled_messages.extend(moremessages)

    print(f"Assembled messages: {assembled_messages}")

    return assembled_messages

def process_response(mode: str, response: str, finish_reason: str) -> str:
    if mode != "quest":
        response = normalize_symbols(response or "")
        response = filter_response(response or "", finish_reason)
        response = strip_fourth_wall_intro(response or "")

    return response

@app.post("/generate")
def generate_response(data: RequestData):
    print(f"Received data: {data}")

    with llm_lock:
        try:
            print("Using llama_cpp.create_chat_completion()")
            messages = assemble_messages(data)

            result = llm.create_chat_completion(
                messages=messages,                  # type: ignore[arg-type]
                max_tokens=data.max_tokens,
                temperature=data.temp,
                stream=False
            )
            response = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            finish_reason = result["choices"][0]["finish_reason"]    # type: ignore

            print(f"Finish reason: {finish_reason}")
            
        except Exception as e:
            print(f"Fallback to prompt mode due to error: {e}")
            traceback.print_exc()
            
            flat_prompt = "\n".join(f"{msg.role.title()}: {msg.content}" for msg in data.messages)
            result = llm.create_completion(
                prompt=flat_prompt,
                max_tokens=data.max_tokens,
                temperature=data.temp
            )
            response = result.get("choices", [{}])[0].get("text", "")
            finish_reason = result["choices"][0]["finish_reason"]    # type: ignore

    print(f"Generated (pre-processed) response: {response}")
    response = process_response(data.mode, response or "", finish_reason or "")
    print(f"Generated (post-processed) response: {response}")
    
    return {"response": response.strip()}           # type: ignore


def filter_response(response: str, finish_reason: str) -> str:
    """
    Removes paragraphs that are likely out-of-character or meta/instructional.
    """
    # Define phrases that indicate OOC behavior
    filter_starts = [
        "Would you like me to",
        "Here are a few ways",
        "To help you",
        "Let me know if",
        "If you'd like",
        "You could",
        "We could",
        "Here's how",
        "Some options might be",
        "Depending on your preferences",
        "If you're going for",
        "Do you want me to"
    ]

    # Split into paragraphs
    paragraphs = re.split(r"\n\s*\n", response)

    # Keep only in-character lines
    filtered = [
        para for para in paragraphs
        if not any(para.strip().lower().startswith(start.lower()) for start in filter_starts)
    ]

                # When the response was truncated due to the token limit eliminate the final (incomplete) paragraph.
    if finish_reason == "length" and len(paragraphs) > 1:
        filtered_response = "\n\n".join(paragraphs[:-1]).strip()
    else:
        filtered_response = "\n\n".join(filtered).strip()

    return filtered_response

def normalize_symbols(text: str) -> str:
    return (
        text.replace("“", '"')
            .replace("”", '"')
            .replace("‘", "'")
            .replace("’", "'")
            .replace("…", "...")    # ellipsis
            .replace("—", "-")      # em-dash
            .replace("–", "-")      # en-dash
            .replace("**", "")      # Emphasis

    )

def strip_fourth_wall_intro(text):
    # Normalize smart quotes to straight quotes
    text = text.replace('“', '"').replace('”', '"')

    # Check for any defined prefix and remove it
    for prefix in FOURTH_WALL_PREFIXES:
        # Check for prefix with optional quote immediately after
        pattern = rf'^{re.escape(prefix)}\s*["\']?'
        if re.match(pattern, text):
            # Remove the prefix + optional opening quote
            cleaned = re.sub(pattern, '', text, count=1)
            # Remove a trailing quote if it exists
            if cleaned.endswith('"') or cleaned.endswith("'"):
                cleaned = cleaned[:-1]
            return cleaned.strip()

    return text
