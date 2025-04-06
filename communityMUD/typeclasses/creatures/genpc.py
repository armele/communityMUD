import subprocess
from typeclasses.characters import Character
from evennia.utils import create
import traceback
from gpt4all import GPT4All
from threading import Lock
import json
import numpy as np
from sentence_transformers import SentenceTransformer

class GenPC(Character):
    """
    A simple NPC that generates responses using a local LLM.
    """
    MODEL_PATH = "C:\\Users\\amele\\model\\"
    MODEL_NAME = "mistral-7b-openorca.Q4_K_M.gguf" # "gpt4all-13b-snoozy-q4_0.gguf"
    TRANSFORMER = SentenceTransformer("all-MiniLM-L6-v2")
        
    llm = None
    llm_lock = Lock()  # Thread-safe access to shared LLM instance
    lore_data = None

    def is_llm_ready(self):
        return GenPC.llm is not None

    def initialize_model(self):
        """Set up defaults when NPC is created."""
        self.max_history = 10
        self.db.persona = "a grizzled railroad ticket-taker from the early 1900s"
        self.db.conversation_history = []
        self.db.instructions = (
            "You are an NPC in a fantasy MUD. Speak in character as if you are talking to a character in a MUD. "
            "You narrate lore, answer questions, give quests, and provide context about the world. Do not break character. "
            "Never describe code or implementation details. Respond only in character. "
            "Keep your responses to a few sentences and entirely in the first person. "
            "Do not generate harmful or inappropriate content. "
        )
        
        if not self.is_llm_ready():
            model_path = self.db.model_path
            model_name = self.db.model_name
            GenPC.llm = GPT4All(model_name=GenPC.MODEL_NAME, model_path=GenPC.MODEL_PATH)
            GenPC.lore_data = self.load_lore_data()
       

    def at_object_creation(self):
        """Set up defaults when NPC is created."""
        self.initialize_model()
        return super().at_object_creation()
    
    def at_init(self):
        if not self.is_llm_ready():
            print("Reloading LLM model...")
            self.initialize_model()
        return super().at_init()


    def msg(self, text, from_obj=None, **kwargs):
        "Custom msg() method reacting to say."

        if from_obj != self:
            # make sure to not repeat what we ourselves said or we'll create a loop
            try:
                # if text comes from a say, `text` is `('say_text', {'type': 'say'})`
                say_text, is_say = text[0], text[1]['type'] == 'say'
            except Exception:
                is_say = False
            if is_say:
                self.at_heard_say(say_text, from_obj, **kwargs)

    def at_heard_say(self, message, from_obj=None, **kwargs):
        """
        Called when someone speaks in the room.
        """
        print(f"Heard: {message} from {from_obj}")

        if from_obj and from_obj != self:
            response = self.generate_response_v1(message)

            if response:
                # Update conversation history
                self.db.conversation_history = self.db.conversation_history[-self.max_history:]
                self.db.conversation_history.append(f"{from_obj} said '{message}'")
                self.db.conversation_history.append(f"You replied: '{response}'")                
                self.execute_cmd(f"say {response}", msg_obj=self)
                print(f"{self.key} Responds: {response}")
            else:
                self.execute_cmd("emote rubs their chin thoughtfully, but says nothing.")
        else:
            print(f"I don't respond to {from_obj}.")


    def load_lore_data(self):
        """
        Loads lore data from a file if it hasn't been loaded yet.

        Returns:
            list: A list of objects with keys 'content' and 'embedding'
        """
        try:
            if not GenPC.lore_data:
                # Load JSON and extract embeddings with their corresponding lore content
                with open("./world/severed_realms_embeddings.json", "r", encoding="utf-8") as f:
                    GenPC.lore_data = json.load(f)

            if not isinstance(GenPC.lore_data, list):
                raise ValueError("Unexpected JSON structure: Expected a list of objects.")
            
            return GenPC.lore_data
        except Exception as e:
            print(f"Error in loading lore data: {e}")
            traceback.print_exc()
            return None


    def get_relevant_lore(self, message, top_n=3):
        try:
            data = self.load_lore_data()

            # Extract embeddings and lore content
            embeddings = []
            lore_chunks = []
            
            for entry in data: # type: ignore
                if "content" in entry and "embedding" in entry:
                    lore_chunks.append(entry["content"])
                    embeddings.append(np.array(entry["embedding"]))
                else:
                    raise ValueError("Missing 'content' or 'embedding' in an entry.")

            if len(embeddings) != len(lore_chunks):
                raise ValueError("Mismatch between embeddings and lore content count.")

            # Convert to numpy array for batch operations
            embeddings = np.vstack(embeddings)  

            # Generate query embedding
            query_embedding = GenPC.TRANSFORMER.encode([message])[0]

            # Compute cosine similarity
            query_norm = np.linalg.norm(query_embedding)
            similarities = [
                (i, np.dot(query_embedding, embed) / (query_norm * np.linalg.norm(embed)))
                for i, embed in enumerate(embeddings)
            ]

            # Sort by similarity score in descending order
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_chunks = [lore_chunks[i] for i, _ in similarities[:top_n]]

            print(f"Top {top_n} chunks: {top_chunks}")

            return "\n".join(top_chunks)

        except Exception as e:
            print(f"Error in get_relevant_lore: {e}")
            return ""

    def generate_response_v2(self, message):
        """
        Queries a local LLM for a response using chat-style messages.
        """
        try:
            # Get context
            lore_elements = self.get_relevant_lore(message)
            persona = self.db.persona or "an NPC"
            chat_history = []

            # System message
            chat_history.append({
                "role": "system",
                "content": (
                    f"Respond in the persona of {persona}. {self.db.instructions} "
                    f"Relevant lore: {lore_elements}"
                )
            })

            # Append conversation history (as alternating user/assistant)
            history = self.db.conversation_history[-6:]  # Most recent messages
            for line in history:
                if line.startswith("You replied:"):
                    chat_history.append({
                        "role": "assistant",
                        "content": line.replace("You replied: ", "")
                    })
                elif " said '" in line:
                    speaker, msg = line.split(" said '", 1)
                    msg = msg.rstrip("'")
                    chat_history.append({
                        "role": "user",
                        "content": msg
                    })

            # Latest user message
            chat_history.append({
                "role": "user",
                "content": message
            })

            print("Chat history:")
            for m in chat_history:
                print(f"{m['role']}: {m['content']}")

            with GenPC.llm_lock:
                with GenPC.llm.chat_session():  # type: ignore
                    result = GenPC.llm.chat_completion(chat_history, max_tokens=500, temp=0.7)  # type: ignore

            response = result['message']['content'].strip()

            if any(x in response.lower() for x in ["out of character", "as an ai", "grouplayout", "ai assistant"]):
                response = "I'm afraid I can't speak on such matters."

            return response

        except Exception as e:
            print(f"LLM query failed: {e}")
            traceback.print_exc()
            return "I do not have an answer right now."


    def generate_response_v1(self, message):
        """
        Queries a local LLM for a response.
        """
        try:
            history = "\n".join(self.db.conversation_history[-6:]) or "None"
            lore_elements = self.get_relevant_lore(message)

            full_prompt = (
                f"Respond in the persona of {self.db.persona}. {self.db.instructions} "
                f"Relevant lore: {lore_elements}\n"
                f"Conversation history: {history}\n"
            )

            print(f"Full prompt: {full_prompt}")

            with GenPC.llm_lock:
                with GenPC.llm.chat_session(): # type: ignore
                    result = GenPC.llm.generate(full_prompt, max_tokens=500, temp=0.7) # type: ignore

            response = result.strip()

            if any(x in response.lower() for x in ["out of character", "as an ai", "grouplayout", "ai assistant"]):
                response = "I'm afraid I can't speak on such matters."

            return response
        except Exception as e:
            print(f"LLM query failed: {e}")
            traceback.print_exc()
            return "I do not have an answer right now."

