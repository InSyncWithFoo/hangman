from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from typing import ClassVar, Mapping, NamedTuple, Self

from ._lax_enum import LaxEnum
from .word_list import Level


@dataclass(frozen = True, slots = True)
class Choice:
	shortcut: str
	description: str
	aliases: frozenset[str]
	value: str | None = None
	
	def __str__(self) -> str:
		return f'[{self.shortcut}] {self.description}'


_ChoiceDescriptor = tuple[str, set[str], str | None]


class ChoiceDescriptor(NamedTuple):
	description: str
	aliases: set[str] = set()
	value: str | None = None


class _LengthList(list[int]):
	
	total: int
	
	def __new__(cls) -> 'Self':  # PY-62301
		instance = super().__new__(cls)
		instance.total = 0
		
		return instance
	
	def append(self, value: int) -> None:
		self.total += value
		super().append(value)


class ChoiceList:
	
	_MAX_WIDTH: ClassVar[int] = 80
	_SEPARATOR: ClassVar[str] = ' ' * 2
	
	__slots__ = ('_shortcut_map', '_alias_map')
	
	_shortcut_map: dict[str, Choice]
	_alias_map: dict[str, Choice]
	
	def __new__(
		cls, /,
		argument: Mapping[str, _ChoiceDescriptor] | None = None,
		**kwargs: _ChoiceDescriptor
	) -> 'Self':  # PY-62301
		if isinstance(argument, Mapping):
			kwargs = {**argument, **kwargs}
		
		instance = super().__new__(cls)
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
			total_separator_length = len(self._SEPARATOR) * len(lengths[-1])
			new_last_row_length = total_choice_length + total_separator_length
			
			if new_last_row_length > self._MAX_WIDTH:
				output.append([])
				lengths.append(_LengthList())
			
			output[-1].append(choice_stringified)
			lengths[-1].append(choice_length)
		
		return '\n'.join(self._SEPARATOR.join(row) for row in output)
	
	def __repr__(self) -> str:
		return (
			f'{self.__class__.__name__}(' +
			', '.join(repr(choice) for choice in self) +
			f')'
		)
	
	def __iter__(self) -> Generator[Choice, None, None]:
		yield from self._shortcut_map.values()


class Choices(metaclass = LaxEnum):
	CONFIRMATION = ChoiceList(
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
	LEVEL = ChoiceList(
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
