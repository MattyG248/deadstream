#!/usr/bin/python3
import optparse
from deadstream import GD
from deadstream import controls as ctl
import config
from time import sleep
import logging
import signal

logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)s: %(message)s', level=logging.INFO,datefmt='%Y-%m-%d %H:%M:%S')
#logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

parser = optparse.OptionParser()
parser.add_option('--debug',dest='debug',default=True)
parser.add_option('--verbose',dest='verbose',default=False)
parms,remainder = parser.parse_args()


meInterrupt = False
def meCustomHandler(signum,stack_frame):
   global meInterrupt
   print('encountered ctrl+C - here before the process exists')
   meInterrupt= True

signal.signal(signal.SIGINT, meCustomHandler)

def play_tape(tape,player):
    logging.info(F"Playing tape {tape}")
    player.insert_tape(tape)
    player.play()
    return player

def meLoop(knobs,a,scr,player,maxN=None):
    y,m,d = knobs
    play_state = config.PLAY_STATE
    d0 = (ctl.date_knob_reader(y,m,d,a)).date
    N = 0

    while N<=maxN if maxN != None else True:
      staged_date = ctl.date_knob_reader(y,m,d,a)
      if meInterrupt: return player,play_state
      # deal with DATE changes
      N = N+1
      if staged_date.date != d0:  # Date knobs changed
         logging.info (F"DATE: {config.DATE}, SELECT_DATE: {config.SELECT_DATE}, PLAY_STATE: {config.PLAY_STATE}")
         print (staged_date)
         d0 = staged_date.date
         scr.show_date(staged_date.date,tape=staged_date.tape_available())
    #     if staged_date.tape_available(): 
    #        venue = staged_date.venue()
    #        scr.show_text(venue)
    #     else:
    #        scr.draw.rectangle((0,0,160,32),outline=0,fill=(0,0,0)) # erase the venue
    #        scr.disp.image(scr.image)
      if config.SELECT_DATE:   # Year Button was Pushed
         if staged_date.tape_available():
            config.DATE = staged_date.date 
            logging.info(F"Setting DATE to {config.DATE}")
            config.PLAY_STATE = config.READY  #  eject current tape, insert new one in player
            scr.show_date(config.DATE,loc=(85,0),size=10,color=(255,255,255),stack=True,tape=True)
         config.SELECT_DATE = False

      # Deal with PLAY_STATE changes

      #PLAY_STATE = config.PLAY_STATE

      if (config.PLAY_STATE == play_state): sleep(0.1); continue
      if (config.PLAY_STATE == config.READY):  #  A new tape to be inserted
         player.eject_tape()
         tape = a.best_tape(config.DATE.strftime('%Y-%m-%d'))
         player.insert_tape(tape)
         config.PLAY_STATE = config.PLAYING
      if (config.PLAY_STATE == config.PLAYING):  # Play tape 
         try:
           logging.info(F"Playing {config.DATE} on player")
           tape = a.best_tape(config.DATE.strftime('%Y-%m-%d'))
           if len(player.playlist) == 0: player = play_tape(tape,player)  ## NOTE required?
           else: player.play()
           play_state = config.PLAYING
           scr.show_playstate('playing')
         except AttributeError:
           logging.info(F"Cannot play date {config.DATE}")
           pass
         except:
           raise 
         finally:
           config.PLAY_STATE = play_state
      if config.PLAY_STATE == config.PAUSED: 
         logging.info(F"Pausing {config.DATE.strftime('%Y-%m-%d')} on player") 
         player.pause()
      if config.PLAY_STATE == config.STOPPED:
         player.stop()
         scr.show_playstate('paused')
      play_state = config.PLAY_STATE
      sleep(.1)
    return (player,play_state)

def main(parms):
    player = GD.GDPlayer()

    y = ctl.knob(config.year_pins,"year",range(1965,1996),1979)   # cl, dt, sw
    m = ctl.knob(config.month_pins,"month",range(1,13),11)
    d = ctl.knob(config.day_pins,"day",range(1,32),2,bouncetime=100)

    _ = [x.setup() for x in [y,m,d]]

    logging.info ("Loading GD Archive")
    a = GD.GDArchive('/home/steve/projects/deadstream/metadata')
    logging.info ("Done ")

    staged_date = ctl.date_knob_reader(y,m,d,a)
    print (staged_date)

    scr = ctl.screen()
    scr.clear()
    scr.show_date(staged_date.date,tape=staged_date.tape_available())
    #scr.show_text(staged_date.venue())
    try:
      player,play_state = meLoop((y,m,d),a,scr,player)   # ,maxN=50)
    finally:
      print("In Finally")
      [x.cleanup() for x in [y,m,d]] ## redundant, only one cleanup is needed!

main(parms)
