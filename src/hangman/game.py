from __future__ import annotations

from typing import ClassVar

from ._static_reader import get_asset
from .canvas import Canvas, Component, Layer
from .choice_list import ChoiceList, Choices
from .conversation import (
	Conversation,
	InputGetter,
	OneOrManyValidators,
	OutputDisplayer,
	Validator
)
from .word import Word
from .word_list import Level, WordList


def _response_is_ascii_letter(character: str, _: ChoiceList | None) -> bool:
	return len(character) == 1 and 'A' <= character <= 'Z'


class Game:
	
	TITLE: ClassVar[str] = get_asset('title.txt')
	INSTRUCTIONS: ClassVar[str] = get_asset('instructions.txt')
	
	COEFFICENTS: ClassVar[dict[Level, int]] = {
		Level.EASY: 1,
		Level.MEDIUM: 2,
		Level.HARD: 3,
		Level.UNIX: 4
	}
	
	_horizontal_rule: ClassVar[str] = '-' * 80
	
	__slots__ = (
		'_conversation', '_used_words', '_points',
		'_reward', '_penalty', '_ended'
	)
	
	_conversation: Conversation
	_used_words: set[str]
	_points: int
	_reward: int
	_penalty: int
	_ended: bool
	
	def __init__(
		self,
		input_getter: InputGetter = input,
		output_displayer: OutputDisplayer = print,
		reward: int = 2,
		penalty: int = -1
	) -> None:
		self._used_words = set()
		self._points = 0
		self._reward, self._penalty = reward, penalty
		
		self._ended = False
		
		self._conversation = Conversation(
			ask = input_getter,
			answer = output_displayer
		)
	
	@property
	def points(self) -> int:
		return self._points
	
	@points.setter
	def points(self, value: int) -> None:
		self._points = max(value, 0)
	
	def _start(self) -> None:
		self._output_game_title()
		self._output_game_instructions()
		
		self._start_round()
		
		while not self._ended and self._prompt_for_continue_confirmation():
			self._start_round()
		
		if not self._ended:
			self.end()
	
	def _output_game_title(self) -> None:
		self.output(self.TITLE)
	
	def _output_game_instructions(self) -> None:
		self.output(self.INSTRUCTIONS)
	
	def _prompt_for_continue_confirmation(self) -> bool:
		answer = self.input('Continue?', Choices.CONFIRMATION)
		
		return answer == 'Y'
	
	def _start_round(self) -> None:
		level = self._prompt_for_level()
		word_list = WordList.from_level(level)
		coefficient = self.COEFFICENTS[level]
		
		word = word_list.get_random_word()
		
		while word in self._used_words:
			word = word_list.get_random_word()
		
		self._used_words.add(word)
		
		game_round = self._initialize_round(word, coefficient)
		game_round.start()
	
	def _initialize_round(self, word: str, coefficient: int) -> GameRound:
		return GameRound(self, word, coefficient)
	
	def _prompt_for_level(self) -> Level:
		choices = Choices.LEVEL
		response = self._conversation.ask('Choose a level:', choices)
		
		value = choices[response].value
		assert value is not None
		
		return Level(value)
	
	def start(self) -> None:
		try:
			self._start()
		except KeyboardInterrupt:
			self.end()
	
	def end(self) -> None:
		self._ended = True
		self.output(
			f'\n{self._horizontal_rule}' +
			f'\nGame over. Total points: {self._points}'
		)
	
	def input(
		self,
		prompt: str,
		choices: ChoiceList | None = None,
		validators: OneOrManyValidators | None = None
	) -> str:
		return self._conversation.ask(prompt, choices, until = validators)
	
	def output(self, answer: str) -> None:
		return self._conversation.answer(answer)
	
	def output_current_points(self) -> None:
		self.output(f'Points: {self._points}')
	
	def reward_correct_guess(self, count: int, coefficient: int) -> None:
		self.points += self._reward * count * coefficient
	
	def penalize_incorrect_guess(self, coefficient: int) -> None:
		self.points += self._penalty * coefficient


class GameRound:
	
	_INVALID_GUESS: ClassVar[str] = \
		'Invalid guess. Please input a letter.'
	_ALREADY_GUESSED: ClassVar[str] = \
		'You have already guessed this letter. Please try again.'
	
	__slots__ = (
		'_game', '_canvas', '_layer_stack',
		'_word', '_coefficient', '_guesses'
	)
	
	_game: Game
	_canvas: Canvas
	_layer_stack: list[Layer]
	_word: Word
	_coefficient: int
	_guesses: set[str]
	
	def __init__(self, game: Game, word: str, coefficient: int) -> None:
		self._game = game
		self._canvas = Canvas.from_layer(Component.GALLOWS)
		self._layer_stack = [
			Component.HEAD,
			Component.TRUNK,
			Component.LEFT_ARM,
			Component.RIGHT_ARM,
			Component.LEFT_LEG,
			Component.RIGHT_LEG
		]
		self._word = Word(word)
		self._coefficient = coefficient
		self._guesses = set()
	
	@property
	def lives_left(self) -> int:
		return len(self._layer_stack)
	
	def _output_canvas(self) -> None:
		self._game.output(str(self._canvas))
	
	def _output_current_word_state(self) -> None:
		self._game.output(f'Word: {self._word.current_state}')
	
	def _output_word(self) -> None:
		self._game.output(f'The word was "{self._word}".')
	
	def _start_turn(self) -> None:
		self._output_canvas()
		self._output_current_word_state()
		
		guess = self._prompt_for_guess()
		count = self._word.count(guess)
		
		self._guesses.add(guess)
		
		if count == 0:
			self._handle_incorrect_guess()
		else:
			self._handle_correct_guess(guess, count)
	
	def _handle_incorrect_guess(self) -> None:
		self._game.output('Incorrect guess.')
		self._game.penalize_incorrect_guess(self._coefficient)
		self._game.output_current_points()
		
		self._minus_1_life()
		
		if self.lives_left == 0:
			self._canvas.add_layers(Component.YOU_LOST)
	
	def _handle_correct_guess(self, guess: str, count: int) -> None:
		if count == 1:
			self._game.output(f'There is {count} "{guess}"!')
		else:
			self._game.output(f'There are {count} "{guess}"s!')
		
		self._game.reward_correct_guess(count, self._coefficient)
		self._game.output_current_points()
	
	def _prompt_for_guess(self) -> str:
		validators = [
			Validator(_response_is_ascii_letter, self._INVALID_GUESS),
			Validator(self._not_previously_guessed, self._ALREADY_GUESSED)
		]
		
		return self._game.input('Your guess:', validators = validators)
	
	def _not_previously_guessed(
		self,
		response: str,
		_choices: ChoiceList | None
	) -> bool:
		return response not in self._guesses
	
	def _minus_1_life(self) -> None:
		self._canvas.add_layers(self._layer_stack.pop(0))
	
	def _print_canvas(self) -> None:
		self._game.output(str(self._canvas))
	
	def start(self) -> None:
		while not self._word.all_clear and self.lives_left:
			self._start_turn()
		
		if not self.lives_left:
			self._output_canvas()
			self._output_word()
			self._game.end()
		else:
			self._output_current_word_state()
