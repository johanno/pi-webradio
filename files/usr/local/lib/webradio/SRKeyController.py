#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Pi-Webradio: implementation of class KeyController
#
# The class KeyController maps key-events to api-calls
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/pi-webradio
#
# ----------------------------------------------------------------------------

import evdev, select
from webradio import Base

class KeyController(Base):
  """ map key-events to api-calls """

  # --- builtin-keymaps   ----------------------------------------------------

  KEYMAP_RADIO = {
    "KEY_1":     ["radio_play_channel", "nr=1"],
    "KEY_2":     ["radio_play_channel", "nr=2"],
    "KEY_3":     ["radio_play_channel", "nr=3"],
    "KEY_4":     ["radio_play_channel", "nr=4"],
    "KEY_5":     ["radio_play_channel", "nr=5"],
    "KEY_6":     ["radio_play_channel", "nr=6"],
    "KEY_7":     ["radio_play_channel", "nr=7"],
    "KEY_8":     ["radio_play_channel", "nr=8"],
    "KEY_9":     ["radio_play_channel", "nr=9"],
    "KEY_0":     ["radio_play_channel", "nr=10"],
    "KEY_D":     ["player_play_dir"],                   # TBD
    "KEY_F":     ["player_play_file"],                  # TBD
    "KEY_I":     ["radio_state"],                       # TBD
    "KEY_O":     ["radio_toggle"],
    "KEY_P":     ["player_mode_toggle"],                # TBD
    "KEY_Q":     ["sys_stop"],
    "KEY_R":     ["rec_toggle"],
    "KEY_L":     ["radio_get_channels"],
    "KEY_M":     ["vol_mute_toggle"],
    "KEY_LEFT":  ["radio_play_prev"],
    "KEY_RIGHT": ["radio_play_next"],
    "KEY_UP":    ["vol_up"],
    "KEY_DOWN":  ["vol_down"],
    "KEY_ENTER": ["player_select"]                      # TBD
    }

  KEY_SPECIAL = ['KEY_LEFTCTRL','KEY_LEFTALT','KEY_LEFTSHIFT',
                 'KEY_RIGHTCTRL','KEY_RIGHTALT','KEY_RIGHTSHIFT']

  # --- constructor   --------------------------------------------------------

  def __init__(self,stop,debug=False):
    """ constructor """

    self._stop    = stop
    self._kmap    = KeyController.KEYMAP_RADIO
    self.debug    = debug

  # --- yield api from key-event   -------------------------------------------

  def api_from_key(self):
    """ monitor key-events and yield mapped API-name """

    devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
    devices = {dev.fd: dev for dev in devices}

    special = 0                    # to ignore combinations with special keys
    while not self._stop.is_set():
      fds, _1, _2 = select.select(devices, [], [])
      for fd in fds:
        for event in devices[fd].read():
          event = evdev.util.categorize(event)
          if not isinstance(event, evdev.events.KeyEvent):
            continue
          self.msg("KeyController: processing %s (%d)" %
                   (event.keycode,event.keystate))
          if event.keystate == event.key_down:
            if event.keycode in KeyController.KEY_SPECIAL:
              special += 1
              continue
            elif special > 0:
              self.msg("KeyController: ignoring %s" % event.keycode)
              continue
            if event.keycode in self._kmap:
              # key is mapped, yield api-name
              self.msg("KeyController: mapping %s to %s" %
                       (event.keycode,self._kmap[event.keycode]))
              yield self._kmap[event.keycode]
            else:
              # key is not mapped, ignore
              self.msg("KeyController: ignoring %s" % event.keycode)
          elif event.keystate == event.key_up:
            if event.keycode in KeyController.KEY_SPECIAL:
              special = max(0,special-1)
