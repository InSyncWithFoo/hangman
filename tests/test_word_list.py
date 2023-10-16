import pytest

from hangman._static_reader import word_list_directory
from hangman.word_list import Level, WordList


LEVELS = Level.__members__.values()


@pytest.fixture(scope = 'module')
def word_list(request) -> WordList:
	return request.getfixturevalue(request.param.lower())


@pytest.fixture(scope = 'module')
def easy():
	word_list = WordList(word_list_directory / 'easy.txt')
	
	yield word_list


@pytest.fixture(scope = 'module')
def medium():
	word_list = WordList.from_level(Level.MEDIUM)
	
	yield word_list


@pytest.fixture(scope = 'module')
def hard():
	word_list = WordList.from_level('hard')
	
	yield word_list


@pytest.fixture(scope = 'module')
def unix():
	word_list = WordList.from_level('uNiX')
	
	yield word_list


@pytest.mark.parametrize('word_list', LEVELS, indirect = True)
def test_word_list_construction(word_list):
	assert isinstance(word_list, WordList)
	assert isinstance(word_list._list, list)


@pytest.mark.parametrize('words', [
	['foobar', 'bazqux', 'lorem', 'ipsum']
])
def test_word_list_construction_from_list(words):
	word_list = WordList.from_list(words)
	
	assert isinstance(word_list, WordList)
	assert isinstance(word_list._list, list)


@pytest.mark.parametrize('word_list, other_word_list', [
	('easy', WordList.from_level(Level.EASY)),
	('medium', WordList(str(word_list_directory / 'medium.txt'))),
	('hard', WordList.from_level('HarD'))
], indirect = ['word_list'])
def test_word_list_caching(word_list, other_word_list):
	assert word_list is other_word_list


@pytest.mark.parametrize('word_list', LEVELS, indirect = True)
def test_get_random_word(word_list):
	word = word_list.get_random_word()
	
	assert isinstance(word, str)
	assert len(word) >= 5
	assert all('a' <= character <= 'z' for character in word)
