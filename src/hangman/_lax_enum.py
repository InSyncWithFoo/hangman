import re
from collections.abc import Generator
from re import Pattern
from typing import ClassVar


class LaxEnum(type):
	'''
	Despite its name, a LaxEnum is no different from
	a normal class except for that it yields every
	item that is not a dunder when being iterated over.
	'''
	
	_dunder: ClassVar[Pattern[str]] = re.compile(r'__.+__')
	
	def __iter__(cls) -> Generator[object, None, None]:
		for member_name, member in cls.__dict__.items():
			if not cls._dunder.fullmatch(member_name):
				yield member
