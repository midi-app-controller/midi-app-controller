import time
from typing import List, Dict

import rtmidi
from pydantic import BaseModel

from midi_app_controller.models.controller import Controller
from ..actions.actions_handler import ActionsHandler
from .controller_constants import ControllerConstants

# Leave uncommented for debug purpouses
# import sys


def midi_callback(message, cls):
    """Callback function for MIDI input, specified by rtmidi package.

    Parameters
    ----------
    message : List[int]
        Standard MIDI message.
    cls : ConnectedController
        ConnectedController class instance.
    """

    # Process MIDI message here
    status_byte = message[0][0]
    command = status_byte & 0xF0
    channel = status_byte & 0x0F
    data_bytes = message[0][1:]

    # Leave uncommented for debug purpouses
    # print(f"Command: {command}, Channel: {channel}, Data: {data_bytes}", file=sys.stdout)

    cls.handle_midi_message(command=command, channel=channel, data=data_bytes)


class ConnectedController(BaseModel):
    """A controller connected to the physical device capable of
    sending and receiving signals.

    Attributes
    ----------
    controller : Controller
        Data about the controller, the create method will try to connect to.
    actions_handler : ActionsHandler
        Actions handler class, responsible for executing actions, specific
        to a button press or a knob turn.
    midi_in : rtmidi.MidiIn
        Midi input client interface from python-rtmidi package.
    midi_out: rtmidi.MidiOut
        Midi output client interface from python-rtmidi package.
    button_ids : List[int]
        A list containing all valid button ids on a handled controller.
    button_engagement: Dict[int, int]
        A dictionary that keeps the state of every button.
    knob_ids : List[int]
        A list containing all valid knob ids on a handled controller.
    knob_engagement: Dict[int, int]
        A dictionary that keeps the value of every knob.
    """

    controller: Controller
    actions_handler: ActionsHandler
    midi_in: rtmidi.MidiIn
    midi_out: rtmidi.MidiOut
    button_ids: List[int]
    button_engagement: Dict[int, int]
    knob_ids: List[int]
    knob_engagement: Dict[int, int]

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def create(
        cls, *, actions_handler: ActionsHandler, controller: Controller
    ) -> "ConnectedController":
        """Creates an instance of `ConnectedController`.

        Parameters
        ----------
        actions_handler : ActionsHandler
            Provides methods capable of executing actions in the app.
        controller : Controller
            Information about the controller, the create method will
            try to connect to.

        Returns
        -------
        ConnectedController
            A created model.

        Raises
        ------
        IOError
            If there is no correct MIDI device connected.
        """

        button_ids = [element.id for element in controller.buttons]
        knob_ids = [element.id for element in controller.knobs]
        midi_in = None
        midi_out = None

        try:
            # Create an instance of MidiIn and MidiOut
            midi_in = rtmidi.MidiIn()
            midi_out = rtmidi.MidiOut()

            # Listing available MIDI ports
            available_ports_in = midi_in.get_ports()
            available_ports_out = midi_out.get_ports()

            available_ports = [
                port for port in available_ports_in if port in available_ports_out
            ]

            controller_port = ""
            port_index = -1

            if available_ports:
                for i, port in enumerate(available_ports):
                    name = port.split(":")[0]
                    if name == controller.name:
                        controller_port = port
                        port_index = i

            if controller_port == "":
                raise IOError("No correct MIDI ports available.")

            # Creating MidiIn and MidiOut instances
            midi_in.open_port(port_index)
            midi_out.open_port(port_index)

        except TypeError as err:
            print(f"Type Error: {err}")
        except SystemError as err:
            print(f"System Error: {err}")
        except rtmidi.InvalidPortError as err:
            print(f"Invalid Port Error: {err}")
        except rtmidi.InvalidUseError as err:
            print(f"Invalid Use Error: {err}")

        instance = cls(
            controller=controller,
            actions_handler=actions_handler,
            midi_out=midi_out,
            midi_in=midi_in,
            button_ids=button_ids,
            button_engagement={},
            knob_ids=knob_ids,
            knob_engagement={},
        )

        instance.init_buttons()
        instance.init_knobs()

        # Set callback for getting data from controller
        instance.midi_in.set_callback(midi_callback, data=instance)

        return instance

    def __del__(self):
        """Responsible for closing in/out ports, and safely deleting
        python-rtmidi classes.
        """
        self.midi_in.close_port()
        self.midi_in.delete()
        self.midi_out.close_port()
        self.midi_out.delete()

    def init_buttons(self):
        """Initializes the buttons on the controller, setting them
        to the 'off' value.

        Adds button entries to `button_engagement` dictionary.
        """
        for id in self.button_ids:
            self.turn_off_button_led(id)
            self.button_engagement[id] = self.controller.button_value_off

    def init_knobs(self):
        """Initializes the knobs on the controller, setting them
        to the minimal value. Adds knob entries to 'knob_engagement'
        dictionary.
        """
        for id in self.knob_ids:
            self.change_knob_value(id, self.controller.knob_value_min)
            self.knob_engagement[id] = self.controller.knob_value_min

    def handle_button_engagement(self, data):
        """Runs the action bound to the button, specified in
        action_handler.

        Parameters
        ----------
        data : List[int]
            Standard MIDI message.
        """
        id = data[0]

        self.action_handler.handle_button_action(
            button_id=id,
        )

    def handle_button_disengagement(self, data):
        """Runs the action bound to the button release, specified in
        action_handler.


        Parameters
        ----------
        data : List[int]
            Standard MIDI message.
        """
        pass  # TODO: for now we're not handling button disengagement

    def handle_knob_message(self, data):
        """Runs the action bound to the knob turn, specified in
        action_handler.


        Parameters
        ----------
        data : List[int]
            Standard MIDI message.
        """
        id = data[0]
        velocity = data[1]
        prev_velocity = self.knob_engagement[id]

        if velocity == self.controller.knob_value_min:
            prev_velocity = self.controller.knob_value_min + 1

        if velocity == self.controller.knob_value_max:
            prev_velocity = self.controller.knob_value_max - 1

        self.action_handler.handle_knob_action(
            knob_id=id,
            old_value=prev_velocity,
            new_value=velocity,
        )

    def send_midi_message(self, data):
        """Sends the specified MIDI message, using python-rtmidi
        MidiIn class.

        Parameters
        ----------
        data : List[int]
            Standard MIDI message.
        """
        try:
            self.midi_out.send_message(data)
        except ValueError as err:
            print(f"Value Error: {err}")

    def flash_knob(self, id):
        """Flashed the LEDs corresponding to a knob on a
        MIDI controller.

        Parameters
        ----------
        position : int
            Position of the knob.
        """
        sleep_seconds = 0.3

        for _ in range(3):
            self.change_knob_value(id, self.controller.knob_value_min)
            time.sleep(sleep_seconds)
            self.change_knob_value(id, self.controller.knob_value_max)
            time.sleep(sleep_seconds)

    def flash_button(self, id):
        """Flashed the button LED on a MIDI controller.

        Parameters
        ----------
        position : int
            Position of the button.
        """
        for _ in range(3):
            self.turn_on_button_led(id)
            time.sleep(0.3)
            self.turn_off_button_led(id)
            time.sleep(0.3)

    def change_knob_value(self, id, new_value):
        """Sends the MIDI message, responsible for changing
        a value assigned to a knob.

        Parameters
        ----------
        id : int
            Knob id.
        new_value : int
            Value to set the knob to.
        """
        data = [ControllerConstants.KNOB_VALUE_CHANGE_COMMAND, id, new_value]

        self.send_midi_message(data)

    def turn_on_button_led(self, id):
        """Sends the MIDI message, responsible for changing
        the button LED to 'on' state.

        Parameters
        ----------
        id : int
            Button id.
        """
        data = [
            ControllerConstants.BUTTON_VALUE_CHANGE_ON_COMMAND,
            id,
            self.controller.button_value_on,
        ]

        self.send_midi_message(data)

    def turn_off_button_led(self, id):
        """Sends the MIDI message, responsible for changing
        the button LED to 'off' state.

        Parameters
        ----------
        id : int
            Button id.
        """
        data = [
            ControllerConstants.BUTTON_VALUE_CHANGE_OFF_COMMAND,
            id,
            self.controller.button_value_off,
        ]

        self.send_midi_message(data)

    def handle_midi_message(self, command, channel, data):
        """Handles the incoming MIDI message.

        The message is interpreted as follows:
        [command*16+channel, data[0], data[1]],
        where the three numbers are unsigned ints.

        Parameters
        ----------
        command : int
            Command id.
        channel : int
            Channel the MIDI message came from.
        data : List[int]
            Remaining part of the MIDI message.
        """
        if id in self.knob_ids:
            self.handle_knob_message(command, channel, data)

        elif (
            id in self.button_ids
            and command == ControllerConstants.BUTTON_ENGAGED_COMMAND
        ):
            self.handle_button_engagement(command, channel, data)

        elif (
            id in self.button_ids
            and command == ControllerConstants.BUTTON_DISENGAGED_COMMAND
        ):
            self.handle_button_disengagement(command, channel, data)

        else:
            raise ValueError(f"action '{id}' cannot be found")
