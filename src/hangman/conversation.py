from __future__ import annotations

from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import ClassVar, Literal

from .choice_list import ChoiceList


def _response_is_valid_choice(
	response: str,
	choices: ChoiceList | None
) -> bool:
	assert choices is not None
	
	return response in choices


def _no_op(_response: str, _choices: ChoiceList | None) -> Literal[True]:
	return True


@dataclass(frozen = True, slots = True, eq = False)
class Validator:
	predicate: ResponseValidator
	warning: str
	
	def __call__(self, response: str, choices: ChoiceList | None) -> bool:
		return self.predicate(response, choices)


InputGetter = Callable[[str], str]
OutputDisplayer = Callable[[str], None]
ResponseValidator = Callable[[str, ChoiceList | None], bool]

OneOrManyValidators = Validator | list[Validator]

_FailingValidators = Generator[Validator, None, None]


class Conversation:
	
	_INVALID_RESPONSE: ClassVar[str] = \
		'Invalid response. Please try again.'
	_INVALID_CHOICE: ClassVar[str] = \
		'Invalid choice. Please try again.'
	
	__slots__ = ('_input', '_output')
	
	_input: InputGetter
	_output: OutputDisplayer
	
	def __init__(self, ask: InputGetter, answer: OutputDisplayer) -> None:
		self._input = ask
		self._output = answer
	
	def _get_response(self, prompt: str) -> str:
		return self._input(prompt).upper()
	
	def _ask(
		self,
		prompt: str, /,
		choices: ChoiceList | None = None, *,
		validators: list[Validator]
	) -> str:
		failing_validators: Callable[[], _FailingValidators] = lambda: (
			validator for validator in validators
			if not validator(response, choices)
		)
		find_first_failing_validator: Callable[[], Validator | None] = \
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
		prompt = f'{question}\n'
		prompt += f'{choices}\n' if choices is not None else ''
		
		if choices is None and until is None:
			validators = [Validator(_no_op, '')]
		elif until is None:
			validators = [
				Validator(_response_is_valid_choice, self._INVALID_CHOICE)
			]
		else:
			validators = [until] if callable(until) else until
		
		return self._ask(
			prompt, choices,
			validators = validators
		)
	
	def answer(self, answer: str) -> None:
		self._output(answer)
