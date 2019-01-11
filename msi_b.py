# -*- coding: utf-8 -*-

# msi part B
# Jan 10 2019
# Main run for EEG recording
# Audio delay now compensated for within ~4ms 

#To do: counterbalance response key based on participant number?

#DO NOT CHANGE - audio library and driver setup
from psychopy import prefs
prefs.general['audioLib'] = ['pyo']
prefs.general['audioDriver'] = ['ASIO']
prefs.general['audioDevice'] = ['Speakers (Creative SB X-Fi)']


import numpy as np
import pandas as pd
import os, sys
from psychopy import visual, core, event, gui, logging, sound
import random
import matplotlib.pyplot as plt
import csv
import pandas as pd
from datetime import datetime


#system setup
framerate = 100 #For debugging purposes only. Must be 100 for data collection 

if framerate != 100:
    print("Warning: framerate not set to 100 Hz")

#get Subject ID
subgui = gui.Dlg() 
subgui.addField("Subject ID:")
subgui.show()
subj = subgui.data[0]

#check for existing SOA file and make experimenter manually verify correct file based on timestamp
SOA_filename = 'data' + os.sep + 'SOAs' + os.sep + 'msi_a_sub' + str(subj) + '_SOAs.csv'

if not os.path.isfile(SOA_filename):
    sys.exit("SOAs not found")
else:
    dategui = gui.Dlg()
    dategui.addText("SOA file for sub" + subj + " created " + str(datetime.fromtimestamp(os.path.getmtime(SOA_filename))) + ". Proceed?")
    dategui.show()
    
    if dategui.OK:
        pass
    else:
        sys.exit()

#get SOAs and assign to list of the form ['label', duration]
SOAs = pd.read_csv(SOA_filename)
ASOA50r = ['ASOA50r', int(SOAs.ASOA50r[0])]
ASOA95r = ['ASOA95r', int(SOAs.ASOA95r[0])]
VSOA50r = ['VSOA50r', int(SOAs.VSOA50r[0])]
VSOA95r = ['VSOA95r', int(SOAs.VSOA95r[0])]
A10 = ['A10', -10]
V10 = ['V10', 10]

#setup
win = visual.Window(fullscr=True, allowGUI=False, color="black", screen=0, units='height', waitBlanking=True)
trialClock = core.Clock()
all_responses = []

num_blocks = 4
#SOA_list= 4*[-30, -25, -20, -15, -10, -8, -5, -2, -1, 0, 1, 2, 5, 8, 10, 15, 20, 25, 30] # SOA (in number of frames)
SOA_list = 32*[ASOA50r, VSOA50r] + 16*[ASOA95r, A10, V10, VSOA95r]

#check for existing subject file
outputFileName = 'data' + os.sep + 'msi_b' + os.sep + 'msi_b_sub' + subj + '.csv' 
if os.path.isfile(outputFileName) :
    sys.exit("Data for this subject already exists")

#setup log file
logFile = 'data' + os.sep + 'logfiles' + os.sep + 'msi_b' + os.sep + 'msi_b_sub' + subj + '_log.csv'

#check refresh rate
actual_framerate = win.getActualFrameRate(nIdentical=100, nMaxFrames=1000,
    nWarmUpFrames=10, threshold=1)
if actual_framerate < framerate - 0.15 or actual_framerate >  framerate + 0.15:
    sys.exit("Expected refresh rate: " + str(framerate) + ". Actual rate: " + str(actual_framerate))

#create beep stimulus
beep = sound.Sound('C:/data/pjohnston/msi/audiocheck.net_sin_3500Hz_0dBFS_1s', stop = 0.01, stereo=True)
beep.setVolume(1)

#create flash stimulus (diameter 4cm = 3.8 degrees of visual angle at 60 cm)
flash = visual.RadialStim(win, size = 0.15, radialCycles = 1, radialPhase = 1/2, 
                                angularPhase = 1/4, angularCycles = 1/2)

#create fixation
fixation = visual.TextStim(win, text = "+", color = "white", height = 0.06)


#intstruction screen
instructions = visual.TextStim(win, text = u"""You will hear a beep and see a flash. When prompted, please use the left and right arrow keys to report whether they occur simultaneously or not. Press any key to begin.
                                                       ← = NO              → = YES""", height = 0.075, pos = (0,0))
start_prompt = visual.TextStim(win, text = "Press any key to begin", height = -0.075)
instructions.draw()
win.flip()
event.waitKeys()

block_count = 0

#run
for block in range(num_blocks):
    random.shuffle(SOA_list)
    block_count += 1
    
    if block_count != 1:
        
        #prompt any key
        break_prompt = visual.TextStim(win, text = """                Break           
                                                            Press any key to continue""", height = 0.075)
        break_prompt.draw()
        win.flip()
        event.waitKeys()
    
    trial_count = 0
    
    for SOA in SOA_list:

        corrected_SOA = (SOA[1]/10)-1 #divide by 10 and correct for 10ms audio lag
        trial_count += 1
        
        fixation.draw()
        win.flip()
        #trigger fixation start here
        
        #jitter initial fixation
        jitter = random.randint(100,150)
        for frameN in range(jitter):
            fixation.draw()
            win.flip()
        
        core.rush(True) #give psychopy priority during stimulus presentation
        
        fixation.draw()
        win.flip()
        
        if corrected_SOA < 0: #auditory then visual
            
            #beep
            beep.play()
            
            #SOA
            for frameN in range(-1*corrected_SOA):
                fixation.draw()
                win.flip()
            
            #flash
            flash.draw()
            fixation.draw()
            win.flip()
            #trigger here
            fixation.draw()
            win.flip()
            
        elif corrected_SOA == 0: #simultaneous
            beep.play()
            flash.draw()
            fixation.draw()
            win.flip()
            #trigger here
            fixation.draw()
            win.flip()
            
        else: #visual then auditory (this coding would logically give 10ms less than expected, but it checks out with the oscilloscope?)
            
            #flash
            flash.draw()
            fixation.draw()
            win.flip()
            #trigger here
            
            #SOA
            for frameN in range(corrected_SOA-1):
                fixation.draw()
                win.flip()
            
            #beep
            beep.play()
            fixation.draw()
            win.flip()
            
        core.rush(False)
        core.wait(0.75)
        
        #collect response
        prompt = visual.TextStim(win, text = "Simultaneous?", height = 0.073, pos = (0, 0.15))
        key_prompt = visual.TextStim(win, text = "   NO                              YES   ", height = 0.073, pos = (0, -0.3))
        prompt.draw()
        key_prompt.draw()
        win.flip()
        trialClock.reset()
        keys = event.waitKeys(timeStamped=trialClock, keyList = ['left', 'right', 'escape', 'ctrl'], maxWait = 2)
        
        if keys == None: # check for no response
            keys=[['NaN', 'NaN']]
        elif keys[0][0] == 'escape': #data saves on quit
            win.close()
            df = pd.DataFrame(all_responses)
            df.columns = ['subj', 'block', 'trial', 'SOA_label', 'SOA', 'resp', 'rt']
            df.to_csv(outputFileName)
            core.quit()
            
        trial_responses = [subj, block + 1, trial_count, SOA[0], SOA[1], keys[0][0], keys[0][1]]
        all_responses.append(trial_responses)
        
        #write to log file
        with open(logFile, 'a') as fd:
            wr = csv.writer(fd, dialect='excel')
            wr.writerow(trial_responses)
            
        win.flip()
        core.wait(0.75) #ITI

#thank you screen
thank_you = visual.TextStim(win, text = "Thanks for participating!", height = 0.06)
thank_you.draw()
win.flip()
event.waitKeys()

win.close()

df = pd.DataFrame(all_responses)
df.columns = ['subj', 'block', 'trial', 'SOA_label', 'SOA', 'resp', 'rt']
df.to_csv(outputFileName)

