import numpy as np
import simpleaudio as sa

#high-level overview
#get midi parameters (tempo, PPQ, etc) -> merge all tracks into megatrack -> run generation to generate pulses -> postprocess -> export

#example usage: python midi2tesla.py --folder --reference_path . -c 16 "<midi>.mid"
#CLI parsing:
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("input")
parser.add_argument("-p", "--reference_path")
parser.add_argument("-o", "--output")
parser.add_argument("-f", "--folder", action="store_true") #use input and output folders
parser.add_argument("-s", "--no_save_file", action="store_true")
parser.add_argument("-m", "--play_music", action="store_true")
parser.add_argument("-d", "--duty_cycle", action="store_true")

args = parser.parse_args()

fs = 44100  # 44100 samples per second

path=""
if (args.reference_path!=None):
    path=args.reference_path
midi=args.input
savewav=midi #output file name
if (args.output!=None):
    savewav=args.output
doplaymusic=args.play_music #play sound after conversion
inpath=path
outpath=path
if (args.folder):
    inpath=path+"/input/"
    outpath=path+"/output/"

midiName=midi.split("/")[-1]
saveName=savewav.split("/")[-1]

#more advanced playback settings
savefiletype="mp3"
A4ref=440 #A4 reference in case you want to change to a different reference frequency
dosavewav = not args.no_save_file
pulseCorrectionFactor=1 #affects pulse width. Usually pulse width is equal to note velocity in microseconds, but this can adjust that
selectedtracksind=[-1] #select indices of tracks to include; -1 indicates all tracks
maxPulseDuration = 10 #in samples
minPulseDuration = 3
maxDutyCycle = 3 #maximum duty cycle per pulse, varied depending on note velocity
if (args.duty_cycle!=None):
    maxDutyCycle=args.duty_cycle
#some notes about pulse length and duty cycle. Lower duty cycle means more notes can be played without is ounding bad, but it reduces the apparent volume. Might be good to make it logarithmic since I don't thnk the correlation between volume and pulse width is linear
#there isn't really one setting that will work well for every song. Some songs require longer duty cycles and higher pulse widths to sound good, and others will just sound like noise without an extremely low duty cycle.

#tempo stuff
tempo=500000 #initial tempo. Usually overridden unless tempoAutoset is False
tempoAutoset=True


maxmidiind=-1 #in case you only want a portion of the midi

#moving avg duty cycle limiter
maxduty=1
minduty=0
windowsize=1000

#deprecated
maxpulselen=int((500/1000000)*fs) #max pulse len before turning off output
timeoutlen=int((100/1000000)*fs) #after max pulse len exceeded, cooldown for this amount of samples
#has been replaced by moving average duty cycle-based limiting though it might be brought back as this is more relevant for Tesla coils


def writeWav(data):
    import soundfile as sf
    sf.write(f'{outpath}{savewav}.{savefiletype}', data, fs)
def ticks2samples(ticks):
   return int((ticks/ticksPerBeat)*(tempo/1000000)*fs) #fixed tempo issue

print(f"converting {midi} to {savewav}.{savefiletype}")

time=0
tones=[]
class tone: #class containing tone generator and other tone playing information
    frequency=0
    pulseWidth=0
    period=0
    note=0
    time = 0
    pitch = 0
    channel=0
    velocity=0
    def __init__(self, tone, velocity, channel): #startTime will be timestamp to start #TODO: add pitch bend and continuous amplitude (pulse width) adjustment functions 
        self.note=tone
        self.velocity=velocity
        self.channel=channel
        self.frequency=A4ref * 2 ** ((tone - 69) / 12) #ChatGPT'd
        self.setFreq(self.frequency) #generate and calculate all the things
    #print(self.period)
    def changePitch(self, newPitch): #for pitch bending functionality
        self.pitch=newPitch
        bend_ratio = (newPitch) / 4096 #allow 2 semitones up or down
        adjusted_note_number = self.note + bend_ratio
        self.frequency = A4ref * (2 ** ((adjusted_note_number-69) / 12))
        self.setFreq(self.frequency)
        return
    def setFreq(self, freq):
        self.period=int(((1/freq)*fs)/2) #period in samples. Dividing by 2 works for some reason
        self.pulseWidth=int((self.velocity/127)*(maxDutyCycle/100)*self.period) #convert velocity to duty cycle (fraction of 1) then multiply by period to get the pulsewidth information
        #adding an offset/minimum on time can help balance out the relative strength of notes
        #should change this to make adjustment have a more continuous range
        if self.pulseWidth>maxPulseDuration:
            self.pulseWidth=maxPulseDuration
        if self.pulseWidth<minPulseDuration:
            self.pulseWidth=minPulseDuration
        self.pulse=np.concatenate((np.ones(self.pulseWidth), np.zeros(self.period-self.pulseWidth))).tolist() # single pulse
    def generate(self, gentime): #generate for a certain amount of time (in samples)
        numperiods=int(gentime/self.period)+2 #the +2 is necessary to create a longer-then needed list that will be trimmed down
        pulses=self.pulse*numperiods #generate a train of pulses
        inittime=(self.time%self.period) #time in pulsetrain to start at (which is the index in a single pulse the last pulse started at)
        final=np.array(pulses[inittime:gentime+inittime]) #slice to get a list with a length of gentime elements and turn into numpy array
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
import mido
mid = MidiFile(f"{inpath}{midi}")
ticksPerBeat=mid.ticks_per_beat #THIS FIXES ALL THE TEMPO PROBLEMS AHHHHHH
#print(f"ticks per beat: {ticksPerBeat}")
time=0
temposet=False #whether tempo has been set
for track in mid.tracks:
    for msg in track[:min((len(track), 10))]:
        #print(msg)
        if msg.type=='set_tempo':
            if tempoAutoset and not temposet:
                temposet=True
                tempo=msg.tempo #comment out if tempo is completely wrong
                print(f"found tempo: {mido.tempo2bpm(msg.tempo)} bpm")




print("converting relative times to absolute times and merging tracks")
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
    if msg.type=='note_on' or msg.type=='note_off' or msg.type=='pitchwheel':
        if ind%100==0:
            print(f"processed {ind}/{bigLen} commands")
            pass
        genTime=ticks2samples(msg.time-absTime) #convert to samples WARNING: midi time is in absolute time rather than relative, so it will not process normal midi that has not run through preprocessing without modification
        music[currSampTime:currSampTime+genTime]=np.where(sum([tone.generate(genTime) for tone in tones]) > 0, 1, 0) #maybe could cut down on compute by replacing sum with something
        #for more advanced polyphony, modify the sum() and tone.generate (probably mess with the offset time)
        currSampTime+=genTime
        absTime+=msg.time-absTime
        if msg.type=='note_on':
           #pulseDuration = msg.velocity*pulseCorrectionFactor TODO: possibly add some sort of compensation for the higher and lower frequencies
           tones.append(tone(msg.note, msg.velocity, msg.channel)) #append note to current note playing
        if msg.type=='note_off':
            tonetoremove=findInTones(msg.note)
            if tonetoremove is not None:
                tones.pop(tonetoremove) #remove note once it stops playing
    if msg.type=='tempo':
        tempo=msg.tempo
    if msg.type=='pitchwheel':
        for ind in range(len(tones)):
            if tones[ind].channel==msg.channel:
                tones[ind].changePitch(msg.pitch)
        #find all tones with same channel attribute and change pitch


#TODO: Drum implementation using a single long pulse
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
print("postprocessing complete")
print()

print(f'conversion complete: {len(music)/fs} seconds of music ({len(music)} samples)')
print(f'with tempo: {tempo} us/beat')
print(f"completed in {time.monotonic()-dt} seconds.")
if dosavewav:
    print(f"saving file as {savewav}.{savefiletype}")
    writeWav(music)
if doplaymusic:
    print(f"playing music...")
    playmusic(music)
