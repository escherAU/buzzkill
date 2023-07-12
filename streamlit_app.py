import streamlit as st
from collections import defaultdict
import pandas as pd
import nltk
from nltk.corpus import words

# Download the English words corpus
nltk.download("words")
word_list = set(word.upper() for word in words.words())  # make all words uppercase

def get_anagrams(common_pool, all_words):
    common_pool_set = set(common_pool)  # calculate once to improve efficiency
    matching_anagrams = []

    for word in all_words:
        if len(word) >= 4 and set(word).issubset(common_pool_set):
            matching_anagrams.append((word, set(word) == common_pool_set))

    return matching_anagrams

def filter_by_letter(anagrams, letter):
    return [(word, is_pangram) for word, is_pangram in anagrams if letter in word]

def filter_by_valid_words(anagrams, word_list):
    return [(word, is_pangram) for word, is_pangram in anagrams if word in word_list]

def main():
    input_style = """
    <style>
    input[type="text"] {
        border: 2px solid black;
        text-transform: uppercase;
    }
    </style>
    """
    st.markdown(input_style, unsafe_allow_html=True)

# Set page title and color
    title_html = """
        <div style="background-color: #F7DA21; padding: 10px;">
            <h1 style="color: black; text-align: center;">BuzzKill</h1>
        </div>
    """
    st.markdown(title_html, unsafe_allow_html=True)

    # Set the subtitle and center it
    subtitle = "<div style='text-align: center; color: black; padding: 10px; background-color: lightgrey; font-weight: bold;'>A helpful companion for solving the New York Times 'Spelling Bee' puzzle.</div>"
    st.markdown(subtitle, unsafe_allow_html=True)

    common_pool = st.text_input("Enter today's letters (7 letters):", key="common_pool").upper().replace(" ", "")

    if all(c.isalpha() for c in common_pool) and len(common_pool) == 7:
        all_words = set(
            word.upper()
            for word in pd.read_csv(
                "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt",
                header=None,
                skip_blank_lines=True,
                na_filter=False,
                dtype=str,
            ).values.flatten()
        )

        matching_anagrams = get_anagrams(common_pool, all_words)
        letter = st.text_input("Enter the center letter to filter the list:", key="filter_letter").upper()
        if letter:
            matching_anagrams = filter_by_letter(matching_anagrams, letter)

        matching_anagrams = filter_by_valid_words(matching_anagrams, word_list)

        # ... keep the rest of the main function code ...

if __name__ == "__main__":
    main()
