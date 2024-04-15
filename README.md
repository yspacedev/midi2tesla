Simple converter for midi files to square wave tesla coil music

A few notes:

Midis with many simultaneous tracks and notes will have to have some tracks removed as they will not sound very good when converted into what is essentially 1-bit audio. Use something like https://signal.vercel.app/ to view and modify your midis. There are some large repositories of midis for Tesla coils specifically, and those files will often work decently well without additional modification. I recommend removing any redundant or noisy tracks. You can simulate how it will sound in the Signal app by changing everything to the synth (square wave) instrument.

Usage example:

python midi2tesla.py --folder --reference_path . "\<midi\>.mid"

will convert \<midi\>.mid from the folder /input to \<midi\>.mid.mp3 in the folder /output
