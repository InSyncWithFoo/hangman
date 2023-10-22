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
	
	'''
	The Hangman game.
	'''
	
	TITLE: ClassVar[str] = get_asset('title.txt')
	INSTRUCTIONS: ClassVar[str] = get_asset('instructions.txt')
	
	COEFFICENTS: ClassVar[dict[Level, int]] = {
		Level.EASY: 1,
		Level.MEDIUM: 2,
		Level.HARD: 3,
		Level.UNIX: 4
	}
	
	_MAX_DISPLAY_WIDTH: ClassVar[int] = 80
	
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
		'''
		Initialize a new game.
		
		See :class:`Conversation` for more information on
		``input_getter`` and ``output_displayer``.
		
		:param input_getter: \
			An ``input``-like function. Defaults to ``input``.
		:param output_displayer: \
			A ``print``-like function. Defaults to ``print``.
		:param reward: \
			The number of points to be added to
			the total on each correct guess.
		:param penalty: \
			The number of points to be subtracted from
			the total on each incorrect guess.
		'''
		
		self._used_words = set()
		self._points = 0
		self._reward, self._penalty = reward, penalty
		
		self._ended = False
		
		self._conversation = Conversation(ask = input_getter, reply = output_displayer)
	
	@property
	def points(self) -> int:
		'''
		The total points earned in this game.
		'''
		
		return self._points
	
	@points.setter
	def points(self, value: int) -> None:
		'''
		Called on operations such as the following:
		
			game.points += 1
		
		The number of points cannot be negative.
		'''
		
		self._points = max(value, 0)
	
	def _start(self) -> None:
		'''
		Output the title, the instructions, then start
		the first :class:`GameRound`. If that round is
		won and the user wants to continue, start another.
		
		Otherwise, if the game has not ended (user did
		not lose in the latest round), end the game.
		'''
		
		self._output_game_title()
		self._output_game_instructions()
		
		self._start_round()
		
		while not self._ended and self._prompt_for_continue_confirmation():
			self._start_round()
		
		if not self._ended:
			self.end()
	
	def _output_game_title(self) -> None:
		'''
		Output the title, which is just some fancy ASCII art.
		'''
		
		self.output(self.TITLE)
	
	def _output_game_instructions(self) -> None:
		'''
		Output the instructions.
		'''
		
		self.output(self.INSTRUCTIONS)
	
	def _prompt_for_continue_confirmation(self) -> bool:
		'''
		Ask for a response until it is a yes/no answer.
		
		:return: Whether the user wants to continue.
		'''
		
		answer = self.input('Continue?', Choices.CONFIRMATION)
		
		return answer in ('Y', 'YES')
	
	def _start_round(self) -> None:
		'''
		Ask for a level, construct a :class:`WordList` and
		a coefficient from that level, then get a random
		word that has not been used.
		
		Finally, initialize a :class:`GameRound` by passing
		the word and the coefficent to it.
		
		Technically, this function would go into an infinite
		loop when the user has played enough rounds, but let's
		hope that no one's that crazy.
		
		A bot? Sounds cool. Tell me if you write one.
		'''
		
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
		'''
		Pass ``word`` and ``coefficient`` as arguments
		to :class:`GameRound`.
		'''
		
		return GameRound(self, word, coefficient)
	
	def _prompt_for_level(self) -> Level:
		'''
		Ask for a response until it is a valid level.
		
		:return: The corresponding :class:`Level`.
		'''
		
		choices = Choices.LEVEL
		response = self._conversation.ask('Choose a level:', choices)
		
		value = choices[response].value
		
		assert value is not None
		
		return Level(value)
	
	def start(self) -> None:
		'''
		Start the game. If a :class:`KeyboardInterrupt`
		is caught, call :meth:`end`.
		'''
		
		try:
			self._start()
		except KeyboardInterrupt:
			self.end()
	
	def end(self) -> None:
		'''
		Switch a boolean flag and call
		:meth:`output_current_points`.
		'''
		
		self._ended = True
		self.output('Game over.'.center(self._MAX_DISPLAY_WIDTH, '-'))
		self.output_current_points()
	
	def input(
		self,
		prompt: str,
		choices: ChoiceList | None = None,
		validators: OneOrManyValidators | None = None
	) -> str:
		'''
		Shorthand for ``self.conversation.ask``.
		'''
		
		return self._conversation.ask(prompt, choices, until = validators)
	
	def output(self, reply: str) -> None:
		'''
		Shorthand for ``self.conversation.reply``.
		'''
		
		return self._conversation.reply(reply)
	
	def output_current_points(self) -> None:
		'''
		Output the total number of points earned.
		'''
		
		self.output(f'Points: {self._points}')
	
	def reward_correct_guess(self, count: int, coefficient: int) -> None:
		'''
		Add ``reward`` multiplied by ``coefficient`` and ``count``
		to the number of points.
		'''
		
		self.points += self._reward * count * coefficient
	
	def penalize_incorrect_guess(self, coefficient: int) -> None:
		'''
		Substract ``penalty`` multiplied by ``coefficient``
		from the number of points.
		'''
		
		self.points += self._penalty * coefficient


class GameRound:
	
	'''
	A game round. The game ends when
	a game round ends with a loss.
	'''
	
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
		'''
		Initialize a game round.
		
		There are initially 6 layers in the stack.
		Each incorrect guess pops one from the stack
		and adds it to the canvas. When the stack
		reaches 0, the entire game is over.
		
		See :class:`Word` for relevant checking logic.
		
		:param game: The game this round belongs to.
		:param word: The word to guess in this round.
		:param coefficient: \
			The coefficient corresponding to the level of this round.
		'''
		
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
		'''
		The number of layers left in the stack.
		'''
		
		return len(self._layer_stack)
	
	def _output_canvas(self) -> None:
		'''
		Output the canvas with all components
		lost via incorrect guesses.
		'''
		
		self._game.output(str(self._canvas))
	
	def _output_current_word_state(self) -> None:
		'''
		Output the word with unknown characters masked.
		'''
		
		self._game.output(f'Word: {self._word.current_state}')
	
	def _output_word(self) -> None:
		'''
		Output the word. Only called when the game is over.
		'''
		
		self._game.output(f'The word was "{self._word}".')
	
	def _start_turn(self) -> None:
		'''
		Call :meth:`_output_canvas` and :meth:`_output_current_word_state`.
		Ask for a new guess, then check it against
		the word and handle the result accordingly.
		'''
		
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
		'''
		Output a notice, then call :meth:`Game.penalize_incorrect_guess`
		and :meth:`Game.output_current_points`.
		
		Also call :meth:`_minus_1_life`. If the number of lives left
		is 0, add :attr:`Component.YOU_LOST` to the canvas.
		'''
		
		self._game.output('Incorrect guess.')
		self._game.penalize_incorrect_guess(self._coefficient)
		self._game.output_current_points()
		
		self._minus_1_life()
		
		if self.lives_left == 0:
			self._canvas.add_layers(Component.YOU_LOST)
	
	def _handle_correct_guess(self, guess: str, count: int) -> None:
		'''
		Output a notice, then call :meth:`Game.reward_correct_guess`
		and :meth:`Game.output_current_points`.
		
		:param guess: The character guessed.
		:param count: The number of that character's appearances in the word.
		'''
		
		if count == 1:
			self._game.output(f'There is {count} "{guess}"!')
		else:
			self._game.output(f'There are {count} "{guess}"s!')
		
		self._game.reward_correct_guess(count, self._coefficient)
		self._game.output_current_points()
	
	def _prompt_for_guess(self) -> str:
		'''
		Ask for a new guess which must be an ASCII letter.
		
		:return: The guess.
		'''
		
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
		'''
		Check if ``response`` is a previous guess.
		Meant to be called in :meth:`_prompt_for_guess`.
		
		:param response: The response to check.
		:return: Whether ``response`` is a previous guess.
		'''
		
		return response not in self._guesses
	
	def _minus_1_life(self) -> None:
		'''
		Pops a layer from the stack and add it to the canvas.
		'''
		
		self._canvas.add_layers(self._layer_stack.pop(0))
	
	def start(self) -> None:
		'''
		While the word is not completely solved and there
		are still some lives left, start a turn.
		
		If there are no lives left (user lost the game),
		call :meth:`_output_canvas` and :meth:`_output_word`,
		then :meth:`Game.end`.
		Otherwise, :meth:`_output_current_word_state`.
		'''
		
		while not self._word.all_clear and self.lives_left:
			self._start_turn()
		
		if not self.lives_left:
			self._output_canvas()
			self._output_word()
			self._game.end()
		else:
			self._output_current_word_state()
