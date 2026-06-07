import os, sys, json

def resource_path(p):
    try: base = sys._MEIPASS
    except: base = os.path.abspath(".")
    return os.path.join(base, p)

# Khởi tạo đường dẫn    
BLACKLIST_FILE = resource_path("data/blacklist/blacklist.json")
ABBR_FILE  = resource_path("data/keyword/abbreviations.json")
GIFT_FILE  = resource_path("data/giftmap/gift_map.json")
EMOJI_FILE = resource_path("data/emoji/emoji_map.json")
CONFIG_FILE = resource_path("data/config/settings.json")
AUDIO_DIR  = resource_path("audio")
CACHE_DIR  = resource_path("audio/cache")

for f in [ABBR_FILE, GIFT_FILE, EMOJI_FILE, BLACKLIST_FILE, CONFIG_FILE]:
    os.makedirs(os.path.dirname(f), exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

def load_json(p):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}

def save_json(p, d):
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)