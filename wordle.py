from cmath import exp
import random, copy
from itertools import combinations_with_replacement, permutations
from more_itertools import only
from tqdm import tqdm

LETTERS = "abcdefghijklmnopqrstuvwxyz"

def get_all_words(filename):
    words = []
    with open(filename) as f:
        for line in f.readlines():
            words.append(line.strip())
    return words

def get_all_letters_without_one(letter):
    if letter == "a":
        return LETTERS[1:]
    if letter == "z":
        return LETTERS[:-1]
    letter_pos = ord(letter)-97
    return LETTERS[:letter_pos] + LETTERS[letter_pos+1:]

def get_response(true_word, guess):
    response = []
    for i in range(5):
        if guess[i] == true_word[i]:
            response += "g"
        elif not guess[i] in true_word:
            response += "b"
        else:
            response += "o"

    # fix repeated letters 
    for letter in set(guess):
        if guess.count(letter) > 1:
            green_positions = [i for i, l, r in zip(range(5), guess, response) if l == letter and r == "g"]
            orange_positions = [i for i, l, r in zip(range(5), guess, response) if l == letter and r == "o"]
            # greens + oranges should not exceed number of letters in word
            to_remove = len(orange_positions) + len(green_positions) - true_word.count(letter)
            random.shuffle(orange_positions)
            for i in range(to_remove):
                response[orange_positions[i]] = "b"
            
    return "".join(response)       

def word_is_possible(word, guesser_state):
    for letter in guesser_state.must_contain:
        if not letter in word:
            return False
    for letter in guesser_state.must_contain_exactly_1:
        if word.count(letter) != 1:
            return False
    for letter in guesser_state.must_contain_at_least_2:
        if word.count(letter) < 2:
            return False
    for i in range(5):
        if word[i] in guesser_state.banned_letters[i]:
            return False
    return True

def get_possible_words(old_words, guesser_state):
    new_words = []
    for word in old_words:
        if word_is_possible(word, guesser_state):
            new_words.append(word)
    return new_words

class GuesserState():
    def __init__(self):
        self.banned_letters = ["","","","",""]
        self.must_contain = ""
        self.must_contain_at_least_2 = ""
        self.must_contain_exactly_1 = ""

    def update_state(self, guess, response):
        for i in range(5):
            letter = guess[i]

            # if letter is black then it isn't in any words
            if response[i] == "b":
                for j in range(5):
                    if j != i and guess[i] == guess[j] and response[j] != "b": # if double letters and other occurrence is not black
                        if not letter in self.banned_letters[i]:
                            self.banned_letters[i] += letter
                        break
                else:
                    for j in range(5):
                        if not letter in self.banned_letters[j]:
                            self.banned_letters[j] += letter

            # if letter is orange, then it isn't in that spot but must be elsewhere
            if response[i] == "o":
                if not letter in self.banned_letters[i]:
                    self.banned_letters[i] += letter
                if not letter in self.must_contain:
                    self.must_contain += letter
            
            # if letter is green, then it must be in that spot
            if response[i] == "g":
                self.banned_letters[i] = get_all_letters_without_one(letter)

        # handle double letters
        for letter in set(guess):
            if guess.count(letter) > 1:
                responses = [r for l, r in zip(guess, response) if l == letter]
                if len(responses) - responses.count("b") == 1:
                    self.must_contain_exactly_1 += letter
                elif len(responses) - responses.count("b") >= 2:
                    self.must_contain_at_least_2 += letter

def get_expected_length_after_guess(guess, guesser_state, possible_answers, guess_word_first=False):
    total_words = len(possible_answers)
    expected_length = 0

    # Get counts of all possible responses for this guess by looping over possible true words
    responses = {}
    for word in possible_answers:
        response = get_response(word, guess_word_first if guess_word_first else guess)
        if response in responses:
            responses[response] += 1
        else:
            responses[response] = 1

    # Calculate expected length of resulting word list for this guess by looping over possible responses
    for response in responses:
        next_guesser_state = copy.deepcopy(guesser_state)
        if guess_word_first:
            next_guesser_state.update_state(guess_word_first, response)
            probability_of_response = get_expected_length_after_guess(guess, next_guesser_state, get_possible_words(possible_answers, next_guesser_state))
            expected_length += probability_of_response * responses[response] / total_words
        else:
            next_guesser_state.update_state(guess, response)
            num_matches = len(get_possible_words(possible_answers, next_guesser_state))
            probability_of_response = responses[response] / total_words
            expected_length += probability_of_response * num_matches
    return expected_length

class WordleGuesser():
    def __init__(self, full_vocab=True, only_guess_from_answers=False):
        self.guesser_state = GuesserState()
        self.possible_guesses = get_all_words("guess_words.txt")
        self.possible_answers = get_all_words("guess_words.txt") if full_vocab else get_all_words("answer_words.txt")
        self.only_guess_from_answers = only_guess_from_answers

    def update(self, guess, response):
        self.guesser_state.update_state(guess, response)
        self.possible_answers = get_possible_words(self.possible_answers, self.guesser_state)

    def get_smart_guess(self, outfile = None, verbose=False, first_guess=False):
        """  select the guess that minimises the length of the new possible words list """
        total_words = len(self.possible_answers) if self.only_guess_from_answers else len(self.possible_guesses)
        expected_lengths = {}

        if verbose:
            for i in tqdm (range (total_words), desc="Processing Words..."):
                word = self.possible_answers[i] if self.only_guess_from_answers else self.possible_guesses[i]
                expected_length = get_expected_length_after_guess(word, self.guesser_state, self.possible_answers, guess_word_first=first_guess)
                expected_lengths[word] = expected_length
        else:
            for i in range(total_words):
                word = self.possible_answers[i] if self.only_guess_from_answers else self.possible_guesses[i]
                expected_length = get_expected_length_after_guess(word, self.guesser_state, self.possible_answers, guess_word_first=first_guess)
                expected_lengths[word] = expected_length

        best_guesses = dict(sorted(expected_lengths.items(),key= lambda x:x[1]))
        if outfile:
            with open(outfile,'w') as f:
                for key in best_guesses:
                    f.write(key + ": " + str(best_guesses[key]) + "\n")
        min_length = min(best_guesses.values())
        return [key for key in best_guesses if best_guesses[key] == min_length][0], min_length

def test_guesser(first_word = "raise", use_full_vocab=False, only_guess_from_answers = True):
    """ Guesses using first_word then using the next best word according to the guesser settings.
    After two guesses, switches to only guess from the correct answers """
    possible_answers = get_all_words("answer_words.txt")
    guesses = {}
    for i in tqdm(range(len(possible_answers)), desc="Processing Words..."):
        true_word = possible_answers[i]
        guesser = WordleGuesser(use_full_vocab, only_guess_from_answers)
        response = get_response(true_word, first_word)
        guesser.update(first_word, response)
        num_guesses = 1
        while response != "ggggg":
            if num_guesses == 2:
                guesser.only_guess_from_answers = True
            if len(guesser.possible_answers) > 1:
                guess, _ = guesser.get_smart_guess()
            else:
                guess = guesser.possible_answers[0]
            response = get_response(true_word, guess)
            guesser.update(guess, response)
            num_guesses+=1
        guesses[true_word] = num_guesses
    
    average = sum(guesses.values()) / len(guesses)
    maximum = max(guesses.values())
    minimum = min(guesses.values())
    print("Average: {}, Minimum: {}, Maximum: {}".format(average, minimum, maximum))

def get_best_second_word(use_full_vocab=False, only_guess_from_answers=True):
    possible_guesses = get_all_words("guess_words.txt")
    guesser = WordleGuesser(use_full_vocab, only_guess_from_answers)
    best_guess_pair = {}
    best_s, best_f = None, None
    min_s = 1000
    for i in tqdm(range(len(possible_guesses)), desc="Processing guesses"):
        guess = possible_guesses[i]
        best_second, min_size = guesser.get_smart_guess(verbose=False, first_guess=guess)
        best_guess_pair[guess + "," + best_second] = min_size
        if min_size < min_s:
            best_s = best_second
            best_f = guess
            min_s = min_size

    print("best pair:",best_s, best_f, "with min:", min_s)
    with open("best_pairs.txt",'w') as f:
        for key in best_guess_pair:
            f.write(key + ": " + str(best_guess_pair[key]) + "\n")


def evaluate_pair(word1, word2):
    guesser = WordleGuesser(False, False)
    print(get_expected_length_after_guess(word2, guesser.guesser_state, guesser.possible_answers, guess_word_first=word1))
