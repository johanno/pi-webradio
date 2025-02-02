<!--
# ----------------------------------------------------------------------------
# Web-interface for pi-webradio.
#
# This file defines the content page for an active playing channel/file
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/pi-webradio
#
# ----------------------------------------------------------------------------
-->

<div id="tab_play" style="height: inherit; display: none" class="content_area">
  <div class="play">                   <!-- flex-row with two columns -->
    <div class="play_left">            <!-- first column              -->
      <div class="clock play_clock">
        <i>14:42</i>
      </div>
      <div class="play_img">
        <img id="wr_play_logo" style="max-height: 200px"
                                                src="/images/default.png"/>
        <div id="wr_play_name" class="play_name"></div>
      </div>
      <div class="play_buttons">
        <a href="#" onclick="audio_toggle()">
                <i id="wr_pause_btn" class="fas fa-pause-circle"></i></a>
        <a href="#" onclick="audio_off()">
                <i id="wr_off_btn" class="fas fa-stop-circle"></i></a>
        <a href="#" onclick="rec_toggle()">
                <i id="wr_rec_btn" class="fas fa-dot-circle"></i></a>
      </div>
      <div class="play_buttons">
        <a href="#" onclick="vol_up()">
                <i id="wr_volup_btn" class="fas fa-volume-up"></i></a>
        <a href="#" onclick="vol_mute_toggle()">
                <i id="wr_mute_btn" class="fas fa-volume-mute"></i></a>
        <a href="#" onclick="vol_down()">
                <i id="wr_voldown_btn" class="fas fa-volume-down"></i></a>
      </div>
    </div>
    <div id="wr_info_column" class="play_right">       <!-- second column  -->

      <!-- in radio mode   ----------------------------------------------  -->

      <div id="wr_radio" class="play_radio"></div>    <!-- info area      -->

      <!-- in player mode   ---------------------------------------------  -->

      <div id="wr_player" class="play_player">
        <div id="wr_artist"  class="id3_artist"></div>
        <div id="wr_title"   class="id3_title"></div>
        <div id="wr_album"   class="id3_album"></div>
        <div id="wr_comment" class="id3_comment"></div>
      </div>
      <div id="wr_time" class="play_time">           <!-- current/total  -->
        <div id="wr_track" class="play_track"></div>
        <div id="wr_time_cur" class="play_time_cur"></div>
        <input id="wr_time_range" type="range" class="play_time_range"
               min="0" max="100" onchange="player_set_pos()"></input>
        <div id="wr_time_tot" class="play_time_tot"></div>
        <div id="wr_track_total" class="play_track_total"></div>
      </div>
    </div>
  </div>
</div>
