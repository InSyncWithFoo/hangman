from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import ClassVar

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


class _ValidatorList(list[Validator]):
	'''
	Provides one helper method: :meth:`find_first_failing_validator`.
	'''
	
	def find_first_failing_validator(
		self,
		response: str,
		choices: ChoiceList | None
	) -> Validator | None:
		'''
		Sequentially run all validators against the response
		and return the first one that fails.
		
		:param response: The response to be validated.
		:param choices: The valid choices.
		:return: \
			The first failing validator or ``None``
			if all passes.
		'''
		
		for validator in self:
			if not validator(response, choices):
				return validator
		
		return None


InputGetter = Callable[[str], str]
OutputDisplayer = Callable[[str], None]
ResponseValidator = Callable[[str, ChoiceList | None], bool]

OneOrManyValidators = ResponseValidator | Iterable[ResponseValidator]


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
	
	def __init__(self, ask: InputGetter, reply: OutputDisplayer) -> None:
		'''
		Construct a :class:`Conversation`.
		
		:param ask: A ``input``-like callable to be called for inputs.
		:param reply: A ``print``-like callable to be called to output.
		'''
		
		self._input = ask
		self._output = reply
	
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
		choices: ChoiceList | None,
		validators: _ValidatorList
	) -> str:
		'''
		Get a response, then validate it against the validators.
		Repeat this process until the response passes all validations.
		'''
		
		def find_first_failing_validator(_response: str) -> Validator | None:
			return validators.find_first_failing_validator(_response, choices)
		
		response = self._get_response(prompt)
		
		while failing_validator := find_first_failing_validator(response):
			self.reply(failing_validator.warning)
			response = self._get_response(prompt)
		
		return response
	
	def _make_validator(self, predicate: ResponseValidator, /) -> Validator:
		'''
		Construct a :class:`Validator` from a :class:`Callable`
		with :attr:`_INVALID_RESPONSE` as the message.
		
		:param predicate: A :class:`ResponseValidator`
		:return: \
			``predicate`` if it is already a :class:`Validator`,
			or a new :class:`Validator` otherwise.
		'''
		
		if isinstance(predicate, Validator):
			return predicate
		
		return Validator(predicate, self._INVALID_RESPONSE)
	
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
		
		validators = _ValidatorList()
		
		if choices is not None and until is None:
			validators.append(self._make_validator(_response_is_valid_choice))
		
		elif isinstance(until, Iterable):
			validators.extend(
				self._make_validator(predicate)
				for predicate in until
			)
		elif until is not None:
			validators.append(self._make_validator(until))
		
		return self._ask(prompt, choices, validators)
	
	def reply(self, reply: str) -> None:
		'''
		Outputs the caller's message.
		
		:param reply: The message to output.
		'''
		
		self._output(reply)
