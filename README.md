# Hangman

![Tests][B1]

This Python package exposes a simple CLI hangman game.
There are four levels in total: Easy (22.5k words),
Medium (74.5k words), Hard (168k words), and Unix
(205k words).

[The word lists][1] are taken from *[dolph/dictionary][2]*,
which, unfortunately, has no license.
[According to Wikipedia][3], the Unix dictionary is sourced
from [Moby Project][4], a public domain compilation of words.
[An answer][5] on *Unix & Linux Stack Exchange* claims that
this list varies by each Unix.
It is assumed that the rest of the lists do not exceed the
threshold of originality and therefore not copyrightable.


## Installation

This package only supports Python 3.12 and later. [PEP 695][6]
features are not yet used due to *mypy* and PyCharm's limited
support. Any other compatibility with earlier versions are
purely incidental.

To play the game, install it with _pip_ using either of the following:

```shell
$ git clone https://github.com/InSyncWithFoo/hangman.git
$ pip install -e .
```

```shell
$ pip install "git+https://github.com/InSyncWithFoo/hangman.git"
```

...then run the pre-built game script called `hangman`:

```shell
$ hangman
```


  [B1]: https://github.com/InSyncWithFoo/hangman/actions/workflows/tests.yaml/badge.svg

  [1]: ./src/hangman/words
  [2]: https://github.com/dolph/dictionary
  [3]: https://en.wikipedia.org/wiki/Words_(Unix)
  [4]: https://en.wikipedia.org/wiki/Moby_Project
  [5]: https://unix.stackexchange.com/a/253498
  [6]: https://peps.python.org/pep-0695
