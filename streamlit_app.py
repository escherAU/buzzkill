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
    # Create a list to store the anagrams that can be made using the common pool
    matching_anagrams = []

    # Get all the anagrams that can be made using the letters in the common pool
    for l in range(4, 21):
        for word in all_words:
            if len(word) == l and set(word.upper()) <= set(common_pool.upper()):
                matching_anagrams.append(word.upper())

    # Return the list of matching anagrams
    return matching_anagrams


# Function to filter out words not containing the specified letter
def filter_by_letter(anagrams, letter):
    return [word for word in anagrams if letter.upper() in word]


# Function to filter out words that are not valid English words
def filter_by_valid_words(anagrams, word_list):
    return [word for word in anagrams if word in word_list]


# Main function to run the tool
def main():
    # Set page title and color
    title_html = """
        <div style="background-color: #F7DA21; padding: 10px;">
            <h1 style="color: black; text-align: center;">BuzzKill</h1>
        </div>
    """
    st.markdown(title_html, unsafe_allow_html=True)

    # Set the subtitle and center it
    subtitle = "<div style='text-align: center; color: #F7DA21; padding: 10px;'>A companion to help solve the New York Times 'Spelling Bee' puzzle.</div>"
    st.markdown(subtitle, unsafe_allow_html=True)

    common_pool = st.text_input("Enter today's letters (7 letters):", key="common_pool")

    common_pool = common_pool.replace(
        " ", ""
    ).upper()  # remove spaces and convert to uppercase

    if all(c.isalpha() for c in common_pool) and len(common_pool) == 7:
        # Get a set of all English words
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

        # Call the get_anagrams function to get the matching anagrams
        matching_anagrams = get_anagrams(common_pool, all_words)

        # Ask the user to enter a letter to filter the anagrams
        letter = st.text_input("Enter the center letter to filter the list:", key="filter_letter")
        if letter:
            # Filter the anagrams by the specified letter
            matching_anagrams = filter_by_letter(matching_anagrams, letter)

        # Filter the anagrams by valid English words
        matching_anagrams = filter_by_valid_words(matching_anagrams, all_words)

        # Create a dictionary to group the anagrams by starting letter
        anagrams_by_letter = defaultdict(list)
        for anagram in matching_anagrams:
            anagrams_by_letter[anagram[0]].append(anagram)

        # Sort the dictionary by key (starting letter)
        sorted_anagrams = sorted(anagrams_by_letter.items())

        # Print the matching anagrams, grouped by starting letter
        st.write("Matching words:")
        for letter, anagrams in sorted_anagrams:
            # Add a line break before the anagrams
            st.write(f"\n<h2 style='font-size:24px'>{letter.upper()}:</h2>", unsafe_allow_html=True)
            # Wrap the anagrams so that they don't fall within the scrollbars
            with st.container():
                st.write(", ".join(anagrams))


if __name__ == "__main__":
    main()