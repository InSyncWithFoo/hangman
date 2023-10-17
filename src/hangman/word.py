class Word:
	
	'''
	A word being guessed.
	'''
	
	__slots__ = ('value', '_character_indices', '_masked')
	
	value: str
	_masked: list[str]
	_character_indices: dict[str, list[int]]
	
	def __init__(self, value: str) -> None:
		self.value = value.upper()
		self._masked = ['_'] * len(value)
		self._character_indices = {}
		
		for index, character in enumerate(self.value):
			self._character_indices.setdefault(character, []).append(index)
	
	def __str__(self) -> str:
		return self.value
	
	def __contains__(self, item: str) -> bool:
		return item.upper() in self._character_indices
	
	@property
	def current_state(self) -> str:
		'''
		The letters, space-separated; unguessed
		ones are replaced with underscores.
		'''
		
		return ' '.join(self._masked)
	
	@property
	def all_clear(self) -> bool:
		'''
		Whether all letters have been guessed correctly.
		'''
		
		return all(char != '_' for char in self._masked)
	
	def count(self, guess: str) -> int:
		'''
		Count the guess's appearances in the word
		and replace those with underscores in the
		current state.
		
		:param guess: A letter.
		:return: The number of its appearances.
		'''
		
		if guess not in self:
			return 0
		
		indices = self._character_indices[guess]
		
		for index in indices:
			self._masked[index] = guess
		
		return len(indices)
