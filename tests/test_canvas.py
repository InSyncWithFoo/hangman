import math
import operator
import random
from dataclasses import astuple as as_tuple, FrozenInstanceError
from enum import Enum
from functools import partial
from pathlib import Path
from random import randint

import pytest

from hangman.canvas import Canvas, Component, Layer, LayerCell


def hangman():
	_assets = Path(__file__).resolve().parent / 'assets'
	
	with open(_assets / 'merged.txt') as file:
		lines = file.read().splitlines()
		
		return tuple(line.ljust(80) for line in lines)


class LayerContent(tuple[str], Enum):
	LOSS = (
		'|  ||',
		'|| |_'
	)
	HANGMAN = hangman()


@pytest.fixture(scope = 'module')
def canvas_10_80():
	return Canvas(height = 10, width = 80)


@pytest.fixture(scope = 'module')
def loss_layers():
	make_5_wide_layer = partial(Layer.from_sequence, width = 5)
	
	yield [
		make_5_wide_layer('|    ''     '),
		make_5_wide_layer('   ||''     '),
		make_5_wide_layer('     ''||   '),
		make_5_wide_layer('     ''   |_')
	]


@pytest.fixture(scope = 'module')
def loss():
	yield Layer(LayerContent.LOSS)


@pytest.fixture(scope = 'module')
def layer(request):
	return request.getfixturevalue(request.param)


@pytest.fixture(scope = 'module')
def layers(request):
	return request.getfixturevalue(f'{request.param}_layers')


@pytest.fixture(scope = 'module')
def loss_first_cell(loss):
	return next(loss.cells())


@pytest.mark.parametrize('layer, index, expected', [
	('loss', 0, (0, 0, '|')),
	('loss', 1, (0, 1, ' '))
], indirect = ['layer'])
def test_layer_cell_construction(layer, index, expected):
	cells = list(layer.cells())
	cell = cells[index]
	
	assert as_tuple(cell) == expected


@pytest.mark.parametrize('row, column, value', [
	(42, 43, 'foo')
])
def test_layer_cell_invalid_value(row, column, value):
	with pytest.raises(ValueError):
		_ = LayerCell(row, column, value)


@pytest.mark.parametrize('attribute, value', [
	('value', 'a'),
	('lorem', 'b')
])
def test_layer_cell_immutability(loss_first_cell, attribute, value):
	with pytest.raises(FrozenInstanceError):
		setattr(loss_first_cell, attribute, value)


@pytest.mark.parametrize('layer, height, width', [
	('loss', 2, 5)
], indirect = ['layer'])
def test_layer_construction(layer, height, width):
	assert layer.height == height
	assert layer.width == width


@pytest.mark.parametrize('text, height, width', [
	('\n'.join(LayerContent.LOSS), 2, 5)
])
def test_layer_construction_from_text(text, height, width):
	layer = Layer.from_text(text)
	
	assert layer.height == height
	assert layer.width == width


@pytest.mark.parametrize('text, width', [
	('\n'.join(LayerContent.LOSS), 10),
	('\n'.join(LayerContent.LOSS), 50)
])
def test_layer_construction_from_text_with_custom_width(text, width):
	layer = Layer.from_text(text, width = width)
	rows = list(layer.rows())
	padded_width = max(width, len(text.splitlines()[0]))
	
	assert all(len(row) == len(rows[0]) == padded_width for row in rows)


@pytest.mark.parametrize('sequence, width', [
	(''.join(LayerContent.LOSS), 5),
	(''.join(LayerContent.LOSS), 3)
])
def test_layer_construction_from_sequence(sequence, width):
	layer = Layer.from_sequence(sequence, width)
	
	assert layer.width == width
	assert layer.height == math.ceil(len(sequence) / width)


@pytest.mark.parametrize('layer, content', [
	('loss', LayerContent.LOSS)
], indirect = ['layer'])
def test_layer_repr(layer, content):
	horizontal_frame = f'+{'-' * len(content[0])}+'
	joined_rows = (f'|{row}|' for row in content)
	expected = '\n'.join([
		horizontal_frame,
		*joined_rows,
		horizontal_frame
	])
	
	assert repr(layer) == expected


@pytest.mark.parametrize('layer, item, expected', [
	('loss', 3, (0, 3, '|')),
	('loss', (1, 4), (1, 4, '_'))
], indirect = ['layer'])
def test_layer_getitem(layer, item, expected):
	cell = layer[item]
	
	assert isinstance(cell, LayerCell)
	assert as_tuple(cell) == expected


@pytest.mark.parametrize('layer, item, exception', [
	('loss', 2.5, TypeError),
	('loss', 'foo', TypeError),
	('loss', 14, IndexError),
	('loss', (3, 2), IndexError)
], indirect = ['layer'])
def test_layer_getitem_invalid(layer, item, exception):
	get_item = operator.itemgetter(item)
	
	with pytest.raises(exception):
		get_item(layer)


@pytest.mark.parametrize('layer, expected', [
	('loss', list(''.join(LayerContent.LOSS)))
], indirect = ['layer'])
def test_layer_iter(layer, expected):
	assert list(layer) == list(layer.cells())
	assert all(isinstance(cell, LayerCell) for cell in layer)
	assert [cell.value for cell in layer] == expected


@pytest.mark.parametrize('layer, expected', [
	('loss', len(''.join(LayerContent.LOSS)))
], indirect = ['layer'])
def test_layer_len(layer, expected):
	assert len(layer) == layer.height * layer.width == expected


@pytest.mark.parametrize('layer, other, expected', [
	('loss', Layer(LayerContent.LOSS), True),
	('loss', Layer(('foo', 'bar')), False),
	('loss', 'loss', False),
	('loss', '|  ||\n|| |_', False)
], indirect = ['layer'])
def test_layer_eq(layer, other, expected):
	assert (layer == other) is expected


@pytest.mark.parametrize('layer', [
	'loss'
], indirect = True)
def test_layer_copy(layer):
	copy = layer.copy()
	
	assert all(id(cell) for cell in copy)


@pytest.mark.parametrize('layers, expected', [
	('loss', Layer(LayerContent.LOSS))
], indirect = ['layers'])
def test_layer_add(layers, expected):
	merged = sum(layers[1:], start = layers[0])
	
	assert merged == expected


@pytest.mark.parametrize('layers, expected', [
	('loss', Layer(LayerContent.LOSS))
], indirect = ['layers'])
def test_layer_iadd(layers, expected):
	merged = first_copied = layers[0].copy()
	
	for layer in layers[1:]:
		merged += layer
	
	assert merged is first_copied
	assert merged == expected


@pytest.mark.parametrize('layer, expected', [
	('loss', LayerContent.LOSS)
], indirect = ['layer'])
def test_layer_rows(layer, expected):
	rows = list(layer.rows())
	
	for row_index, row in enumerate(rows):
		assert isinstance(row, tuple)
		
		for column_index, cell in enumerate(row):
			assert isinstance(cell, LayerCell)
			assert cell.value == expected[row_index][column_index]


@pytest.mark.parametrize('layer, expected', [
	('loss', LayerContent.LOSS)
], indirect = ['layer'])
def test_layer_columns(layer, expected):
	columns = list(layer.columns())
	
	for column_index, column in enumerate(columns):
		assert isinstance(column, tuple)
		
		for row_index, cell in enumerate(column):
			assert isinstance(cell, LayerCell)
			assert cell.value == expected[row_index][column_index]


@pytest.mark.parametrize('layer, expected', [
	('loss', ''.join(LayerContent.LOSS))
], indirect = ['layer'])
def test_layer_cells(layer, expected):
	cells = list(layer.cells())
	
	assert list(layer) == cells
	
	for cell, expected_value in zip(cells, expected):
		assert cell.value == expected_value


@pytest.mark.parametrize('height, width', [
	(randint(1, 100), randint(1, 100))
	for _ in range(5)
])
def test_canvas_construction(height, width):
	canvas = Canvas(height = height, width = width)
	
	assert (canvas.height, canvas.width) == (height, width)
	assert str(canvas).strip() == ''
	assert len(''.join(str(canvas).splitlines())) == height * width


@pytest.mark.parametrize('layer', [
	'loss'
], indirect = ['layer'])
def test_canvas_construction_from_layer(layer):
	canvas = Canvas.from_layer(layer)
	
	assert canvas.height == layer.height
	assert canvas.width == layer.width


@pytest.mark.parametrize('layer', [
	'loss'
], indirect = ['layer'])
def test_canvas_contains(layer):
	canvas = Canvas.from_layer(layer)
	
	assert layer in canvas


@pytest.mark.parametrize('layer', [
	'loss'
], indirect = ['layer'])
def test_canvas_iter(layer):
	canvas = Canvas.from_layer(layer)
	canvas_layers = list(canvas.layers)
	
	assert len(canvas_layers) == 1
	assert canvas_layers[0] is layer


@pytest.mark.parametrize('layer', [
	'loss'
], indirect = ['layer'])
def test_canvas_add_layers(layer):
	canvas = Canvas.from_layer(layer)
	to_be_added = [layer] * random.randint(3, 7)
	
	canvas.add_layers(*to_be_added)
	
	assert len(list(canvas.layers)) == len(to_be_added) + 1


# @pytest.mark.xfail
@pytest.mark.parametrize('layers, expected', [
	(Component, '\n'.join(LayerContent.HANGMAN))
])
def test_canvas_str(layers, expected):
	first, *others = layers
	canvas = Canvas.from_layer(first)
	
	canvas.add_layers(*others)
	
	assert str(canvas) == str(expected)

# @pytest.mark.xfail()
def test_component():
	assert all(isinstance(item, Layer) for item in Component)
