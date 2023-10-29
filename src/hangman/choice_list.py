from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from typing import Final, Mapping, NamedTuple, Self

from ._lax_enum import LaxEnum
from .word_list import Level


@dataclass(frozen = True, slots = True)
class Choice:
	'''
	Represents a valid choice of a :class:`ChoiceList`.
	'''
	
	shortcut: str
	description: str
	aliases: frozenset[str]
	value: str | None = None
	
	def __str__(self) -> str:
		return f'[{self.shortcut}] {self.description}'


_ChoiceDescriptor = tuple[str, set[str], str | None]


class ChoiceDescriptor(NamedTuple):
	'''
	Syntactic sugar for a bare tuple containing three elements:
	``description``, ``aliases``, and ``value``.
	'''
	
	description: str
	aliases: set[str] = set()
	value: str | None = None


class _LengthList(list[int]):
	'''
	A list of integers which keeps track of the sum.
	Meant for internal use only.
	'''
	
	total: int
	
	def __new__(cls) -> 'Self':  # PY-62301
		instance = super().__new__(cls)
		instance.total = 0
		
		return instance
	
	def append(self, value: int) -> None:
		'''
		Append an integer value to the end of
		the list and add it the total.
		
		:param value: A length.
		'''
		self.total += value
		super().append(value)


class ChoiceList:
	
	__slots__ = ('_shortcut_map', '_alias_map', 'max_width', 'separator')
	
	_shortcut_map: dict[str, Choice]
	_alias_map: dict[str, Choice]
	
	separator: str
	max_width: int
	
	def __new__(
		cls, /,
		argument: Mapping[str, _ChoiceDescriptor] | None = None, *,
		separator: str = '  ',
		max_width: int = 80,
		**kwargs: _ChoiceDescriptor
	) -> 'Self':  # PY-62301
		r'''
		Construct a list of valid choices whose string
		representation looks like the following::
		
			[A] Foobar bazqux  [BAR] Lorem ipsum
			[C] Consectetur adipiscing elit
		
		All shorcuts and aliases are case-insensitive and
		mapped to their corresponding :class:`Choice`.
		Shortcuts are uppercased in the string representation.
		
		A :class:`Choice` can be chosen by referencing
		either ``shortcut`` or any of the ``aliases``.
		
		``argument`` and ``kwargs`` are shortcut-to-:class:`ChoiceDescriptor`
		maps. Each ``shortcut`` *should* be a single character,
		whereas the ``description``\ s need to be human-readable.
		``value`` is the value the choice represents,
		defaults to ``None``.
		
		:param argument: A :class:``collections.abc.Mapping``.
		:param separator: \
			A string to be used as the separator
			in the string representation.
		:param max_width: \
			The maximum width of the string
			representation, in characters.
		:param kwargs: \
			Other shortcut-to-descriptor arguments.
		'''
		
		if isinstance(argument, Mapping):
			kwargs = {**argument, **kwargs}
		
		instance = super().__new__(cls)
		
		instance.separator = separator
		instance.max_width = max_width
		
		shortcut_map = instance._shortcut_map = {}
		alias_map = instance._alias_map = {}
		
		for shortcut, (description, aliases, value) in kwargs.items():
			shortcut = shortcut.upper()
			uppercased_aliases = frozenset(alias.upper() for alias in aliases)
			
			choice = Choice(
				shortcut, description,
				uppercased_aliases, value
			)
			
			shortcut_map[shortcut] = choice
			
			for alias in uppercased_aliases:
				alias_map[alias] = choice
		
		return instance
	
	def __contains__(self, item: object) -> bool:
		if not isinstance(item, str):
			return False
		
		item = item.upper()
		
		return item in self._shortcut_map or item in self._alias_map
	
	def __getitem__(self, item: str) -> Choice:
		item = item.upper()
		
		if item in self._shortcut_map:
			return self._shortcut_map[item]
		
		return self._alias_map[item]
	
	def __str__(self) -> str:
		output: list[list[str]] = [[]]
		lengths: list[_LengthList] = [_LengthList()]
		
		for choice in self:
			choice_stringified = str(choice)
			choice_length = len(choice_stringified)
			
			total_choice_length = lengths[-1].total + choice_length
			total_separator_length = len(self.separator) * len(lengths[-1])
			new_last_row_length = total_choice_length + total_separator_length
			
			if new_last_row_length > self.max_width:
				output.append([])
				lengths.append(_LengthList())
			
			output[-1].append(choice_stringified)
			lengths[-1].append(choice_length)
		
		return '\n'.join(self.separator.join(row) for row in output)
	
	def __repr__(self) -> str:
		return (
			f'{self.__class__.__name__}(' +
			', '.join(repr(choice) for choice in self) +
			f')'
		)
	
	def __iter__(self) -> Generator[Choice, None, None]:
		yield from self._shortcut_map.values()


class Choices(metaclass = LaxEnum):
	'''
	Pre-built instances of :class:`ChoicesList`.
	'''
	
	CONFIRMATION: Final[ChoiceList] = ChoiceList(
		Y = ChoiceDescriptor(
			description = 'Yes',
			aliases = {'Yes'},
			value = 'YES'
		),
		N = ChoiceDescriptor(
			description = 'No',
			aliases = {'No'},
			value = 'NO'
		)
	)
	LEVEL: Final[ChoiceList] = ChoiceList(
		E = ChoiceDescriptor(
			description = 'Easy (22.5k words)',
			aliases = {'EASY'},
			value = Level.EASY
		),
		M = ChoiceDescriptor(
			description = 'Medium (74.5k words)',
			aliases = {'MEDIUM'},
			value = Level.MEDIUM
		),
		H = ChoiceDescriptor(
			description = 'Hard (168k words)',
			aliases = {'HARD'},
			value = Level.HARD
		),
		U = ChoiceDescriptor(
			description = 'Unix (205k words)',
			aliases = {'UNIX'},
			value = Level.UNIX
		)
	)
