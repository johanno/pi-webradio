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

<div id="wr_play" style="height: 100%; display: none" class="content_area">
  <div class="play">                   <!-- flex-row with two columns -->
    <div class="play_left">            <!-- first column              -->
      <div class="clock play_clock">
        <i>14:42</i>
      </div>
      <div class="play_img">
        <img id="wr_play_logo" src="/images/default.png"/>
        <div id="wr_play_name" class="play_name"></div>
      </div>
      <div class="play_buttons">
        <a href="#" onclick="radio_on()">
                <i id="wr_on_btn" class="fas fa-play-circle"></i></a>
        <a href="#" onclick="radio_toggle()">
                <i id="wr_pause_btn" class="fas fa-pause-circle"></i></a>
        <a href="#" onclick="radio_off()">
                <i id="wr_off_btn" class="fas fa-stop-circle"></i></a>
        <a href="#" onclick="vol_mute_toggle()">
                <i id="wr_mute_btn" class="fas fa-volume-mute"></i></a>
        <a href="#" onclick="rec_toggle()">
                <i id="wr_rec_btn" class="fas fa-dot-circle"></i></a>
      </div>
    </div>
    <div id="wr_infos" class="play_info">    <!-- second column            -->
    </div>
  </div>
</div>

<script>
get_events();
</script>