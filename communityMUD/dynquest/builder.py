import numpy as np
from evennia.objects.models import ObjectDB
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import traceback
from evennia import create_script, create_object
from evennia.scripts.scripts import DefaultScript
from evennia.utils.logger import log_info
from evennia.utils.utils import make_iter
from dynquest.models import QuestEntry
import json

TRANSFORMER = SentenceTransformer("all-MiniLM-L6-v2")
LOCATION_SIMILARITY_THRESHOLD = 0.70


def get_similar_locations(description, transformer, threshold=0.85, top_n=3):
    """
    Finds existing in-game locations that are semantically similar to a new description.

    Args:
        description (str): The new location description to compare.
        transformer (SentenceTransformer): Your embedding model instance.
        threshold (float): Similarity threshold for "close enough" matches.
        top_n (int): Number of top matches to return.

    Returns:
        List of tuples: (room, similarity_score), sorted by descending score.
    """
    # Get all rooms that might be reusable (e.g., tagged or with a desc)
    candidates = ObjectDB.objects.filter(
        db_typeclass_path__icontains="Room"
    )

    print(f"Candidates: {candidates}")

    candidates = [room for room in candidates if room.db.desc]

    if len(candidates) == 0:
        return []

    descriptions = []
    rooms = []
    room_embeddings = []

    for room in candidates:
        desc = room.db.desc

        print(f"Checking {room}: {desc}")

        if not desc:
            continue

        rooms.append(room)
        descriptions.append(desc)

        # Use cached embedding if available, else compute and store
        if room.db.embedding:
            room_embeddings.append(np.array(room.db.embedding))
        else:
            embedding = transformer.encode([desc])[0]
            room.db.embedding = embedding.tolist()
            room_embeddings.append(embedding)

    # Embed the query
    query_embedding = transformer.encode([description])[0]
    query_embedding = np.array(query_embedding)

    similarities = cosine_similarity(
        [query_embedding],  # type: ignore 
        room_embeddings          # type: ignore
    )[0]

    scored = list(zip(rooms, similarities))

    print(f"Scoring {scored}")

    filtered = [(room, score) for room, score in scored if score >= threshold]

    print(f"Filtered {filtered}")

    # Sort by descending similarity
    return sorted(filtered, key=lambda x: x[1], reverse=True)[:top_n]


class QuestBuilderScript(DefaultScript):
    """
    Periodically checks for pending quests and builds game content from them.
    """

    def at_script_creation(self):
        self.key = "quest_builder_script"
        self.desc = "Builds rooms, NPCs, and items from pending quests."
        self.interval = 60  # every 60 seconds; adjust as needed
        self.persistent = True
        self.start_delay = True

    def do_build(self, pending: QuestEntry):
        if pending.status != "pending":
            return
        
        try:
            print(f"Building quest: {pending.title} ({pending.quest_id})")
            log_info(f"Building quest: {pending.title} ({pending.quest_id})")

            data = pending.raw_data.get("quest")
            if not data:
                log_info("Missing 'quest' key in raw_data.")
                pending.status = "failed"
                pending.save()
                return

            tag = f"quest:{pending.quest_id}"
            location_map = {}

            # --------------------------
            # Parse goals to infer assets
            # --------------------------
            goals = data.get("goals", [])
            goal_targets = {
                "findlocation": set(),
                "findnpc": set(),
                "findobject": set(),
                "giveto": set(),
            }

            for goal in goals:
                goal_type = goal.get("type")
                target = goal.get("target")
                obj = goal.get("object")

                if goal_type in ("findlocation", "findnpc", "findobject") and target:
                    goal_targets[goal_type].add(target)
                elif goal_type == "giveto" and target and obj:
                    goal_targets["findnpc"].add(target)
                    goal_targets["findobject"].add(obj)

            # Build fast-lookup sets from declared quest elements
            existing_location_keys = {loc["key"] for loc in data.get("locations", [])}
            existing_object_keys = {obj["key"] for obj in data.get("objects", [])}
            existing_npc_keys = {npc["key"] for npc in data.get("npcs", [])}

            # Inject inferred locations from goals
            for key in goal_targets["findlocation"]:
                if key not in existing_location_keys:
                    data.setdefault("locations", []).append({
                        "key": key,
                        "desc": f"A mysterious place called {key}."
                    })
                    existing_location_keys.add(key)

            # Inject inferred NPCs from goals
            for key in goal_targets["findnpc"]:
                if key not in existing_npc_keys:
                    data.setdefault("npcs", []).append({
                        "key": key,
                        "location": "limbo",  # fallback if location not yet known
                        "dialogue": [f"{key} grunts in vague acknowledgment."]
                    })
                    existing_npc_keys.add(key)

            # Inject inferred objects from goals
            for key in goal_targets["findobject"]:
                if key not in existing_object_keys:
                    data.setdefault("objects", []).append({
                        "key": key,
                        "desc": f"A quest item labeled {key}.",
                        "location": "limbo"
                    })
                    existing_object_keys.add(key)

            # --------------------------
            # Create or reuse locations
            # --------------------------
            for loc in data.get("locations", []):
                loc_desc = loc["desc"]
                existing_matches = get_similar_locations(loc_desc, transformer=TRANSFORMER, threshold=LOCATION_SIMILARITY_THRESHOLD)

                if existing_matches:
                    chosen_room = existing_matches[0][0]
                    log_info(f"Reusing existing location: {chosen_room.key} (score: {existing_matches[0][1]:.2f})")
                else:
                    chosen_room = create_object(
                        "typeclasses.rooms.Room",
                        key=loc["key"],
                        attributes=[("desc", loc["desc"])],
                        tags=[tag]
                    )
                    log_info(f"Created new room: {chosen_room.key}")

                location_map[loc["key"]] = chosen_room

            # --------------------------
            # Create objects
            # --------------------------
            for obj in data.get("objects", []):
                loc_obj = location_map.get(obj["location"])
                if not loc_obj:
                    loc_obj = location_map.get("limbo") or create_object("typeclasses.rooms.Room", key="limbo", attributes=[("desc", "A hazy void.")])
                create_object(
                    "typeclasses.objects.Object",
                    key=obj["key"],
                    location=loc_obj,
                    attributes=[("desc", obj["desc"])],
                    tags=[tag]
                )

            # --------------------------
            # Create NPCs
            # --------------------------
            for npc in data.get("npcs", []):
                loc_obj = location_map.get(npc["location"])
                if not loc_obj:
                    loc_obj = location_map.get("limbo") or create_object("typeclasses.rooms.Room", key="limbo", attributes=[("desc", "A hazy void.")])
                npc_obj = create_object(
                    "typeclasses.creatures.basecreature.Mob",
                    key=npc["key"],
                    location=loc_obj,
                    tags=[tag]
                )
                npc_obj.db.dialogue = npc.get("dialogue", [])

            pending.status = "built"
            pending.save()
            log_info(f"Quest {pending.quest_id} built successfully.")

        except Exception as e:
            log_info(f"[QuestBuilderScript] Error building quest: {e}")
            traceback.print_exc()
            if pending:
                log_info(f"[QuestBuilderScript] Failed quest {pending.title}: {e}")
                pending.status = "error"
                pending.save()

    def at_repeat(self):
        """
        Periodically checks for pending quests and builds game content from them.

        This method retrieves the oldest pending quest from the database,
        processes its data, and generates in-game locations, objects, and NPCs.
        Locations are either reused if a similar one exists or created anew.
        Similarly, objects and NPCs are created at their specified locations.

        It also ensures that all goal-related targets are created, even if not explicitly
        defined in the original data (e.g., inferred NPCs/objects for "giveto" goals).

        If any errors occur during processing, the quest status is updated to
        "failed", otherwise, it is marked as "built" upon successful completion.
        """

        pending = QuestEntry.objects.filter(status="pending").order_by("timestamp_created").first()
        if not pending:
            print("No pending quests found.")
            log_info("No pending quests found.")
            return

        self.do_build(pending)

