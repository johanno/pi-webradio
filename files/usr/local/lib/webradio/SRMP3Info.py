#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Pi-Webradio: implementation of helper class MP3Info
#
# The class MP3Info collects and caches MP3-infos of the files of a directory.
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/pi-webradio
#
# -----------------------------------------------------------------------------

import os, subprocess, json

from webradio import Base

class MP3Info(Base):
  """ query MP3-info from files """

  def __init__(self,app):
    """ constructor """

    self.debug   = app.debug

  # --- pretty print duration/time   ----------------------------------------

  def _pp_time(self,seconds):
    """ pritty-print time as mm:ss or hh:mm """

    m, s = divmod(seconds,60)
    h, m = divmod(m,60)
    if h > 0:
      return "{0:02d}:{1:02d}:{2:02d}".format(h,m,s)
    else:
      return "{0:02d}:{1:02d}".format(m,s)

  # --- create file info for a given file   ----------------------------------

  def get_fileinfo(self,dir,file):
    """ create file info """

    if os.path.isabs(file):
      f = file
    else:
      f = os.path.join(dir,file)
    mp3info = subprocess.check_output(
      ["mp3info","-p","%S\n%a\n%c\n%l\n%n\n%t",f])
    #                  total
    #                      artist
    #                          comment
    #                              album
    #                                  track
    #                                      title

    # as fallback, assume file = "artist - title.mp3"
    ind = file.find('-')
    if ind > 0:
      artist = file[:ind-2]
      title  = file[ind+2:len(file)-5]
    else:
      artist = ""
      title  = ""

    try:
      mp3info = mp3info.decode("utf-8")
    except:
      mp3info = mp3info.decode("iso-8859-1")

    #tokenize and convert
    tokens = mp3info.split("\n")
    info                 = {} 
    info['fname']        = file
    info['total']        = int(tokens[0])
    info['total_pretty'] = self._pp_time(info['total'])
    try:
      info['artist']       = tokens[1]
    except:
      info['artist']       = artist
    try:
      info['comment']      = tokens[2]
    except:
      info['comment']      = ""
    try:
      info['album']        = tokens[3]
    except:
      info['album']        = ""
    try:
      info['track']        = int(tokens[4])
    except:
      info['track']        = 1
    try:
      info['title']        = tokens[5]
    except:
      info['title']        = title
    self.msg("MP3Info: file-info: %s" % json.dumps(info))
    return info

  # --- create directory info for given dir   --------------------------------

  def get_dirinfo(self,dir,force_save=False):
    """ return directory info """

    info_file = os.path.join(dir,".dirinfo")
    mtime_dir = os.path.getmtime(dir)
    if os.path.exists(info_file) and mtime_dir <= os.path.getmtime(info_file):
      try:
        f = open(info_file,"r")
        dirinfo = json.load(f)
        close(f)
        self.msg("MP3Info: using dir-info file %s" % info_file)
        return dirinfo
      except:
        self.msg("MP3Info: could not load dir-info file %s" % info_file)

    dirinfo = self._create_dirinfo(dir)
    # only update dirinfo-file if it already existed before
    if os.path.exists(info_file) or force_save:
      try:
        f = open(info_file,"w")
        json.dump(dirinfo,f,indent=2)
        f.close()
        self.msg("MP3Info: updating dir-info file %s" % info_file)
      except:
        self.msg("MP3Info: could not update dir-info file %s" % info_file)
    return dirinfo

  # --- create directory info for given dir   --------------------------------

  def _create_dirinfo(self,dir):
    """ create directory info """

    dirinfo = {'dirs':  [], 'files': []}
    files   = []
    self.msg("MP3Info: collecting dir-info for %s" % dir)

    for f in os.listdir(dir):
      if os.path.isfile(os.path.join(dir,f)):
        if f.endswith(".mp3"):
          files.append(f)
      else:
        dirinfo['dirs'].append(f)

    # ... and sort results
    files.sort()
    dirinfo['dirs'].sort()

    # add add time and mp3-info
    for f in files:
      dirinfo['files'].append(self.get_fileinfo(dir,f))

    return dirinfo