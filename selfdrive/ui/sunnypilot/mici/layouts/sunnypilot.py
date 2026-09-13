"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from openpilot.common.params import Params
from openpilot.selfdrive.ui.layouts.settings.common import restart_needed_callback
from openpilot.selfdrive.ui.mici.widgets.button import BigMultiParamToggle, BigMultiToggle, BigParamControl
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import MousePos
from openpilot.system.ui.widgets.scroller import NavScroller


class BigValueParamToggle(BigMultiToggle):
  """Cycle a numeric param through a fixed set of values; the labels are what the driver sees."""

  def __init__(self, text: str, param: str, values: list[int], labels: list[str]):
    super().__init__(text, labels)
    self._param = param
    self._values = values
    self._params = Params()
    self._load_value()

  def _load_value(self):
    try:
      cur = int(self._params.get(self._param, return_default=True))
    except (TypeError, ValueError):
      cur = self._values[0]
    idx = min(range(len(self._values)), key=lambda i: abs(self._values[i] - cur))
    self.set_value(self._options[idx])

  def _handle_mouse_release(self, mouse_pos: MousePos):
    super()._handle_mouse_release(mouse_pos)
    self._params.put(self._param, self._values[self._options.index(self.value)])


class SunnypilotLayoutMici(NavScroller):
  """The handful of sunnypilot settings this car uses, so they can be changed on the comma four
  screen instead of over SSH or through sunnylink. Speeds are mph; the car is not metric."""

  def __init__(self):
    super().__init__()

    # torque tuning: read once when the car starts, so parked-only and needs a restart
    self._enforce_torque = BigParamControl("enforce torque control", "EnforceTorqueControl", toggle_callback=restart_needed_callback)
    self._self_tune = BigParamControl("torque self-tune", "LiveTorqueParamsToggle", toggle_callback=restart_needed_callback)

    # live params: picked up while driving
    self._blinker_pause = BigParamControl("blinker pauses steering", "BlinkerPauseLateralControl")
    self._blinker_speed = BigValueParamToggle("blinker pause below", "BlinkerMinLateralControlSpeed",
                                              [35, 45, 55], ["35 mph", "45 mph", "55 mph"])
    self._sla_mode = BigMultiParamToggle("speed limit", "SpeedLimitMode", ["off", "info", "warning", "assist"])
    self._sla_offset = BigValueParamToggle("speed limit offset", "SpeedLimitValueOffset",
                                           [0, 5, 8], ["+0 mph", "+5 mph", "+8 mph"])
    self._road_name = BigParamControl("show road name", "RoadNameToggle")
    self._dev_ui = BigMultiParamToggle("developer ui", "DevUIInfo", ["off", "bottom", "right", "right & bottom"])
    self._rainbow = BigParamControl("rainbow path", "RainbowMode")

    self._bool_items = (self._enforce_torque, self._self_tune, self._blinker_pause, self._road_name, self._rainbow)
    self._value_items = (self._blinker_speed, self._sla_mode, self._sla_offset, self._dev_ui)

    self._scroller.add_widgets([
      self._enforce_torque,
      self._self_tune,
      self._blinker_pause,
      self._blinker_speed,
      self._sla_mode,
      self._sla_offset,
      self._road_name,
      self._dev_ui,
      self._rainbow,
    ])

    for item in (self._enforce_torque, self._self_tune):
      item.set_enabled(lambda: not ui_state.started)

  def show_event(self):
    super().show_event()
    # pick up anything changed over SSH since the page was last open
    for item in self._bool_items:
      item.refresh()
    for item in self._value_items:
      item._load_value()
