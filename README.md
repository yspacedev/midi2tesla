Simple converter for midi files to square wave tesla coil music

A few notes:
Midis that have a lot of simultaneous tracks and notes will have to have some tracks removed as they will not sound very good when converted into what is essentially 1-bit audio. Use something like https://signal.vercel.app/ to view and modify your midis. If you need midis, there are a lot of sites offering free midis and there are some large repositories of midis for Tesla coils.

For some reason, the tempo of the resultant file can be completely off. If it is (usually indicated by the conversion taking way too long (usually it takes around 1 second to convert a 2 minute song), change the tempoCorrectionFactor variable. The correct correction factor will usually range somewhere from 1 to 20 and is usually a multiple of 4.
