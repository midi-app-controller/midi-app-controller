import pytest
from typing import List
from app_model.types import Action

from ..bound_controller import BoundController, ButtonActions, KnobActions
from midi_app_controller.models.binds import Binds
from midi_app_controller.models.controller import Controller


@pytest.fixture
def binds() -> Binds:
    binds_data = {
        "name": "TestBinds",
        "description": "Test description",
        "app_name": "TestApp",
        "controller_name": "TestController",
        "button_binds": [{"button_id": 1, "action_id": "Action1"}],
        "knob_binds": [
            {
                "knob_id": 2,
                "action_id_increase": "incr",
                "action_id_decrease": "decr",
            }
        ],
    }
    return Binds(**binds_data)


@pytest.fixture
def controller() -> Controller:
    controller_data = {
        "name": "TestController",
        "button_value_off": 11,
        "button_value_on": 100,
        "knob_value_min": 33,
        "knob_value_max": 55,
        "buttons": [{"id": 0, "name": "Button1"}, {"id": 1, "name": "Button2"}],
        "knobs": [{"id": 2, "name": "Knob1"}, {"id": 3, "name": "Knob2"}],
    }
    return Controller(**controller_data)


@pytest.fixture
def actions() -> List[Action]:
    return [
        Action(
            id="Action1",
            title="sdfgsdfg",
            callback=lambda: None,
        ),
        Action(
            id="incr",
            title="dfgssdfg",
            callback=lambda: None,
        ),
        Action(
            id="decr",
            title="sdfdfg",
            callback=lambda: None,
        ),
        Action(
            id="other",
            title="aaaasfd",
            callback=lambda: None,
        ),
    ]


@pytest.fixture
def bound_controller(binds, controller, actions) -> BoundController:
    return BoundController.create(binds=binds, controller=controller, actions=actions)


def test_button_actions(actions):
    data = {"action_press": actions[0]}
    actions = ButtonActions(**data)

    assert actions.dict() == data


def test_knob_actions(actions):
    data = {"action_increase": actions[0], "action_decrease": actions[1]}
    actions = KnobActions(**data)

    assert actions.dict() == data


def test_bound_controller(binds, controller, actions):
    bound_controller = BoundController.create(
        binds=binds, controller=controller, actions=actions
    )

    assert bound_controller.knob_value_min == controller.knob_value_min
    assert bound_controller.knob_value_max == controller.knob_value_max
    assert bound_controller.buttons.keys() == {
        bind.button_id for bind in binds.button_binds
    }
    assert bound_controller.knobs.keys() == {bind.knob_id for bind in binds.knob_binds}

    for bind in binds.button_binds:
        bound_button = bound_controller.buttons[bind.button_id]
        assert bound_button.action_press.id == bind.action_id
    for bind in binds.knob_binds:
        bound_knob = bound_controller.knobs[bind.knob_id]
        assert bound_knob.action_increase.id == bind.action_id_increase
        assert bound_knob.action_decrease.id == bind.action_id_decrease


@pytest.mark.parametrize("action_index_to_delete", [0, 1, 2])
def test_non_existent_action_id(binds, controller, actions, action_index_to_delete):
    actions.pop(action_index_to_delete)

    with pytest.raises(ValueError):
        BoundController.create(binds=binds, controller=controller, actions=actions)


def test_non_existent_knob(binds, controller, actions):
    controller.knobs.pop(0)

    with pytest.raises(ValueError):
        BoundController.create(binds=binds, controller=controller, actions=actions)


def test_non_existent_button(binds, controller, actions):
    controller.buttons.pop(1)

    with pytest.raises(ValueError):
        BoundController.create(binds=binds, controller=controller, actions=actions)


def test_different_controller_name(binds, controller, actions):
    controller.name = "asdfjkasdfjk"

    with pytest.raises(ValueError):
        BoundController.create(binds=binds, controller=controller, actions=actions)


def test_get_button_press_action(actions, bound_controller):
    assert bound_controller.get_button_press_action(1) == actions[0]


@pytest.mark.parametrize("knob_id", [2, 10, 1000])
def test_get_button_press_action_when_not_found(bound_controller, knob_id):
    assert bound_controller.get_button_press_action(knob_id) is None


def test_get_knob_increase_action(actions, bound_controller):
    assert bound_controller.get_knob_increase_action(2) == actions[1]


@pytest.mark.parametrize("knob_id", [3, 10, 1000])
def test_get_knob_increase_action_when_not_found(bound_controller, knob_id):
    assert bound_controller.get_knob_increase_action(knob_id) is None


def test_get_knob_decrease_action(actions, bound_controller):
    assert bound_controller.get_knob_decrease_action(2) == actions[2]


@pytest.mark.parametrize("knob_id", [3, 10, 1000])
def test_get_knob_decrease_action_when_not_found(bound_controller, knob_id):
    assert bound_controller.get_knob_decrease_action(knob_id) is None
