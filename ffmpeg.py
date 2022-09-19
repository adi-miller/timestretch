import os
import time
from asyncio.log import logger

class Ffmpeg:
    _gaussFactor = 12000
    
    def __init__(self, path, logger, logLevel, ffmpegLogLevel):
        self.ffmpeg_path = path + f" -y -loglevel {ffmpegLogLevel}"
        self.logger = logger

    def trim(self, cfg, workingDir, startTime, endTime, word, output):
        start_time = time.time()
        length = endTime - startTime
        vidFile = f"\"{workingDir}\\{cfg.videoFile}\""

        self.logger.info(f"Rendering section {output}...")
        self.logger.info(f" - Trimming from {self.secondsToTimecode(startTime, False)} to {self.secondsToTimecode(endTime, False)}")
        command = f"{self.ffmpeg_path} -ss {startTime} -to {endTime} -i {vidFile} "
        command = command + f" -filter_complex \"drawtext=timecode=\'{self.secondsToTimecode(startTime)}\:000':r=15.97:x=w-tw-10:y=h-th-10:fontsize=24:fontcolor=white"

        command = command + f", drawtext=text='{word}':font=Calibri:box=1:boxborderw=12:boxcolor=#DD4F1B:x=44:'y=822':fontsize=64:fontcolor=white"

        # command = command + f" ,setpts=0.5*PTS;atempo=2.0"

        command = command + f"\" -pix_fmt yuv420p \"{workingDir}\\{output}\""
        self.logger.debug(command)
        os.system(command)
        self.logger.info(f"Section rendering done. Runtime: {self.secondsToTimecode(time.time() - start_time, False)}.")

        return output

    def concat(self, indexFilename, metadataFilename, output):
        command = f"{self.ffmpeg_path} -f concat -safe 0 -i \"{indexFilename}\" -i \"{metadataFilename}\" -af loudnorm -map_metadata 1 -c:v copy {output}"
        self.logger.info(f"Rendering {output}...")
        self.logger.info(f" - Normalizing audio levels")
        self.logger.debug(command)
        res = os.system(command)
        return output

    def timecodeToSeconds(self, timecode):
        hours, minutes, seconds = timecode.split(':')
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)

    def secondsToTimecode(self, seconds, escaped = True):
        hours = int(seconds / 3600)
        minutes = int(seconds / 60) % 60
        seconds = round(seconds % 60, 2)
        if escaped:
            return f"{hours:>02d}\:{minutes:>02d}\:{seconds:>02d}"
        else:
            return f"{hours:>02d}:{minutes:>02d}:{seconds:>02.2f}"
    
    def wordWrap(self, sentence, length):
        words = sentence.split(" ")
        _sentence = ""
        _count = 0
        for word in words:
            _count = _count + len(word) + 1
            if _count > length:
                _sentence = _sentence.strip() + "\v" + word + " "
                _count = len(word) + 1
            else:
                _sentence = _sentence + word + " "
        return _sentence.strip("\r\n. ")
