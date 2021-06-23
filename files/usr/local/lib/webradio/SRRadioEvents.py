#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Pi-Webradio: implementation of class RadioEvents
#
# The class RadioEvents multiplexes events to multiple consumers.
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/pi-webradio
#
# -----------------------------------------------------------------------------

import queue
import threading

from webradio import Base

class RadioEvents(Base):
  """ Multiplex events to consumers """

  def __init__(self,app):
    """ initialization """

    self._api         = app.api
    self._debug       = app._debug
    self._stop_event  = app.stop_event
    self._input_queue = queue.Queue()
    self._consumers   = {}
    self.register_apis()
    threading.Thread(target=self._process_events).start()

  # --- register APIs   ------------------------------------------------------

  def register_apis(self):
    """ register API-functions """

    self._api.push_event   = self.push_event
    self._api.add_consumer = self.add_consumer
    self._api.del_consumer = self.del_consumer

  # --- push an event to the input queue   -----------------------------------

  def push_event(self,event):
    """ push event to the  input queue """

    self._input_queue.put(event)

  # --- add a consumer   -----------------------------------------------------

  def add_consumer(self,id,queue):
    """ add a consumer to the list of consumers """

    if not id in self._consumers:
      self._consumers[id] = queue

  # --- remove a consumer   --------------------------------------------------

  def del_consumer(self,id):
    """ delete a consumer from the list of consumers """

    if id in self._consumers:
      del self._consumers[id]

  # --- multiplex events   ---------------------------------------------------

  def _process_events(self):
    """ pull events from the input-queue and distribute to the consumer queues """

    self.debug("starting event-processing")
    while not self._stop_event.is_set():
      try:
        event = self._input_queue.get(block=True,timeout=1)   # block 1s
      except queue.Empty:
        continue
      self.debug("received event: %r" % (event,))
      for consumer in self._consumers.values():
        consumer.put(event)
      self._input_queue.task_done()

    self.debug("stopping event-processing")
    for consumer in self._consumers.values():
      consumer.put(None)