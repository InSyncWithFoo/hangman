from __future__ import annotations

import dataclasses
from collections.abc import Collection, Generator, Iterator, Sequence
from dataclasses import dataclass
from functools import partial
from itertools import batched
from typing import Never, overload, Self

from ._lax_enum import LaxEnum
from ._static_reader import get_asset


@dataclass(frozen = True)
class LayerCell:
	'''
	Represents a layer cell.
	
	``value`` must be a single character.
	'''
	
	row: int
	column: int
	value: str
	
	def __post_init__(self) -> None:
		if len(self.value) != 1:
			raise ValueError('"value" must be a single character')
	
	@property
	def is_transparent(self) -> bool:
		'''
		Whether the value contains only whitespaces.
		'''
		
		return self.value.strip() == ''


_GridOfStrings = Sequence[Sequence[str]]


class Layer:
	
	r'''
	A rectangle grid of :class:`LayerCell`\ s.
	'''
	
	__slots__ = ('_cells', '_height', '_width')
	
	_cells: list[LayerCell]
	_height: int
	_width: int
	
	def __new__(cls, argument: _GridOfStrings, /) -> 'Self':  # PY-62301
		'''
		Construct a :class:`Layer`.
		
		:param argument: A grid of strings. Cannot be a string itself.
		'''
		
		if isinstance(argument, str):
			raise TypeError('"argument" must not be a string')
		
		instance = super().__new__(cls)
		grid = [list(row) for row in argument]
		first_row = grid[0]
		
		same_width = all(len(row) == len(first_row) for row in grid)
		
		if not same_width:
			raise ValueError('All rows must have the same width')
		
		instance._height = len(grid)
		instance._width = len(first_row)
		instance._cells = []
		
		for row_index, row in enumerate(grid):
			for column_index, cell_value in enumerate(row):
				cell = LayerCell(row_index, column_index, cell_value)
				
				instance._cells.append(cell)
		
		return instance
	
	def __repr__(self) -> str:
		horizontal_frame = f'+{'-' * self._width}+'
		
		joined_rows = (
			f'|{''.join(cell.value for cell in row)}|'
			for row in self.rows()
		)
		
		return '\n'.join([
			horizontal_frame,
			*joined_rows,
			horizontal_frame
		])
	
	@overload
	def __getitem__(self, item: int) -> LayerCell:
		pass
	
	@overload
	def __getitem__(self, item: tuple[int, int]) -> LayerCell:
		pass
	
	def __getitem__(self, item: int | tuple[int, int]) -> LayerCell:
		if isinstance(item, int):
			return self._cells[item]
		
		if isinstance(item, tuple) and len(item) == 2:
			row_index, column_index = item
			
			if row_index >= self._height or column_index >= self._width:
				raise IndexError('Row or column index is out of bounds')
			
			index = self._width * row_index + column_index
			
			return self[index]
		
		raise TypeError(f'Invalid index')
	
	def __iter__(self) -> Iterator[LayerCell]:
		yield from self._cells
	
	def __len__(self) -> int:
		return len(self._cells)
	
	def __eq__(self, other: object) -> bool:
		if not isinstance(other, Layer):
			return NotImplemented
		
		return self._cells == other._cells
	
	def __add__(self, other: Layer) -> Layer:
		if not isinstance(other, Layer):
			return NotImplemented
		
		copied = self.copy()
		copied += other
		
		return copied
	
	def __iadd__(self, other: Layer) -> Self:
		if not isinstance(other, Layer):
			return NotImplemented
		
		if self.height != other.height or self.width != other.width:
			raise ValueError(
				'To be added, two layers must have the same height and width'
			)
		
		copy_cell = dataclasses.replace
		
		for index, other_cell in enumerate(other):
			if not other_cell.is_transparent:
				self._cells[index] = copy_cell(other_cell)
		
		return self
	
	def __copy__(self) -> Self:
		return self.copy()
	
	def __deepcopy__(self, _memodict: dict[Never, Never]) -> Self:
		return self.copy()
	
	@property
	def height(self) -> int:
		'''
		The height of the layer.
		'''
		
		return self._height
	
	@property
	def width(self) -> int:
		'''
		The width of the layer.
		'''
		
		return self._width
	
	@classmethod
	def from_text(cls, text: str, width: int | None = None) -> Self:
		'''
		Construct a :class:`Layer` from a piece of text.
		
		:param text: Any string, with one or more lines.
		:param width: \
			The width of the layer.
		:return: A new :class:`Layer`.
		'''
		
		if width is None:
			width = -1
		
		lines = text.splitlines()
		longest_line_length = max(len(line) for line in lines)
		
		width = max([longest_line_length, width])
		
		return cls([line.ljust(width) for line in text.splitlines()])
	
	@classmethod
	def from_sequence(cls, cells: Sequence[str], width: int) -> Self:
		'''
		Construct a :class:`Layer` from a sequence of strings.
		
		:param cells: A :class:`Sequence` of strings.
		:param width: \
			The number of cells per chunk. \
			The last chunk is padded with spaces.
		:return: A new :class:`Layer`.
		'''
		
		rows = []
		
		for row in batched(cells, width):
			if len(row) < width:
				padder = ' ' * (width - len(row))
				rows.append([*row, *padder])
			else:
				rows.append(list(row))
		
		return cls(rows)
	
	def rows(self) -> Generator[tuple[LayerCell, ...], None, None]:
		r'''
		Yield a tuple of :class:`LayerCell`\ s for each row.
		'''
		
		yield from batched(self._cells, self._width)
	
	def columns(self) -> Generator[tuple[LayerCell, ...], None, None]:
		r'''
		Yield a tuple of :class:`LayerCell`\ s for each column.
		'''
		
		for column in zip(*self.rows()):
			yield column
	
	def cells(self) -> Generator[LayerCell, None, None]:
		'''
		Synonym of :meth:`__iter__`.
		'''
		
		yield from self
	
	def copy(self) -> Self:
		'''
		Construct a new :class:`Layer` from this one.
		'''
		
		string_cells = [cell.value for cell in self]
		
		return self.__class__.from_sequence(string_cells, self._width)


class Canvas(Collection[Layer]):
	
	r'''
	A collection of :class:`Layers`.
	Its string representation is that of all its layers merged.
	'''
	
	__slots__ = ('_height', '_width', '_layers')
	
	_height: int
	_width: int
	_layers: list[Layer]
	
	def __init__(self, height: int, width: int) -> None:
		'''
		Construct a :class:`Canvas` of given height and width.
		
		:param height: The height of the canvas.
		:param width: The width of the canvas.
		'''
		
		self._height = height
		self._width = width
		self._layers = []
	
	def __str__(self) -> str:
		if not self._layers:
			return '\n'.join([' ' * self._width] * self._height)
		
		first, *others = self._layers
		flattened = sum(others, start = first)
		
		joined_rows = [
			''.join(cell.value for cell in row)
			for row in flattened.rows()
		]
		
		return '\n'.join(joined_rows)
	
	def __contains__(self, layer: object) -> bool:
		return layer in self._layers
	
	def __iter__(self) -> Iterator[Layer]:
		return iter(self._layers)
	
	def __len__(self) -> int:
		return len(self._layers)
	
	@property
	def height(self) -> int:
		'''
		The height of the canvas.
		'''
		
		return self._height
	
	@property
	def width(self) -> int:
		'''
		The width of the canvas.
		'''
		
		return self._width
	
	@property
	def layers(self) -> Generator[Layer, None, None]:
		'''
		Yield every layer the canvas contains.
		'''
		
		for layer in self._layers:
			yield layer
	
	@classmethod
	def from_layer(cls, layer: Layer) -> Self:
		'''
		Construct a :class:`Canvas` from a layer
		using its height and width.
		
		:param layer: A :class:`Layer`.
		:return: A new :class:`Canvas`.
		'''
		
		canvas = cls(height = layer.height, width = layer.width)
		canvas.add_layers(layer)
		
		return canvas
	
	def _fits_layer(self, layer: Layer) -> bool:
		'''
		Whether the layer has same height and width as the canvas.
		
		:param layer: A :class:`Layer`.
		:return: ``True`` if the layer fits, ``False`` otherwise.
		'''
		
		return self._height == layer.height and self._width == layer.width
	
	def add_layers(self, *layers: Layer) -> None:
		r'''
		Add one or more :class:`Layer`\ s to the canvas.
		
		:param layers: One or more :class:`Layer`\ s.
		'''
		
		if not all(self._fits_layer(layer) for layer in layers):
			raise ValueError(
				'Layers must have same height and width as canvas'
			)
		
		self._layers.extend(layers)


_make_80_wide_layer = partial(Layer.from_text, width = 80)


class Component(metaclass = LaxEnum):
	r'''
	Pre-built :class:`Layer`\ s to be used in the game.
	'''
	
	GALLOWS = _make_80_wide_layer(get_asset('gallows.txt'))
	HEAD = _make_80_wide_layer(get_asset('head.txt'))
	TRUNK = _make_80_wide_layer(get_asset('trunk.txt'))
	LEFT_ARM = _make_80_wide_layer(get_asset('left_arm.txt'))
	RIGHT_ARM = _make_80_wide_layer(get_asset('right_arm.txt'))
	LEFT_LEG = _make_80_wide_layer(get_asset('left_leg.txt'))
	RIGHT_LEG = _make_80_wide_layer(get_asset('right_leg.txt'))
	YOU_LOST = _make_80_wide_layer(get_asset('you_lost.txt'))
