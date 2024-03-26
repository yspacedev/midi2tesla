Simple converter for midi files to square wave tesla coil music

A few notes:

Midis with many simultaneous tracks and notes will have to have some tracks removed as they will not sound very good when converted into what is essentially 1-bit audio. Use something like https://signal.vercel.app/ to view and modify your midis. There are some large repositories of midis for Tesla coils specifically, and those files will often work decently well although any midi can work as well. I recommend removing any redundant or noisy tracks. You can simulate how it will sound in the Signal app by changing everything to the synth (square wave) instrument.

For some reason, the tempo of the resultant file can be completely off. If it is (usually indicated by the conversion taking way too long (usually it takes around 1 second to convert a 2 minute song if the tempo is set correctly), change the tempoCorrectionFactor variable. The correct correction factor will usually range somewhere from 1 to 20 and is usually a multiple of 4.

Usage example:

python midi2tesla.py "come as you are.mid"
