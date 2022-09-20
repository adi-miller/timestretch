import sys
import logging
import argparse
import time
import json
from ffmpeg import Ffmpeg
from speech import SpeechCli

def main(args):
    parser = argparse.ArgumentParser(description='Time Stretch')

    parser.add_argument("videoFile", action="store", help="Full path and filename for original video")
    parser.add_argument("--ffmpegPath", "-f", default="ffmpeg.exe", help="Full path for ffmpeg runtime")
    parser.add_argument("--speechKey", "-k", action="store", help="Key to Speech services")
    

    options = parser.parse_args()
    if options.videoFile is None:
        parser.print_help()
    
    logger = getLogger(logLevel=logging.DEBUG)

    _ffmpegPath = "ffmpeg.exe"
    if options.ffmpegPath is not None:
        _ffmpegPath = f"{options.ffmpegPath}\\{_ffmpegPath}"
    ffmpeg = Ffmpeg(_ffmpegPath, logger)

    workingDir = '\\'.join(options.videoFile.split('\\')[0:-1])
    if workingDir == "":
        workingDir = "."
    audFile = createAudioOnlyFile(logger, options.videoFile, ffmpeg, workingDir)
    wordLevelTimestamp = createWordLevelTimestamp(logger, options.speechKey, audFile)
    process(logger, ffmpeg, workingDir, options.videoFile, wordLevelTimestamp)

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

def createWordLevelTimestamp(logger, key, audFile):
    speech = SpeechCli(logger)
    return speech.runSpx(key, audFile)

def createAudioOnlyFile(logger, videoFile, ffmpeg, workingDir):
    vidFile = f"\"{workingDir}\\{videoFile}\""
    audFile = vidFile.replace(".mp4", ".wav")

    ffmpeg.extractAudio(logger, vidFile, audFile)
    return audFile

def process(logger, ffmpeg, workingDir, vidFile, words):
    _startTime = time.time()

    _indexFilename = "index.txt"
    _indexFilePath = f"{workingDir}\\{_indexFilename}"

    index = 0
    with open(_indexFilePath, "w") as indexFile:
        words = words[:80]
        for wordTuple in words:
            _word = wordTuple[0]
            _start = wordTuple[1]
            _dur = wordTuple[2]
            _outputFilename = f"wordFile{index:05d}.mp4"
            index = index + 1
            _text = f"{_word} dur: {_dur} cps: {round(_dur/len(_word), 2)}"
            _outputFilename = ffmpeg.trim(vidFile, _start, _dur, 1.0, _text, _outputFilename)
            indexFile.write(f"file '{_outputFilename}'\n")

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
