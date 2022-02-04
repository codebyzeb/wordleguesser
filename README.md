# Wordle Guesser
A little python script for finding the best word choice in a Wordle game, by assuming that at each step you want to minimise the average number of possible answers left after guessing that word (note this is a greedy assumption and not fully correct, but as a TikTok user pointed out, this is the best you can do before it gets NP-hard).

## Install Dependencies

The Wordle Guesser requires a few additional code libraries that don't come pre-installed with python. To run the program you will first need to run the following command:

```bash
pip install -r requirements.txt #Install dependencies
```

## Finding the best first word

To find the best first word, run the following in python:
```python
import wordle
guesser = wordle.WordleGuesser(full_vocab=False, only_guess_from_answers=False)
best_word, min_length = guesser.get_smart_guess(outfile="best_words.txt", verbose=True)
print("Best word: {}, gives {} possible answers left".format(best_word, min_length))
```

`full_vocab=False` means we evaluate against the possible answers and `only_guess_from_answers=False` means we guess from all the possible guesses, not just the possible answers. The example above saves all the words in a file called `best_words.txt`.

## Finding the best next word

After getting a response from your guess in wordle, you can update your guesser as follows:
```python
import wordle
guesser = wordle.WordleGuesser(full_vocab=False, only_guess_from_answers=False)
# If the game responded with Orange, Black, Orange, Black, Green
guesser.update("roate", "obobg")
```

You can then either print out the possible answers left, or find the next best word to guess:
```python
print(guesser.possible_answers)
best_word, _ = guesser.get_smart_guess()
```

