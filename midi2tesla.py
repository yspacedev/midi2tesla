import numpy as np
import simpleaudio as sa

fs = 44100  # 44100 samples per second
"""
import sys
path=sys.argv[0]
midi=sys.argv[1]
savewav=sys.argv[2]
doplaymusic=sys.argv[3]
"""
path="./input"
midi="popcorn"
savewav=midi #output file name
doplaymusic=True #play sound after conversion

#more advanced playback settings
savefiletype="mp3"
dosavewav=True
pulseCorrectionFactor=1 #affects pulse width. Usually pulse width is equal to note velocity in microseconds, but this can adjust that
selectedtracksind=[-1] #select indices of tracks to include; -1 indicates all tracks
pulseDuration = 100

#tempo stuff
tempo=500000 #initial tempo. Usually overridden unless tempoAutoset is False
tempoAutoset=True
tempoCorrectionFactor=16 #have no idea why this has to exist. But often tempo is slower or faster than it should be and it requires a correction factor.
maxmidiind=10000 #in case you only want a portion of the midi

#moving avg duty cycle limiter
maxduty=0.5
minduty=0
windowsize=1000

#deprecated
maxpulselen=int((500/1000000)*fs) #max pulse len before turning off output
timeoutlen=int((100/1000000)*fs) #after max pulse len exceeded, cooldown for this amount of samples
#has been replaced by moving average duty cycle-based limiting


def writeWav(data):
    import soundfile as sf
    sf.write(f'{path}output/{savewav}.{savefiletype}', data, fs)
def ticks2samples(ticks):
   return int((fs/(1000000*tempoCorrectionFactor))*tempo*(ticks/(24)))

print(f"converting {midi}.mid to {savewav}.{savefiletype}")

time=0
tones=[]
class tone:
  frequency=0
  pulseWidth=0
  period=0
  note=0
  time = 0
  MIDI_NOTE_TO_FREQUENCY = 440 * 2 ** ((-9) / 12)  # MIDI note 69 (A4) frequency (ChatGPT'd)
  def __init__(self, tone, pulseWidth): #startTime will be timestamp to start
    self.note=tone
    self.frequency=self.MIDI_NOTE_TO_FREQUENCY * 2 ** ((tone - 69) / 12) #ChatGPT'd
    self.period=int(((1/self.frequency)*fs)/2) #period in samples. Dividing by 2 works for some reason
    self.pulseWidth=int((pulseWidth/1000000)*fs) #pulse width in samples
    self.pulse=np.concatenate((np.ones(self.pulseWidth), np.zeros(self.period-self.pulseWidth))).tolist() # single pulse
    #print(self.period)
  def generate(self, gentime): #generate for a certain amount of time (in samples)
    numperiods=int(gentime/self.period)+2 #the +2 is necessary
    pulses=self.pulse*numperiods #generate a train of pulses
    inittime=(self.time%self.period) #time in pulsetrain to start at (which is the index in a single pulse the last pulse started at)
    final=np.array(pulses[inittime:gentime+inittime]) #slice to get gentime long list and turn into numpy array
    self.time+=gentime #update self.time
    return final

def findInTones(note):
   for ind in range(len(tones)):
      if tones[ind].note==note: #could be sped up
         return ind

def playmusic(music):
    dt=time.monotonic()
    audio = music * (2**15 - 1)
    # Convert to 16-bit data
    audio = audio.astype(np.int16)

    # Start playback
    play_obj = sa.play_buffer(audio, 1, 2, fs)

    # Wait for playback to finish before exiting
    play_obj.wait_done()
    print(f"song done in {time.monotonic()-dt} seconds")


from mido import MidiFile
mid = MidiFile(f"{path}/{midi}.mid", clip=True)
time=0
temposet=False #whether tempo has been set
for track in mid.tracks:
    for msg in track[:min((len(track), 10))]:
        if msg.type=='set_tempo':
            if tempoAutoset and not temposet:
                temposet=True
                tempo=msg.tempo #comment out if tempo is completely wrong
        if msg.type=='time_signature':
            print(msg)






import time
dt=time.monotonic()
biggestTrack=max(mid.tracks, key=len)
bigLen=len(biggestTrack)
currSampTime=0
#preprocessing midi to convert all tracks into one

selectedtracks=[]
if selectedtracksind==[]:
    selectedtracks.append(biggestTrack)
elif selectedtracksind==[-1]:
    selectedtracks=mid.tracks
else:
    for trackind in selectedtracksind:
        selectedtracks.append(mid.tracks[trackind])


absTickTimes=np.zeros(len(selectedtracks)).tolist() #stores the absolute (not relative) tick value for each track
megatrack=[]
completed=False
ind=0
while ind<=bigLen:
    for trackind, track in enumerate(selectedtracks):
        if (ind+1)<=len(track):
            #do some list manipulation
            #print(track[ind])
            absTickTimes[trackind]+=track[ind].time
            newobj=track[ind]
            newobj.time=absTickTimes[trackind]
            megatrack.append(newobj)
    ind+=1

megatrack = sorted(megatrack, key=lambda x: x.time)
#this midi object now has times stored as absolute times not relative times.



totalsamples=int(ticks2samples(megatrack[-1].time)+windowsize) #sum total number of samples
music=np.zeros(totalsamples) #placeholder array to be filled by samples. Much more efficient than np.append()
absTime=0
bigLen=len(megatrack)
for ind, msg in enumerate(megatrack[:maxmidiind]): #will add multiple tracks later
    if msg.type=='note_on' or msg.type=='note_off':
        if ind%100==0:
            print(f"processed {ind}/{bigLen} commands")
            pass
        genTime=ticks2samples(msg.time-absTime) #convert to samples WARNING: midi time is in absolute time rather than relative, so it will not process normal midi that has not run through preprocessing without modification
        music[currSampTime:currSampTime+genTime]=np.where(sum([tone.generate(genTime) for tone in tones]) > 0, 1, 0) #maybe could cut down on compute by replacing sum with something
        #for more advanced polyphony, modify the sum() and tone.generate (probably mess with the offset time)
        currSampTime+=genTime
        absTime+=msg.time-absTime
        if msg.type=='note_on':
           #can use msg.velocity*pulseCorrectionFactor for pulse duration
           tones.append(tone(msg.note, pulseDuration)) #append note to current note playing
        if msg.type=='note_off':
            tonetoremove=findInTones(msg.note)
            if tonetoremove is not None:
                tones.pop(tonetoremove) #remove note once it stops playing
        if msg.type=='tempo':
           tempo=msg.tempo

print(f"postprocessing {len(music)} elements to limit duty cycle to {maxduty*100}%: ")
#postprocess
#window=np.zeros(windowsize)
def movingavg(data, window): #ChatGPT'd
    # Create a simple moving average kernel
    kernel = np.ones(window) / window
    # Use np.convolve to compute the moving average
    return np.convolve(data, kernel, mode='valid')
avg=movingavg(music, windowsize)
music=np.where((avg>=maxduty) | (avg<=minduty), 0, music[:-windowsize+1])


print(f'{len(music)/fs} seconds')
print(f'in {len(music)} samples')
print(f'with tempo: {tempo}')
print(f"conversion completed in {time.monotonic()-dt} seconds")
if dosavewav:
    print(f"saving file as {savewav}.{savefiletype}")
    writeWav(music)
if doplaymusic:
    print(f"playing music...")
    playmusic(music)
