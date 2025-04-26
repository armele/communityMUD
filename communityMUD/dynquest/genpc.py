import subprocess
from typeclasses.characters import Character
import traceback
import json
import numpy as np
import requests
import re
from dynquest.helpers import QuestEval
from dynquest.builder import TRANSFORMER
from evennia.utils.logger import log_info

class GenPC(Character):
    """
    A simple NPC that generates responses using a local LLM.
    """
    MODEL_URL = "http://127.0.0.1:8000/generate"            # URL for local LLM
    MODEL_TIMEOUT = 45                                      # Timeout for remote LLM in seconds
        
    lore_data = None
       

    def at_object_creation(self):
        """Set up defaults when NPC is created."""
        self.db.max_history = 10
        self.db.persona = "a grizzled railroad ticket-taker from the early 1900s"
        self.db.conversation_history = []
        self.db.quest_giver = False
        return super().at_object_creation()
    
    def at_init(self):
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

    def was_quest(self, dq: QuestEval):
        """
        If the response seems quest-like, attempt to analyze it and create a persistable QuestEntry.
        """
        log_info(f"[QuestAnalysis] Analyzing response: {dq}")

        if dq.is_quest_worthy() and dq.quest_confidence_score() >= 2:
            log_info("[QuestAnalysis] Prompting for quest design.")
            quest = self.analyze_response_for_quest(dq.text)
        else:
            log_info("[QuestAnalysis] Skipped: not quest-worthy.")
            return None

        return quest
            
    def at_quest_response(self, response, from_obj):
        """
        Check to see if the response seems quest-like, and if so, persist it.
        """
        try:
            dq = QuestEval(response)
            quest = self.was_quest(dq)
            if quest:
                dq.persist_generated_quest(quest, player=from_obj)
                log_info(f"Successfully persisted quest: {quest}")
            else:
                log_info(f"Received a non-questy response: {response}")
        except Exception as e:
            traceback.print_exc()
            log_info(f"Failed to persist quest Response: {response} Quest: {quest}: {e} ")


    def at_heard_say(self, message, from_obj=None, **kwargs):
        """
        Called when someone speaks in the room.
        """
        print(f"Heard: {message} from {from_obj}")

        if from_obj and from_obj != self:
            response = self.generate_response_remote(message)

            if response:
                # Update conversation history
                if self.db.conversation_history is None:
                    self.db.conversation_history = []

                self.db.conversation_history = self.db.conversation_history[-self.db.max_history:]
                self.db.conversation_history.append(f"{message}")
                self.db.conversation_history.append(f"You replied: '{response}'")                
                self.execute_cmd(f"say {response}", msg_obj=self)
                
                if self.db.quest_giver:
                    self.at_quest_response(response, from_obj.account)
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
            query_embedding = TRANSFORMER.encode([message])[0]

            # Compute cosine similarity
            query_norm = np.linalg.norm(query_embedding)
            similarities = [
                (i, np.dot(query_embedding, embed) / (query_norm * np.linalg.norm(embed)))
                for i, embed in enumerate(embeddings)
            ]

            # Sort by similarity score in descending order
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_chunks = [lore_chunks[i] for i, _ in similarities[:top_n]]

            # print(f"Top {top_n} chunks: {top_chunks}")

            return "\n".join(top_chunks)

        except Exception as e:
            print(f"Error in get_relevant_lore: {e}")
            return ""

    def generate_response_remote(self, message):
        try:
            # Prepare chat-style messages
            chat_history = []

            # System persona and role
            chat_history.append({
                "role": "system",
                "content": f"Lore elements: {self.get_relevant_lore(message)}"
            })

            # Add conversation history as user/assistant turns
            if self.db.conversation_history is None:
                self.db.conversation_history = []

            for line in self.db.conversation_history[-6:]:
                if line.startswith("You replied:"):
                    chat_history.append({
                        "role": "assistant",
                        "content": line
                    })
                elif " said '" in line:
                    chat_history.append({
                        "role": "user",
                        "content": line
                    })

            # Current message from the player
            chat_history.append({"role": "user", "content": message})

            # Call the remote LLM API
            response = requests.post(
                GenPC.MODEL_URL,
                json={
                    "mode": "npc",
                    "persona": self.db.persona,
                    "messages": chat_history,
                    "max_tokens": 250,
                    "temp": 0.5
                },
                timeout=GenPC.MODEL_TIMEOUT
            ).json()["response"]

            if any(x in response.lower() for x in ["out of character", "as an ai", "grouplayout", "ai assistant"]):
                response = "I'm afraid I can't speak on such matters."

            return response

        except Exception as e:
            print(f"LLM API call failed: {e}")
            traceback.print_exc()
            return "I do not have an answer right now."

    def analyze_response_for_quest(self, npc_response):
        """
        Ask the LLM to extract a build plan in JSON.
        """

        try:
            messages = [
                {"role": "user", "content": f"Quest description: {npc_response}"}
            ]

            try:
                modelrequest = {
                        "mode": "quest",
                        "persona": self.db.persona,
                        "messages": messages,
                        "max_tokens": 1200,
                        "temp": 0.3
                    }
            except Exception as e:
                print(f"[QuestAnalysis] Error assembling model request: {e}")
                traceback.print_exc()
                return None

            result = requests.post(
                GenPC.MODEL_URL,
                json = modelrequest,
                timeout = GenPC.MODEL_TIMEOUT
            )

            raw_response = result.json().get("response", "").strip()

            match = re.search(r"```json\s*(.*?)```", raw_response, re.DOTALL)
            json_content = match.group(1).strip() if match else raw_response

            try:
                parsed = json.loads(json_content)
            except Exception as e:
                print(f"[QuestAnalysis] Error parsing JSON {json_content}: {e}")
                traceback.print_exc()
                return None

            if not parsed or parsed.get("title") is None:
                log_info(f"[QuestAnalysis] could not parse raw response: {raw_response}")
                return None
            else:
                log_info(f"[QuestAnalysis] parsed raw response: {raw_response}")
                parsed.update({"originating_response": npc_response})

            return parsed

        except Exception as e:
            print(f"[QuestAnalysis] Error: {e}")
            traceback.print_exc()
            return None
