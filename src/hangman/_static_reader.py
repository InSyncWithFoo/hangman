from functools import partial
from os import PathLike
from pathlib import Path


package_directory = Path(__file__).resolve().parent
assets_directory = package_directory / 'assets'
word_list_directory = package_directory / 'words'


def _read(base_directory: Path, filename: PathLike[str]) -> str:
	with open(base_directory / filename) as file:
		return file.read()


get_asset = partial(_read, assets_directory)
get_word_list = partial(_read, word_list_directory)
