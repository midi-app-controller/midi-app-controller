from typing import List
from pydantic import BaseModel, Field, root_validator, validator

from .utils import YamlBaseModel, find_duplicate


class ControllerElement(BaseModel):
    """Any element of a controller.

    Attributes
    ----------
    id : int
        The ID of the element that the controller sends with every event.
        Should be in the range [0, 127].
    name : str
        A user-defined name for the element that helps to differentiate elements.
        Cannot be empty.
    """

    id: int = Field(ge=0, le=127)
    name: str = Field(min_length=1)


class Controller(YamlBaseModel):
    """A controller's schema.

    Attributes
    ----------
    name : str
        The name of the controller. Cannot be empty. Must be unique among all schemas.
    button_value_off : int
        The number sent by the controller when a button is in 'off' state.
        Should be in the range [0, 127].
    button_value_on : int
        The number sent by the controller when a button is in 'on' state.
        Should be in the range [0, 127].
    knob_value_min : int
        The minimum value sent by the controller when a knob is rotated.
        Should be in the range [0, 127].
    knob_value_max : int
        The maximum value sent by the controller when a knob is rotated.
        Should be in the range [0, 127].
    buttons : List[ControllerElement]
        List of available buttons on the controller.
    knobs : List[ControllerElement]
        List of available knobs on the controller.
    """

    name: str = Field(min_length=1)
    button_value_off: int = Field(ge=0, le=127)
    button_value_on: int = Field(ge=0, le=127)
    knob_value_min: int = Field(ge=0, le=127)
    knob_value_max: int = Field(ge=0, le=127)
    buttons: List[ControllerElement]
    knobs: List[ControllerElement]

    @root_validator
    @classmethod
    def check_duplicate_ids(cls, values):
        """Ensures that every button and every knob has a different id."""
        button_ids = [elem.id for elem in values.get("buttons")]
        knob_ids = [elem.id for elem in values.get("knobs")]

        duplicate = find_duplicate(button_ids)
        if duplicate is not None:
            raise ValueError(f"id={duplicate} was used for multiple buttons")

        duplicate = find_duplicate(knob_ids)
        if duplicate is not None:
            raise ValueError(f"id={duplicate} was used for multiple knobs")

        return values

    @validator("buttons", "knobs")
    @classmethod
    def check_duplicate_names(
        cls, v: List[ControllerElement]
    ) -> List[ControllerElement]:
        """Ensures that no two elements of same kind have the same name."""
        names = [elem.name for elem in v]

        duplicate = find_duplicate(names)
        if duplicate is not None:
            raise ValueError(f"name={duplicate} was used for multiple elements")

        return v

    @root_validator
    @classmethod
    def check_button_values(cls, values):
        """Ensures that the 'off' and 'on' values for buttons are different."""
        if values.get("button_value_off") == values.get("button_value_on"):
            raise ValueError("button_value_off and button_value_on are equal")
        return values

    @root_validator
    @classmethod
    def check_knob_values(cls, values):
        """Ensures that the minimum value of knobs is smaller than the maximum value."""
        if values.get("knob_value_min") >= values.get("knob_value_max"):
            raise ValueError("knob_value_min must be smaller than knob_value_max")
        return values
