from flask import Flask, render_template, request, jsonify
from collections import defaultdict
from pathlib import Path
import pandas as pd
import os
# --- Curated word list (SB master) ---
from pathlib import Path

SB_MASTER_TXT = Path("data/wordlists/sb_master.txt")

def load_txt_local(path: Path):
    if not path.exists():
        print(f"[buzzkill] Warning: curated list not found at {path}")
        return []
    return [ln.strip().lower() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]

CURATED_WORDS = load_txt_local(SB_MASTER_TXT)
print(f"[buzzkill] Curated SB list loaded: {len(CURATED_WORDS)} words")

# --- Big (fallback) word list loader ---
WORDS_BIG_URL = "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"

def load_txt_remote(url: str):
    import requests
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return [ln.strip().lower() for ln in r.text.splitlines() if ln.strip()]

try:
    ALL_WORDS = load_txt_remote(WORDS_BIG_URL)
    print(f"[buzzkill] Big list loaded: {len(ALL_WORDS)} words")
except Exception as e:
    print(f"[buzzkill] Big list failed to load: {e}")
    ALL_WORDS = []

def get_candidate_words(use_curated: bool) -> list[str]:
    """
    If 'Likely words' toggle is on and curated list is available, use it.
    Otherwise fall back to the big english list.
    """
    if use_curated and CURATED_WORDS:
        return CURATED_WORDS
    return ALL_WORDS

app = Flask(__name__)

# Fetch the external word list once and store it
external_word_data = pd.read_csv(
    "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt",
    header=None,
    skip_blank_lines=True,
    na_filter=False,
    dtype=str
)
all_words = set(word.upper() for word in external_word_data.values.flatten())


def get_anagrams(common_pool):
    matching_anagrams = []

    for word in all_words:
        if len(word) >= 4 and set(word).issubset(set(common_pool)):
            is_pangram = set(word) == set(common_pool)
            matching_anagrams.append((word, is_pangram))

    return matching_anagrams


def filter_by_letter(anagrams, letter):
    return [(word, is_pangram) for word, is_pangram in anagrams if letter in word]


def filter_by_valid_words(anagrams):
    word_length_groups = defaultdict(list)
    for word, is_pangram in anagrams:
        if word in all_words:
            word_length_groups[len(word)].append((word, is_pangram))

    return word_length_groups

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')
    
@app.route('/process_input', methods=['POST'])
def process_input():
    data = request.get_json(silent=True) or {}

    # Inputs (accept either case; normalise to lower for logic)
    common_pool_raw = (data.get('common_pool') or "").strip()
    filter_letter_raw = (data.get('filter_letter') or "").strip()
    use_curated = bool(data.get('use_curated'))

    # Guard: need a 7-letter pool and a center letter
    if not common_pool_raw or not filter_letter_raw:
        return jsonify({'status': 'error', 'message': 'Provide common_pool (7 letters) and filter_letter.'}), 400

    common_pool = common_pool_raw.lower()
    filter_letter = filter_letter_raw.lower()

    # Choose candidate dictionary
    try:
        candidate_words = get_candidate_words(use_curated)  # uses CURATED_WORDS vs ALL_WORDS
    except NameError:
        # Fallback if helper isn't present
        candidate_words = CURATED_WORDS if use_curated and 'CURATED_WORDS' in globals() and CURATED_WORDS else \
                          (ALL_WORDS if 'ALL_WORDS' in globals() else [])

    # Core validators
    pool_set = set(common_pool)
    def valid_word(w: str) -> bool:
        w = w.lower()
        if len(w) < 4:
            return False
        if filter_letter not in w:
            return False
        # every char must be from the 7-letter pool
        return all((ch in pool_set) for ch in w)

    def is_pangram(w: str) -> bool:
        # pangram if it uses all distinct letters from the pool at least once
        return pool_set.issubset(set(w.lower()))

    # Filter candidate list
    matches = [w for w in candidate_words if valid_word(w)]

    # Group into your original structure
    result = {}
    word_counts = {}
    for w in matches:
        w_up = w.upper()
        wl = len(w_up)
        pang = is_pangram(w_up)

        first_letter = w_up[0]
        if first_letter not in result:
            result[first_letter] = {}
            word_counts[first_letter] = 0
        if wl not in result[first_letter]:
            result[first_letter][wl] = []
        result[first_letter][wl].append([w_up, pang])
        word_counts[first_letter] += 1

    if result:
        return jsonify({'status': 'success', 'result': result, 'counts': word_counts})
    else:
        return jsonify({'status': 'error', 'message': 'No matching words found.'})


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)