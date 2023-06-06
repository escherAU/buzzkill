import streamlit as st
from collections import defaultdict
import itertools
import pandas as pd
import nltk
from nltk.corpus import words

# Download the English words corpus
nltk.download("words")
word_list = set(words.words())

def get_anagrams(common_pool, all_words):
    matching_anagrams = []

    for word in all_words:
        if len(word) >= 4 and set(word.upper()).issubset(set(common_pool.upper())):
            # The word is a pangram if it contains all letters in the common pool
            is_pangram = set(word.upper()) == set(common_pool.upper())
            matching_anagrams.append((word.upper(), is_pangram))

    return matching_anagrams

# Function to filter out words not containing the specified letter
def filter_by_letter(anagrams, letter):
    return [(word, is_pangram) for word, is_pangram in anagrams if letter.upper() in word]

# Function to filter out words that are not valid English words
def filter_by_valid_words(anagrams, word_list):
    return [(word, is_pangram) for word, is_pangram in anagrams if word in word_list]

# Main function to run the tool
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

    common_pool = st.text_input("Enter today's letters (7 letters):", key="common_pool")
    common_pool = common_pool.upper()

    common_pool = common_pool.replace(" ", "")

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

        letter = st.text_input("Enter the center letter to filter the list:", key="filter_letter")
        letter = letter.upper()
        if letter:
            matching_anagrams = filter_by_letter(matching_anagrams, letter)

        matching_anagrams = filter_by_valid_words(matching_anagrams, all_words)

        anagrams_by_letter = defaultdict(lambda: ([], 0))
        for anagram, is_pangram in matching_anagrams:
            key = anagram[0]
            anagrams, count = anagrams_by_letter[key]
            anagrams.append((anagram, is_pangram))
            anagrams_by_letter[key] = (anagrams, count + 1)

        sorted_anagrams = sorted(anagrams_by_letter.items())

        st.write("Matching words:")
        for letter, (anagrams, count) in sorted_anagrams:
            st.write(f"\n<h2 style='font-size:24px'>{letter.upper()} ({count}):</h2>", unsafe_allow_html=True)
            with st.container():
                anagrams.sort(key=lambda x: x[0])
                anagrams_to_write = []
                for word, is_pangram in anagrams:
                    if is_pangram:
                        anagrams_to_write.append(f"<span style='font-color: yellow; font-weight: bold;'>{word}</span>")
                    else:
                        anagrams_to_write.append(word)
                st.write(", ".join(anagrams_to_write), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
