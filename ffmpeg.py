import os
import time
from asyncio.log import logger

class Ffmpeg:
    def __init__(self, path, logger):
        self.ffmpeg_path = path + f" -y"
        self.logger = logger

    def extractAudio(self, logger, inputFile, outputFile):
        command = f"{self.ffmpeg_path} -i {inputFile} -ss 0 -t 30 -acodec pcm_s16le -ac 1 -ar 16000 {outputFile}"
        self.logger.debug(command)
        res = os.system(command)
        if (res != 0):
            raise Exception(res)

    def trim(self, vidFile, startTime, duration, speed, text, output):
        self.logger.info(f"Rendering section {output}...")
        command = f"{self.ffmpeg_path} -ss {startTime} -i \"{vidFile}\" -t {duration} "
        command = command + f" -filter_complex \"drawtext=text=\\'{text}\\':font=Calibri:box=1:boxborderw=12:boxcolor=white:x=44:'y=44':fontsize=128:fontcolor=black"

        command = command + f" ,setpts={1/speed}*PTS;atempo={speed}"

        command = command + f"\" -pix_fmt yuv420p \"{output}\""
        self.logger.debug(command)
        os.system(command)

        return output

    def processWithFilterFile(self, vidFile, output, filterFile):
        """
        Runs the ffmpeg command on the input file with the filter file and outputs to the output file
        """
        self.logger.info(
            f"Processing {vidFile} with complex filters file {filterFile}...")

        command = f"{self.ffmpeg_path} -i \"{vidFile}\" -filter_complex_script \"{filterFile}\""
        command += f" -preset superfast -profile:v baseline {output}"
        self.logger.debug(command)
        os.system(command)
        return output

    def concat(self, indexFilename, output):
        command = f"{self.ffmpeg_path} -f concat -safe 0 -i \"{indexFilename}\" -c:v copy {output}"
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
