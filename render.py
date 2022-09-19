import sys
import logging
import argparse
import time
import json
from ffmpeg import Ffmpeg

def main(args):
    parser = argparse.ArgumentParser(description='Time Stretch')

    parser.add_argument("videoFile", action="store", help="Full path and filename for original video")
    parser.add_argument("--ffmpegPath", "-f", default="ffmpeg.exe", help="Full path for ffmpeg runtime")

    options = parser.parse_args()
    if options.videoFile is None:
        parser.print_help()
    
    logger = getLogger(options.logLevel)

    _ffmpegPath = "ffmpeg.exe"
    if options.ffmpegPath is not None:
        _ffmpegPath = f"{options.ffmpegPath}\\{_ffmpegPath}"
    ffmpeg = Ffmpeg(_ffmpegPath, logger, options.logLevel, options.ffmpegLogLevel)

    workingDir = '\\'.join(options.videoFile.split('\\')[0:-1])

    process(logger, ffmpeg, workingDir)

def getLogger(logLevel):
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.FileHandler('log.txt', mode='w')
    handler.setFormatter(formatter)
    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(formatter)
    logger = logging.getLogger("MyLogger")
    logger.setLevel(logLevel)
    logger.addHandler(handler)
    logger.addHandler(screen_handler)
    return logger

def process(logger, ffmpeg, workingDir):
    _dur = 0
    _startTime = time.time()

    _indexFilename = "index.txt"
    _indexFilePath = f"{workingDir}\\{_indexFilename}"

    # words = segmentVideo()
    words = [(0, 20, "word"), (25, 50, "longer")]

    with open(_indexFilePath, "w") as indexFile:
        indexFile.write(f"file '{_outputFilename}'\n")
        for wordTuple in words:
            _start = wordTuple[0]
            _dur = wordTuple[1]
            _word = wordTuple[2]
            _outputFilename = ffmpeg.trim(workingDir, _start, _dur, _word, _outputFilename)
            break

        ffmpeg.concat(_indexFilePath, f"\"{workingDir}\\output.mp4\"")
        logger.info(f"Processing done. Runtime: {ffmpeg.secondsToTimecode(time.time() - _startTime, False)}.")

def segmentVideo(JsonFillePath):
    wordSegments = []
    videoData = json.load(open(JsonFillePath))
    
    for word in videoData["Words"]:
        wordStatistics = (word["Offset"], word["Duration"], word["Word"])
        wordSegments.append(wordStatistics)
        
    return wordSegments
    

if __name__ == '__main__':
    sys.exit(main(sys.argv))
