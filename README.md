Simple converter for midi files to "square wave" Tesla coil music

For custom (and better quality!) music on prebuilt Tesla coils that connect over bluetooth or people who don't have, don't want to build, or don't find it convenient to use a fiber optic interrupter. 

A few notes:

Midis with many simultaneous tracks and notes will have to have some tracks removed as they will not sound very good when converted into what is essentially 1-bit audio. Use something like https://signal.vercel.app/ to view and modify your midis. There are some large repositories of midis for Tesla coils specifically, and those files will often work decently well without additional modification. I recommend removing any redundant or noisy tracks. You can simulate how it will sound in the Signal app by changing everything to the synth (square wave) instrument.

Recommended midi modifications:
- remove all drums (they tend to slow down conversion and make the resulting quality worse)
- remove any tracks that play the same note as another track (this makes sections noisy and takes longer to process)
- remove long-held notes unless necessary

Songs that seem to work well:
- Generally very melodic, fast-paced music
- anything that relies on a very slow melody will end up having annoying continuous tones that overshadow everything else
- anything that relies on drums and vocals more than instruments like guitar, piano, etc will likely not sound very good and/or be hard to recognize
- Generally, just experiment to see what sounds good.


Features:
- basic polyphony on a single coil
- multitrack midi support
- pitchbend support
- accessible playback parameters in code
- simple to use (at least in my opinion)
- CURRENTLY WIP - note decay, ADSR envelopes, tempo and time signature change

Usage example:

`python midi2tesla.py --folder --reference_path . "<midi>.mid"` will convert \<midi\>.mid from the folder /input to \<midi\>.mid.mp3 in the folder /output


`python midi2tesla.py --folder --reference_path . "<midi>.mid" --output "<filename>"` will convert \<midi\>.mid from the folder /input to \<filename\>.mp3 in the folder /output


`python midi2tesla.py "<midi>.mid"` will convert \<midi\>.mid from the current directory to <midi\>.mid.mp3 in the current directory



required parameter: input: String with path and filename to midi file to convert.

optional parameters:
- --reference_path or -p determines what root path to look for files in
- --output overrides the default save file name
- --folder or -f will use /input and /output folders
- --duty_cycle or -d controls the maximum duty cycle parameter
- --no_save_file or -s disables file saving
- --play_music or -m will play music after processing


