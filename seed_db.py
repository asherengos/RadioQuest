import os
import logging
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from bson.objectid import ObjectId

# --- Configuration ---
MONGO_URI = os.environ.get("MONGO_URI")
if MONGO_URI:
    MONGO_URI = MONGO_URI.strip('\'"') # Strip both single and double quotes
# MONGO_URI = "[REDACTED_MONGODB_URI]"

MODEL_PATH = './models/all-MiniLM-L6-v2'

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Story Data ---
# We're crafting full-length story segments now. Each 'text' should be about 1-2 minutes long.
story_data = {
    "intro": {
        "_id": "intro",
        "title": "The Journey Begins",
        "text": "You awaken to the gentle hum of the Congo rainforest. Your name is Koko, and a message crackles over your small, solar-powered radio. It's a plea from a nearby village – their children are lost, and a mysterious sickness is spreading. The transmission mentioned a hidden river, the 'River of Life,' said to hold the cure. With your radio as your only guide, you step out of your hut. The air is thick with the scent of damp earth and flowers. Before you, the path splits. To your left, you see fresh animal tracks leading into the dense jungle. Straight ahead, a steep hill rises, promising a view of the surrounding area. To your right, a rickety rope bridge sways over a wide chasm. The choice is yours.",
        "choices": [
            {"text": "Follow the animal tracks", "next_segment_id": "follow_tracks"},
            {"text": "Climb the hill for a better view", "next_segment_id": "climb_hill"},
            {"text": "Bravely cross the rickety bridge", "next_segment_id": "cross_bridge"}
        ],
        "audio_url": None
    },
    "follow_tracks": {
        "_id": "follow_tracks",
        "title": "Into the Jungle",
        "text": "You decide to trust the wisdom of the forest creatures. The tracks are small, like those of a forest antelope. You follow them deeper into the jungle, pushing aside giant ferns and ducking under hanging vines. The canopy above is so thick that the sunlight only dapples the forest floor. Strange bird calls echo around you, and you hear the chatter of monkeys high in the trees. After walking for what feels like an hour, the tracks lead you to a clearing. In the center of the clearing is a massive, ancient baobab tree, its branches reaching towards the sky like gnarled arms. A series of intricate carvings cover its trunk, depicting stories of the forest. At the base of the tree, you see a small, leather-bound journal, half-buried in the leaves. It looks very old. Do you open the ancient journal or continue following the tracks, which seem to lead past the tree and deeper into the shadows?",
        "choices": [
            {"text": "Open the ancient journal", "next_segment_id": "open_journal"},
            {"text": "Keep following the tracks", "next_segment_id": "continue_tracks"}
        ],
        "audio_url": None
    },
    "climb_hill": {
        "_id": "climb_hill",
        "title": "The View from Above",
        "text": "You choose the high ground, hoping for a better sense of direction. The climb is steep and challenging. You scramble over rocks and pull yourself up using sturdy roots. The air grows thinner and cooler as you ascend. Finally, you reach the summit, breathless but rewarded with a spectacular view. The entire valley stretches out before you, a sea of green under a vast blue sky. In the distance, you see a plume of smoke rising – a sign of a settlement, perhaps the lost village! But as you watch, you notice something else. A glint of sunlight reflecting off something metallic, hidden within a cluster of rocks not far from your position. It could be a clue, or it could be nothing. Do you investigate the glint of metal, or do you head straight for the smoke plume in the distance?",
        "choices": [
            {"text": "Investigate the metallic glint", "next_segment_id": "investigate_glint"},
            {"text": "Head towards the smoke plume", "next_segment_id": "head_for_smoke"}
        ],
        "audio_url": None
    },
    "cross_bridge": {
        "_id": "cross_bridge",
        "title": "The Chasm of Courage",
        "text": "You take a deep breath and step onto the rope bridge. It sways wildly with each step, the wooden planks creaking under your feet. Below you, a deep chasm disappears into the mist. You focus on the other side, moving slowly and deliberately, your knuckles white as you grip the ropes. Halfway across, you hear a screech from above. A large, territorial eagle is circling, unhappy with your presence. It dives towards you, its talons outstretched. You have to think fast. Do you try to scare it away by yelling and waving your arms, or do you make a dash for the other side before it can reach you?",
        "choices": [
            {"text": "Scare the eagle", "next_segment_id": "scare_eagle"},
            {"text": "Dash for the other side", "next_segment_id": "dash_across"}
        ],
        "audio_url": None
    },
    "open_journal": {
        "_id": "open_journal",
        "title": "Secrets of the Baobab",
        "text": "You kneel beside the ancient baobab and gently brush the leaves from the journal. Its cover is cracked, the pages yellowed with age. As you open it, a wave of history washes over you—the journal belonged to a healer from the village, who wrote of a hidden spring deep in the jungle, guarded by a spirit called Mokele. The entries warn of dangers: quicksand, venomous snakes, and a riddle that must be answered to pass. Suddenly, you hear a rustle behind you. Do you hide and observe, or call out to whoever is there?",
        "choices": [
            {"text": "Hide and observe", "next_segment_id": "hide_observe"},
            {"text": "Call out bravely", "next_segment_id": "call_out"}
        ],
        "audio_url": None
    },
    "continue_tracks": {
        "_id": "continue_tracks",
        "title": "Deeper Shadows",
        "text": "You decide to trust your instincts and continue following the tracks. The jungle grows darker and the air thickens. You hear distant drumming—perhaps a village ceremony, or a warning? Suddenly, the tracks split: one set leads toward a thicket of bamboo, the other toward a muddy riverbank. Do you investigate the bamboo thicket or approach the riverbank?",
        "choices": [
            {"text": "Investigate the bamboo thicket", "next_segment_id": "bamboo_thicket"},
            {"text": "Approach the riverbank", "next_segment_id": "riverbank"}
        ],
        "audio_url": None
    },
    "investigate_glint": {
        "_id": "investigate_glint",
        "title": "The Shining Clue",
        "text": "Curiosity gets the better of you. You carefully make your way to the cluster of rocks and discover a small, metal compass—its needle spinning wildly. Next to it, a faded photograph of a smiling family. On the back, a message: 'Trust the river when the path is unclear.' As you ponder its meaning, you hear footsteps behind you. Do you hide and watch, or confront whoever is coming?",
        "choices": [
            {"text": "Hide and watch", "next_segment_id": "hide_watch"},
            {"text": "Confront the stranger", "next_segment_id": "confront_stranger"}
        ],
        "audio_url": None
    },
    "head_for_smoke": {
        "_id": "head_for_smoke",
        "title": "The Village Revealed",
        "text": "You decide the smoke is your best lead. Descending the hill, you move quickly but carefully, avoiding loose rocks. As you approach, you hear voices and laughter—the village is alive! But the mood is tense; people are gathered around a sick child. The village elder greets you, asking if you have come to help. Do you offer to help the child, or ask about the River of Life first?",
        "choices": [
            {"text": "Help the child immediately", "next_segment_id": "help_child"},
            {"text": "Ask about the River of Life", "next_segment_id": "ask_river"}
        ],
        "audio_url": None
    },
    "scare_eagle": {
        "_id": "scare_eagle",
        "title": "The Eagle's Test",
        "text": "You wave your arms and shout, trying to scare the eagle away. The bird screeches and swoops closer, but at the last moment, it veers off, dropping a shiny object onto the bridge. It's a carved wooden amulet, warm to the touch. As you pick it up, you feel a surge of courage. But the bridge is swaying dangerously. Do you hurry across, or stop to examine the amulet?",
        "choices": [
            {"text": "Hurry across the bridge", "next_segment_id": "hurry_across"},
            {"text": "Examine the amulet", "next_segment_id": "examine_amulet"}
        ],
        "audio_url": None
    },
    "dash_across": {
        "_id": "dash_across",
        "title": "Leap of Faith",
        "text": "You sprint across the bridge, heart pounding. The eagle screeches above, but you make it to the other side just as the last plank snaps behind you. Safe, but shaken, you find yourself at a fork: one path leads into a dark cave, the other toward a sunlit clearing. Do you enter the cave or head for the clearing?",
        "choices": [
            {"text": "Enter the cave", "next_segment_id": "enter_cave"},
            {"text": "Head for the clearing", "next_segment_id": "sunlit_clearing"}
        ],
        "audio_url": None
    }
}

def seed_database():
    """Connects to MongoDB, clears the existing collection, and inserts the new story data."""
    if not MONGO_URI:
        logging.error("MONGO_URI is not set. Aborting database seed.")
        return

    try:
        logging.info("Connecting to MongoDB...")
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
        client.admin.command('ismaster') # Check connection
        db = client.get_database("RadioQuest")
        collection = db.story_segments
        logging.info("Successfully connected to MongoDB.")

        logging.info("Loading sentence-transformer model for embeddings...")
        model = SentenceTransformer(MODEL_PATH)
        logging.info("Model loaded.")

        logging.info(f"Clearing the '{collection.name}' collection...")
        collection.delete_many({})
        logging.info("Collection cleared.")

        logging.info("Inserting new story segments and generating embeddings...")
        for segment_id, segment_data in story_data.items():
            text_to_embed = f"{segment_data['title']} {segment_data['text']}"
            embedding = model.encode(text_to_embed).tolist()
            segment_data['story_embedding'] = embedding
            collection.insert_one(segment_data)
            logging.info(f"Inserted segment: '{segment_id}'")

        logging.info("Database seeding completed successfully!")

    except Exception as e:
        logging.error(f"An error occurred during database seeding: {e}")

if __name__ == "__main__":
    seed_database()
