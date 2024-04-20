import os
from pathlib import Path
from typing import Any, List, Optional, Tuple
import uuid

from pydantic import BaseModel
import yaml

from midi_app_controller.config import Config
from midi_app_controller.gui.utils import is_subpath


# Enable writing Path objects as strings. When reading, pydantic converts strings into Paths automatically.
def _path_representer(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data))


yaml.SafeDumper.add_multi_representer(Path, _path_representer)


class YamlBaseModel(BaseModel):
    @classmethod
    def load_from(cls, path: Path) -> "YamlBaseModel":
        """Creates a model initialized with data from a YAML file.

        Parameters
        ----------
        path : Path
            YAML file path.

        Returns
        -------
        cls
            A created model.
        """
        with open(path) as f:
            data = yaml.safe_load(f)
            assert data is not None, "Empty file"
            return cls(**data)

    @classmethod
    def load_all_from(
        cls, directories: List[Path]
    ) -> List[Tuple["YamlBaseModel", Path]]:
        """Creates models initialized with data from all YAML files in multiple directories.

        Parameters
        ----------
        directories : List[Path]
            List of paths to directories with YAML files inside.

        Returns
        -------
        List[Tuple[cls, Path]]
            List of created models with paths to corresponding YAML files.
        """
        return [
            (
                cls.load_from(directory / filename),
                directory / filename,
            )
            for directory in directories
            if directory.exists()
            for filename in os.listdir(directory)
            if filename.lower().endswith((".yaml", ".yml"))
        ]

    def save_to(self, path: Path) -> None:
        """Saves the model's data to a YAML file.

        Never saves anything to readonly dirs as defined in Config. The folder
        where the output file should be will also be created.

        Parameters
        ----------
        path : Path
            YAML file path.
        """

        assert not is_subpath(Config.BINDS_READONLY_DIR, path)
        assert not is_subpath(Config.CONTROLLERS_READONLY_DIR, path)

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w") as f:
            yaml.safe_dump(self.dict(), f, default_flow_style=False)

    def save_copy_to(self, path: Path, new_dir: Path) -> Path:
        """Copy YAML to a new file avoiding file name collisions."""
        new_path = new_dir / path.name
        while new_path.exists():
            new_path = new_path.with_stem(f"{new_path.stem} {uuid.uuid1()}")
        self.save_to(new_path)
        return new_path


def find_duplicate(values: List[Any]) -> Optional[Any]:
    """Checks if there are any duplicates in the list and returns the first one.

    Parameters
    ----------
    values : list
        The list of values to be searched for duplicates.

    Returns
    -------
    Any
        The first duplicate if it exists.
    None
        If there are no duplicates.
    """
    seen = set()
    for val in values:
        if val in seen:
            return val
        seen.add(val)
    return None
