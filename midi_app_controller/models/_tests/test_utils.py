from typing import List, Optional

from pydantic import ValidationError
import pytest
import yaml

from ..utils import find_duplicate, YamlBaseModel


class TempYamlModel(YamlBaseModel):
    key1: str
    key2: str
    key3: List[str]
    key4: Optional[int]


class OtherTempYamlModel(YamlBaseModel):
    other_key: str


@pytest.fixture
def yaml_data():
    return {"key1": "value1", "key2": "value2", "key3": ["a", "b"], "key4": None}


@pytest.fixture
def yaml_str(yaml_data):
    dumped = yaml.safe_dump(yaml_data, default_flow_style=False)
    assert dumped == "key1: value1\nkey2: value2\nkey3:\n- a\n- b\nkey4: null\n"
    return dumped


@pytest.fixture
def yaml_file(tmp_path, yaml_str):
    yaml_file = tmp_path / "sample.yaml"
    with open(yaml_file, "w") as f:
        f.write(yaml_str)
    return yaml_file


def test_load_from(yaml_file, yaml_data):
    model = TempYamlModel.load_from(yaml_file)

    assert isinstance(model, TempYamlModel)
    assert model.dict() == yaml_data


def test_load_from_when_invalid_data(yaml_file, yaml_data):
    with pytest.raises(ValidationError):
        OtherTempYamlModel.load_from(yaml_file)


def test_save_to(yaml_data, yaml_str, tmp_path):
    model = TempYamlModel(**yaml_data)
    yaml_file = tmp_path / "saved.yaml"

    model.save_to(yaml_file)

    with open(yaml_file) as f:
        assert f.read() == yaml_str


@pytest.mark.parametrize(
    "values, result",
    [
        ([1, 2, 3], None),
        (["a", "b"], None),
        ([1, 2, 3, 1, 4], 1),
        ([1, 2, 1, 2], 1),
        ([], None),
    ],
)
def test_find_duplicate(values, result):
    assert find_duplicate(values) == result
