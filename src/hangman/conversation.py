from __future__ import annotations

from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import ClassVar, Literal

from .choice_list import ChoiceList


def _response_is_valid_choice(
	response: str,
	choices: ChoiceList | None
) -> bool:
	'''
	Checks if the response is a valid choice.
	'''
	
	assert choices is not None
	
	return response in choices


def _no_op(_response: str, _choices: ChoiceList | None) -> Literal[True]:
	'''
	A validator that always returns ``True``.
	'''
	
	return True


@dataclass(frozen = True, slots = True, eq = False)
class Validator:
	'''
	Callable wrapper for a validator function.
	The second argument is the warning message
	to be output when this validator fails.
	'''
	
	predicate: ResponseValidator
	warning: str
	
	def __call__(self, response: str, choices: ChoiceList | None) -> bool:
		return self.predicate(response, choices)


InputGetter = Callable[[str], str]
OutputDisplayer = Callable[[str], None]
ResponseValidator = Callable[[str, ChoiceList | None], bool]

OneOrManyValidators = Validator | list[Validator]


class Conversation:
	
	'''
	Protocol for input-output operations.
	'''
	
	_INVALID_RESPONSE: ClassVar[str] = \
		'Invalid response. Please try again.'
	_INVALID_CHOICE: ClassVar[str] = \
		'Invalid choice. Please try again.'
	
	__slots__ = ('_input', '_output')
	
	_input: InputGetter
	_output: OutputDisplayer
	
	def __init__(self, ask: InputGetter, answer: OutputDisplayer) -> None:
		'''
		Construct a :class:`Conversation`.
		
		:param ask: A ``input``-like callable to be called for inputs.
		:param answer: A ``print``-like callable to be called to output.
		'''
		
		self._input = ask
		self._output = answer
	
	def _get_response(self, prompt: str) -> str:
		'''
		Get a raw response.
		
		:param prompt: The prompt to be used.
		:return: The response, uppercased.
		'''
		
		return self._input(prompt).upper()
	
	def _ask(
		self,
		prompt: str, /,
		choices: ChoiceList | None = None, *,
		validators: list[Validator]
	) -> str:
		'''
		Get a response, then validate it against the validators.
		Repeat this process until the response passes all validations.
		'''
		
		failing_validators = lambda: (
			validator for validator in validators
			if not validator(response, choices)
		)
		find_first_failing_validator = \
			lambda: next(failing_validators(), None)
		
		response = self._get_response(prompt)
		
		while failing_validator := find_first_failing_validator():
			self.answer(failing_validator.warning)
			response = self._get_response(prompt)
		
		return response
	
	def ask(
		self,
		question: str, /,
		choices: ChoiceList | None = None, *,
		until: OneOrManyValidators | None = None
	) -> str:
		r'''
		Thin wrapper around :meth:`_ask`.
		
		If ``choices`` is given, it will be included in
		the prompt text. If ``until`` is ``None``, a
		default validator will be used to check if
		the response is a valid choice.
		
		If both ``choices`` and ``until`` are ``None``,
		no validators will be applied.
		
		:param question: The question to ask.
		:param choices: The choices to choose from. Optional.
		:param until: \
			A :class:`Callable`, a :class:`Validator` or
			a list of :class:`Validator`\ s. Optional.
		:return: The response of the user.
		'''
		
		prompt = f'{question}\n'
		prompt += f'{choices}\n' if choices is not None else ''
		
		if choices is None and until is None:
			validators = [Validator(_no_op, '')]
		elif until is None:
			validators = [
				Validator(_response_is_valid_choice, self._INVALID_CHOICE)
			]
		elif isinstance(until, Validator):
			validators = [until]
		elif callable(until):
			validators = [Validator(until, self._INVALID_CHOICE)]
		else:
			validators = until
		
		return self._ask(
			prompt, choices,
			validators = validators
		)
	
	def answer(self, answer: str) -> None:
		'''
		Outputs the caller's message.
		
		:param answer: The message to output.
		'''
		
		self._output(answer)
