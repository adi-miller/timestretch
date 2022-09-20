import sys
import logging
import argparse
import time
import json
from ffmpeg import Ffmpeg
from speech import SpeechCli


def main(args):
    parser = argparse.ArgumentParser(description='Time Stretch')

    parser.add_argument("videoFile", action="store",
                        help="Full path and filename for original video")
    parser.add_argument("--ffmpegPath", "-f", default="ffmpeg.exe",
                        help="Full path for ffmpeg runtime")
    parser.add_argument("--speechKey", "-k", action="store",
                        help="Key to Speech services")

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
    # Generate the synthesized audio file from the sentences in the original audio file
    # speech = SpeechCli(logger)
    # SpeechCli(logger).runSpxSynthesized(options.speechKey, sentences, audFileSynthesized)
    # synthesizedWordLevelTimestamp = createWordLevelTimestamp(
    #     logger, options.speechKey, audFileSynthesized)
    process(logger, ffmpeg, workingDir, options.videoFile, wordLevelTimestamp)
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


def createWordLevelTimestamp(logger, key, audFile):
    speech = SpeechCli(logger)
    return speech.runSpxRecognize(key, audFile)


def createAudioOnlyFile(logger, videoFile, ffmpeg, workingDir):
    vidFile = f"\"{workingDir}\\{videoFile}\""
    audFile = vidFile.replace(".mp4", ".wav")

    ffmpeg.extractAudio(logger, vidFile, audFile)
    return audFile


def createFiltersFile(filterFile, words):
    lengthOfWords = len(words)
    filterComplex = f"[0:v]trim=0:{words[0][1]},setpts=PTS-STARTPTS[v{0}];"
    filterComplex += f"[0:a]atrim=0:{words[0][1]},asetpts=PTS-STARTPTS[a{0}];"

    concatedParts = "[v0][a0]"
    for i in range(lengthOfWords):
        _speed = words[i][3] if len(words[i]) == 4 else 1.0
        _text = f"{words[i][0]} dur: {words[i][2]} speed: {_speed}"
        concatedParts += f"[v{i+1}][a{i+1}]"
        if (i == lengthOfWords - 1):
            filterComplex += f"[0:v]trim={words[i][1]},setpts={1/_speed}*(PTS-STARTPTS),drawtext=text=\\'{_text}\\':fontfile=/Windows/fonts/calibri.ttf:box=1:boxborderw=12:boxcolor=white:x=44:'y=44':fontsize=32:fontcolor=black[v{i+1}];"
            filterComplex += f"[0:a]atrim={words[i][1]},asetpts=PTS-STARTPTS,atempo={_speed}[a{i+1}];"
        else:
            filterComplex += f"[0:v]trim={words[i][1]}:{words[i+1][1]},setpts={1/_speed}*(PTS-STARTPTS),drawtext=text=\\'{_text}\\':fontfile=/Windows/fonts/calibri.ttf:box=1:boxborderw=12:boxcolor=white:x=44:'y=44':fontsize=32:fontcolor=black[v{i+1}];"
            filterComplex += f"[0:a]atrim={words[i][1]}:{words[i+1][1]},asetpts=PTS-STARTPTS,atempo={_speed}[a{i+1}];"

    filterComplex += concatedParts
    filterComplex += f"concat=n={lengthOfWords + 1}:v=1:a=1"

    with open(filterFile, "w") as indexFile:
        indexFile.write(filterComplex)


def compareAndExtractWordSpeeds(logger, wordsOriginal, wordsSynthesized):
    minSpeed = 0.5

    # This should have a better algorithm to match words if the count is different
    if (len(wordsOriginal) != len(wordsSynthesized)):
        logger.error("Word count mismatch")
        raise Exception("Word counts do not match")

    wordsWithSpeedRatio = []
    for i in range(len(wordsSynthesized)):
        wordsWithSpeedRatio.append(
            (wordsOriginal[i][0], wordsOriginal[i][1], wordsOriginal[i][2], max(wordsOriginal[i][2] / wordsSynthesized[i][2], minSpeed)))

        # Spaces additions: Take some space time (white noise) based on the spaces in the target
        # if (i < len(wordsTarget) - 1):
        #     output.append(
        #         ("(Silence)", wordsOriginal[i][1] + wordsOriginal[i][2], wordsTarget[i+1][1] - (wordsTarget[i][1] + wordsTarget[i][2])))

    return wordsWithSpeedRatio


def processWithWords(logger, ffmpeg, workingDir, vidFile, wordsOriginal, wordsSynthesized):
    _startTime = time.time()
    wordsWithSpeedRatio = compareAndExtractWordSpeeds(
        logger, wordsOriginal, wordsSynthesized)
    createFiltersFile(f"{workingDir}\\filter.txt", wordsWithSpeedRatio)
    ffmpeg.processWithFilterFile(
        f"\"{workingDir}\\{vidFile}\"", f"\"{workingDir}\\{vidFile.replace('.mp4', '_speed_ratio.mp4')}\"", f"\"{workingDir}\\filter.txt\"")
    logger.info(
        f"Processing done. Runtime: {ffmpeg.secondsToTimecode(time.time() - _startTime, False)}.")


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
            _outputFilename = ffmpeg.trim(
                vidFile, _start, _dur, 1.0, _text, _outputFilename)
            indexFile.write(f"file '{_outputFilename}'\n")

    ffmpeg.concat(_indexFilePath, f"\"{workingDir}\\output.mp4\"")
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
