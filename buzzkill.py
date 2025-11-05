from flask import Flask, render_template, request, jsonify
from collections import defaultdict
import pandas as pd
import os

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
    data = request.json
    common_pool = data['common_pool'].upper()
    filter_letter = data['filter_letter'].upper()

    matching_anagrams = get_anagrams(common_pool)
    if filter_letter:
        matching_anagrams = filter_by_letter(matching_anagrams, filter_letter)

    word_length_groups = filter_by_valid_words(matching_anagrams)

    result = {}
    word_counts = {}
    for word_length, anagrams in sorted(word_length_groups.items()):
        for word, is_pangram in sorted(anagrams):
            first_letter = word[0].upper()
            if first_letter not in result:
                result[first_letter] = {}
                word_counts[first_letter] = 0
            if word_length not in result[first_letter]:
                result[first_letter][word_length] = []
            result[first_letter][word_length].append([word, is_pangram])
            word_counts[first_letter] += 1

    if result:
        return jsonify({'status': 'success', 'result': result, 'counts': word_counts})
    else:
        return jsonify({'status': 'error', 'message': 'No matching anagrams found.'})


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)