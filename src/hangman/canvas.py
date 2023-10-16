from __future__ import annotations

import dataclasses
from abc import ABC
from collections.abc import Collection, Container, Generator, Iterator, Sequence
from dataclasses import dataclass
from functools import partial
from itertools import batched
from typing import overload, Self

from ._lax_enum import LaxEnum
from ._static_reader import get_asset


@dataclass(frozen = True)
class LayerCell:
	row: int
	column: int
	value: str
	
	def __post_init__(self) -> None:
		if len(self.value) != 1:
			raise ValueError('"value" must be a single character')
	
	@property
	def is_transparent(self) -> bool:
		return self.value.strip() == ''


_GridOfStrings = Sequence[Sequence[str]]


class Layer:
	
	__slots__ = ('_cells', '_height', '_width')
	
	_cells: list[LayerCell]
	_height: int
	_width: int
	
	def __new__(cls, argument: _GridOfStrings) -> 'Self':  # PY-62301
		if isinstance(argument, str):
			raise TypeError('"rows" must not be a string')
		
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
		...
	
	@overload
	def __getitem__(self, item: tuple[int, int]) -> LayerCell:
		...
	
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
	
	@property
	def height(self) -> int:
		return self._height
	
	@property
	def width(self) -> int:
		return self._width
	
	@classmethod
	def from_text(cls, text: str, width: int | None = None) -> Self:
		lines = text.splitlines()
		
		if width is None:
			width = max(len(line) for line in lines)
		
		return cls([line.ljust(width) for line in text.splitlines()])
	
	@classmethod
	def from_sequence(cls, cells: Sequence[str], width: int) -> Self:
		rows = []
		
		for row in batched(cells, width):
			padder = ' ' * (width - len(row))
			rows.append(list(row) + list(padder))
		
		return cls(rows)
	
	def rows(self) -> Generator[tuple[LayerCell, ...], None, None]:
		yield from batched(self._cells, self._width)
	
	def columns(self) -> Generator[tuple[LayerCell, ...], None, None]:
		for column in zip(*self.rows()):
			yield column
	
	def cells(self) -> Generator[LayerCell, None, None]:
		yield from self
	
	def copy(self) -> Self:
		string_cells = [cell.value for cell in self]
		
		return self.__class__.from_sequence(string_cells, self._width)


class Canvas(Container[Layer]):
	
	__slots__ = ('_height', '_width', '_layers')
	
	_height: int
	_width: int
	_layers: list[Layer]
	
	def __init__(self, height: int, width: int) -> None:
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
	
	@property
	def height(self) -> int:
		return self._height
	
	@property
	def width(self) -> int:
		return self._width
	
	@property
	def layers(self) -> Generator[Layer, None, None]:
		for layer in self._layers:
			yield layer
	
	@classmethod
	def from_layer(cls, layer: Layer) -> Self:
		canvas = cls(height = layer.height, width = layer.width)
		canvas.add_layers(layer)
		
		return canvas
	
	def _fits_layer(self, layer: Layer) -> bool:
		return self._height == layer.height and self._width == layer.width
	
	def add_layers(self, *layers: Layer) -> None:
		if not all(self._fits_layer(layer) for layer in layers):
			raise ValueError(
				'Layers must have same height and width as canvas'
			)
		
		self._layers.extend(layers)


_make_80_wide_layer = partial(Layer.from_text, width = 80)


class Component(metaclass = LaxEnum):
	GALLOWS = _make_80_wide_layer(get_asset('gallows.txt'))
	HEAD = _make_80_wide_layer(get_asset('head.txt'))
	TRUNK = _make_80_wide_layer(get_asset('trunk.txt'))
	LEFT_ARM = _make_80_wide_layer(get_asset('left_arm.txt'))
	RIGHT_ARM = _make_80_wide_layer(get_asset('right_arm.txt'))
	LEFT_LEG = _make_80_wide_layer(get_asset('left_leg.txt'))
	RIGHT_LEG = _make_80_wide_layer(get_asset('right_leg.txt'))
	YOU_LOST = _make_80_wide_layer(get_asset('you_lost.txt'))
