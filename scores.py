# scores.py
import json
import os

SCORES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "scores.json")


def load_scores():
    # returns {"Easy": {"name": "...", "hits": 5}, ...}, or {} if none yet
    try:
        with open(SCORES_FILE) as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    return {}


def save_score(level, name, hits):
    # keeps only the best score per level; returns True for a new record
    if hits <= 0:
        return False
    scores = load_scores()
    best = scores.get(level)
    if best is not None and hits <= best.get("hits", 0):
        return False
    scores[level] = {"name": name, "hits": hits}
    try:
        with open(SCORES_FILE, "w") as f:
            json.dump(scores, f, indent=2)
    except OSError:
        pass                      # a failed save must never crash the game
    return True