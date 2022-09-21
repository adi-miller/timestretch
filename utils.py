import time
from speech import SpeechCli

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

