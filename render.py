import sys
import logging
import argparse
import time
import json
from adimi import AdimiIMpl
from ffmpeg import Ffmpeg
from speech import SpeechCli
from utils import createAudioOnlyFile, createWordLevelTimestamp


def main(args):
    parser = argparse.ArgumentParser(description='Time Stretch')

    parser.add_argument("videoFile", action="store",
                        help="Full path and filename for original video")
    parser.add_argument("--ffmpegPath", "-f", default="ffmpeg.exe",
                        help="Full path for ffmpeg runtime")
    parser.add_argument("--speechKey", "-k", action="store",
                        help="Key to Speech services")
    parser.add_argument("--method", "-m", default="default",
                        help="Which rednering method to use")

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

    audFile = createAudioOnlyFile(
        logger, options.videoFile, ffmpeg, workingDir)
    wordLevelTimestamp = createWordLevelTimestamp(
        logger, options.speechKey, audFile)

    if options.method == "adimi":
        impl = AdimiIMpl("", logger, ffmpeg)
        impl.process(workingDir, options.videoFile, wordLevelTimestamp)
        return

    # Generate the synthesized audio file from the sentences in the original audio file
    # speech = SpeechCli(logger)
    # SpeechCli(logger).runSpxSynthesized(options.speechKey, sentences, audFileSynthesized)
    # synthesizedWordLevelTimestamp = createWordLevelTimestamp(
    #     logger, options.speechKey, audFileSynthesized)
    # process(logger, ffmpeg, workingDir, options.videoFile, wordLevelTimestamp)
    # processWithWords(logger, ffmpeg, workingDir, options.videoFile,
    #                  wordLevelTimestamp, synthesizedWordLevelTimestamp)

def getLogger(logLevel):
    formatter = logging.Formatter(
        fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.FileHandler('log.txt', mode='w')
    handler.setFormatter(formatter)
    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(formatter)
    logger = logging.getLogger("MyLogger")
    logger.setLevel(logLevel)
    logger.addHandler(handler)
    logger.addHandler(screen_handler)
    return logger

def processWithWords(logger, ffmpeg, workingDir, vidFile, wordsOriginal, wordsSynthesized):
    _startTime = time.time()
    wordsWithSpeedRatio = compareAndExtractWordSpeeds(
        logger, wordsOriginal, wordsSynthesized)
    createFiltersFile(f"{workingDir}\\filter.txt", wordsWithSpeedRatio)
    ffmpeg.processWithFilterFile(
        f"\"{workingDir}\\{vidFile}\"", f"\"{workingDir}\\{vidFile.replace('.mp4', '_speed_ratio.mp4')}\"", f"\"{workingDir}\\filter.txt\"")
    logger.info(
        f"Processing done. Runtime: {ffmpeg.secondsToTimecode(time.time() - _startTime, False)}.")

def segmentVideo(JsonFillePath):
    wordSegments = []
    videoData = json.load(open(JsonFillePath))

    for word in videoData["Words"]:
        wordStatistics = (word["Offset"], word["Duration"], word["Word"])
        wordSegments.append(wordStatistics)

    return wordSegments

if __name__ == '__main__':
    sys.exit(main(sys.argv))
