# scores.py
import json
import os

SCORES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "scores.json")
TOP_N = 5                         # the leaderboard shows the top 5 players


def _read():
    # raw file content: {"Easy": [{"name": "...", "hits": 5}, ...], ...}
    try:
        with open(SCORES_FILE) as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    return {}


def _entries(value):
    # an older scores.json held one record per level: {"name": ..., "hits": ...}
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list):
        return []
    clean = [e for e in value
             if isinstance(e, dict) and isinstance(e.get("hits"), int)]
    return sorted(clean, key=lambda e: -e["hits"])      # best first


def load_leaderboard(level):
    # top 5 players of a level, best first: [{"name": ..., "hits": ...}, ...]
    return _entries(_read().get(level))[:TOP_N]


def load_scores():
    # best record of each level: {"Easy": {"name": "...", "hits": 5}, ...}
    # (the level cards and the results screen use this)
    best = {}
    for level, value in _read().items():
        entries = _entries(value)
        if entries:
            best[level] = entries[0]
    return best


def save_score(level, name, hits):
    # keeps each player's best score per level (top 5 only);
    # returns True when the score is a new record for the level
    if hits <= 0:
        return False
    data = _read()
    entries = _entries(data.get(level))
    old_best = entries[0]["hits"] if entries else 0

    # one line per player: a player's second score replaces the first
    # only if it is higher
    kept = []
    for e in entries:
        if str(e.get("name", "")).lower() == name.lower():
            hits_to_keep = max(hits, e["hits"])
            name, hits = e.get("name", name), hits_to_keep
        else:
            kept.append(e)
    kept.append({"name": name, "hits": hits})
    kept.sort(key=lambda e: -e["hits"])         # stable: earlier score wins a tie
    data[level] = kept[:TOP_N]

    try:
        with open(SCORES_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass                      # a failed save must never crash the game
    return hits > old_best