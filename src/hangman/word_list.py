import random
from enum import StrEnum
from os import PathLike
from typing import ClassVar, final, Self

from ._static_reader import word_list_directory


class Level(StrEnum):
	EASY = 'EASY'
	MEDIUM = 'MEDIUM'
	HARD = 'HARD'
	UNIX = 'UNIX'


@final
class WordList:
	
	_instances: ClassVar[dict[str, Self]] = {}
	
	__slots__ = tuple(['_list'])
	
	_list: list[str]
	
	def __new__(cls, filename: str | PathLike[str]) -> 'Self':  # PY-62301
		filename = str(filename)
		
		if filename not in cls._instances:
			cls._instances[filename] = instance = super().__new__(cls)
			
			with open(filename) as file:
				instance._list = file.read().splitlines()
		
		return cls._instances[filename]
	
	def __len__(self) -> int:
		return len(self._list)
	
	def get_random_word(self) -> str:
		return random.choice(self._list)
	
	@classmethod
	def from_list(cls, words: list[str]) -> Self:
		instance = super().__new__(cls)
		instance._list = words
		
		return instance
	
	@classmethod
	def from_level(cls, level: str) -> Self:
		match level.upper():
			case Level.EASY:
				filename = 'easy.txt'
			case Level.MEDIUM:
				filename = 'medium.txt'
			case Level.HARD:
				filename = 'hard.txt'
			case Level.UNIX:
				filename = 'unix.txt'
			case _:
				raise ValueError('No such level')
		
		return cls(word_list_directory / filename)
