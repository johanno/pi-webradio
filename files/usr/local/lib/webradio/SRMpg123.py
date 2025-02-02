#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Pi-Webradio: implementation of class Mpg123
#
# The class Mpg123 encapsulates the mpg123-process for playing MP3s.
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/pi-webradio
#
# -----------------------------------------------------------------------------

import threading, subprocess, signal, os, shlex, re, traceback
from threading import Thread
import queue, collections, time

from webradio import Base

class Mpg123(Base):
  """ mpg123 control-object """

  def __init__(self,app):
    """ initialization """

    self._app       = app
    self._api       = app.api
    self.debug      = app.debug
    self._process   = None
    self._op_event  = threading.Event()
    self._play      = False
    self._pause     = False
    self._volume    = -1
    self._elapsed   = 0
    self._mute      = False
    self._url       = None

    self.read_config()
    self.register_apis()

  # --- read configuration   --------------------------------------------------

  def read_config(self):
    """ read configuration from config-file """

    # section [MPG123]
    self._vol_default = int(self.get_value(self._app.parser,"MPG123",
                                       "vol_default",30))
    self._volume      = self._vol_default
    self._vol_delta   = int(self.get_value(self._app.parser,"MPG123",
                                       "vol_delta",5))
    self._mpg123_opts = self.get_value(self._app.parser,"MPG123",
                                       "mpg123_opts","")

  # --- register APIs   ------------------------------------------------------

  def register_apis(self):
    """ register API-functions """

    self._api.vol_up          = self.vol_up
    self._api.vol_down        = self.vol_down
    self._api.vol_set         = self.vol_set
    self._api.vol_mute_on     = self.vol_mute_on
    self._api.vol_mute_off    = self.vol_mute_off
    self._api.vol_mute_toggle = self.vol_mute_toggle

  # --- return persistent state of this class   -------------------------------

  def get_persistent_state(self):
    """ return persistent state (overrides SRBase.get_pesistent_state()) """
    return {
      'volume': self._volume if not self._mute else self._vol_old
      }

  # --- restore persistent state of this class   ------------------------------

  def set_persistent_state(self,state_map):
    """ restore persistent state (overrides SRBase.set_pesistent_state()) """

    self.msg("Mpg123: restoring persistent state")
    if 'volume' in state_map:
      self._volume = state_map['volume']
    else:
      self._volume = self._vol_default
    self.msg("Mpg123: volume is: %d" % self._volume)

  # --- active-state (return true if playing)   --------------------------------

  def is_active(self):
    """ return active (playing) state """

    return self._process is not None and self._process.poll() is None

  # --- elapsed time   ---------------------------------------------------------

  def elapsed(self):
    """ return relative elapsed time (0.0-1.0) """

    return self._elapsed

  # --- create player in the background in remote-mode   ----------------------

  def create(self):
    """ spawn new mpg123 process """

    args = ["mpg123","-R"]
    opts = shlex.split(self._mpg123_opts)
    args += opts

    self.msg("Mpg123: starting mpg123 with args %r" % (args,))
    # start process with line-buffered stdin/stdout
    self._process = subprocess.Popen(args,bufsize=1,
                                     universal_newlines=True,
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT,
                                     errors='replace')
    self._reader_thread = Thread(target=self._process_stdout)
    self._reader_thread.start()
    self.vol_set(self._volume)

  # --- play URL/file   -------------------------------------------------------

  def play(self,url,last=True,elapsed=-1):
    """ start playing, return True if a new file/url is started """

    if self._process:
      if self._play:
        check_url = url if url.startswith("http") else os.path.basename(url)
        if check_url == self._url:   # already playing
          if not url.startswith("http"):
            self._exec_cmd("SAMPLE")
          return False
        self.stop(last=False)        # since we are about to play another file
      self.msg("Mpg123: starting to play %s" % url)
      self._last = last
      if url.startswith("http"):
        self._url   = url
      else:
        self._url   = os.path.basename(url)
      if url.endswith(".m3u"):
        self._exec_cmd("LOADLIST 0 %s" % url)
      else:
        if elapsed > 0:
          self._exec_cmd("LOADPAUSED %s" % url)
          self._exec_cmd("JUMP %ss" % elapsed)
          self._exec_cmd("SAMPLE")
          self._exec_cmd("PAUSE")
        else:
          self._exec_cmd("LOAD %s" % url)
          self._exec_cmd("SAMPLE")
      return True
    else:
      return False

  # --- stop playing current URL/file   ---------------------------------------

  def stop(self,last=True):
    """ stop playing """

    if not self._play:
      return
    if self._process:
      self.msg("Mpg123: stopping current url/file: %s" % self._url)
      self._last = last
      self._exec_cmd("STOP")
      self._elapsed   = 0

  # --- pause playing   -------------------------------------------------------

  def pause(self):
    """ pause playing """

    if not self._url or self._pause:
      return
    if self._process:
      self.msg("Mpg123: pausing playback")
      if not self._pause:
        self._exec_cmd("PAUSE")
        self._exec_cmd("SAMPLE")

  # --- continue playing   ----------------------------------------------------

  def resume(self):
    """ continue playing """

    if not self._play and not self._pause:
      return
    if self._process:
      self.msg("Mpg123: resuming playback")
      if self._pause:
        self._exec_cmd("PAUSE")

  # --- toggle playing   ------------------------------------------------------

  def toggle(self):
    """ toggle playing """

    if not self._play:
      return
    if self._process:
      self.msg("Mpg123: toggle playback")
      self._exec_cmd("PAUSE")
      self._exec_cmd("SAMPLE")

  # --- stop player   ---------------------------------------------------------

  def destroy(self):
    """ destroy current player """

    if self._process:
      self.msg("Mpg123: stopping mpg123 ...")
      try:
        self._exec_cmd("QUIT",wait=False)
        self._process.wait(5)
        self.msg("Mpg123: ... done")
      except:
        # can't do anything about it
        self.msg("Mpg123: ... exception during destroy of mpg123")
        pass

  # --- jump to position   ----------------------------------------------------

  def jump(self,elapsed):
    """ jump to specified absolute position (elapsed time in seconds) """

    self._exec_cmd("JUMP %ss" % str(elapsed))
    self._exec_cmd("SAMPLE")

  # --- execute mpg123-command   ----------------------------------------------

  def _exec_cmd(self,cmd,wait=True):
    """ execute mpg123-command """

    self._op_event.clear()
    self._process.stdin.write(cmd+"\n")
    if wait:
      self._op_event.wait()

  # --- process output of mpg123   --------------------------------------------

  def _process_stdout(self):
    """ read mpg123-output and process it """

    self.msg("Mpg123: starting mpg123 reader-thread")
    regex = re.compile(r".*ICY-META.*?'([^']*)';?.*\n")
    while True:
      try:
        line = self._process.stdout.readline()
        if not line:
          break;
      except:
        # catch e.g. decode-error
        continue
      if line.startswith("@F"):
        continue
      self.msg("Mpg123: processing line: %s" % line)
      if line.startswith("@I ICY-META"):
        (line,_) = regex.subn(r'\1',line)
        self._api._push_event({'type': 'icy_meta',
                              'value': line})
      elif line.startswith("@I ICY-NAME"):
        self._api._push_event({'type': 'icy_name',
                              'value': line[13:].rstrip("\n")})
      elif line.startswith("@P 0"):
        # @P 0 is not reliable
        if self._play:
          self._api._push_event({'type': 'eof',
                                 'value': {'name': self._url,
                                           'last': self._last}})
          self._url     = None
          self._pause   = False
          self._play    = False
          self._elapsed = 0
          self._op_event.set()
      elif line.startswith("@P 1"):
        self._pause = True
        self._api._push_event({'type': 'pause',
                              'value': self._url})
        self._op_event.set()
      elif line.startswith("@P 2"):
        self._play  = True
        self._pause = False
        self._api._push_event({'type': 'play',
                              'value': self._url})
        self._op_event.set()
      elif line.startswith("@SAMPLE"):
        sample = line.split()
        if int(sample[2]) > 0:
          self._elapsed = int(sample[1])/int(sample[2])
        else:
          self._elapsed = 0
        self._api._push_event({'type': 'sample',
                              'value': {'elapsed': self._elapsed,
                                        'pause': self._pause}})
        self._op_event.set()
      elif line.startswith("@J"):
        self._op_event.set()

    self.msg("Mpg123: stopping mpg123 reader-thread")

  # --- increase volume   ----------------------------------------------------

  def vol_up(self,by=None):
    """ increase volume by amount or the pre-configured value """

    if by:
      amount = max(0,int(by))     # only accept positive values
    else:
      amount = self._vol_delta        # use default
    self._volume = min(100,self._volume + amount)
    return self.vol_set(self._volume)

  # --- decrease volume   ----------------------------------------------------

  def vol_down(self,by=None):
    """ decrease volume by amount or the pre-configured value """

    if by:
      amount = max(0,int(amount))     # only accept positive values
    else:
      amount = self._vol_delta        # use default
    self._volume = max(0,self._volume - amount)
    return self.vol_set(self._volume)

  # --- set volume   ---------------------------------------------------------

  def vol_set(self,val):
    """ set volume """

    val = min(max(0,int(val)),100)
    self._volume = val
    if self._process:
      self.msg("Mpg123: setting current volume to: %d%%" % val)
      self._exec_cmd("VOLUME %d" % val,wait=False)
      self._api._push_event({'type': 'vol_set',
                              'value': self._volume})
      return self._volume

  # --- mute on  -------------------------------------------------------------

  def vol_mute_on(self):
    """ activate mute (i.e. set volume to zero) """

    if not self._mute:
      self._vol_old = self._volume
      self._mute    = True
      return self.vol_set(0)

  # --- mute off  ------------------------------------------------------------

  def vol_mute_off(self):
    """ deactivate mute (i.e. set volume to last value) """

    if self._mute:
      self._mute = False
      return self.vol_set(self._vol_old)

  # --- mute toggle   --------------------------------------------------------

  def vol_mute_toggle(self):
    """ toggle mute """

    if self._mute:
      return self.vol_mute_off()
    else:
      return self.vol_mute_on()
