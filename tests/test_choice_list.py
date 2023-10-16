import pytest

from hangman import ChoiceList, Level
from hangman.choice_list import Choice, ChoiceDescriptor, Choices


@pytest.mark.parametrize('choice_list, items', [
	(Choices.LEVEL, ['easy', 'MEDIUM', 'HaRd', 'U']),
	(Choices.CONFIRMATION, ['yeS', 'No'])
])
def test_choice_list_contains(choice_list, items):
	assert all(item in choice_list for item in items)


@pytest.mark.parametrize('choice_list, items, expected_values', [
	(Choices.LEVEL, ['e', 'MeDIUM'], ['EASY', Level.MEDIUM]),
	(Choices.CONFIRMATION, ['yEs', 'n'], ['YES', 'NO'])
])
def test_choices_list_getitem(choice_list, items, expected_values):
	for item, expected in zip(items, expected_values):
		assert choice_list[item].value == expected


@pytest.mark.parametrize('choice_list', Choices)
def test_choice_list_str(choice_list):
	stringified = str(choice_list)
	lines = stringified.splitlines()
	
	assert all(len(line) <= ChoiceList._MAX_WIDTH for line in lines)


@pytest.mark.parametrize('choice_list', Choices)
def test_choice_lists_iter(choice_list):
	for choice in choice_list:
		assert isinstance(choice, Choice)
		assert choice.shortcut.isupper()
		assert choice.value.isupper()


@pytest.mark.parametrize('arguments', [
	dict(
		FOO = ChoiceDescriptor('Foobar', {'foo'}),
		lorem = ChoiceDescriptor('Lorem ipsum', {'lorem'}, 'lipsum')
	)
])
def test_choice_list_construction(arguments):
	choice_list = ChoiceList(**arguments)
	
	for key, descriptor in arguments.items():
		assert choice_list[key] is choice_list[key.upper()]
		
		choice = choice_list[key]
		
		assert choice.shortcut == key.upper()
		assert choice.description == descriptor.description
		assert len(choice.aliases) == len(descriptor.aliases)
		assert choice.value == descriptor.value
		
		for alias in descriptor.aliases:
			assert alias.upper() in choice.aliases
