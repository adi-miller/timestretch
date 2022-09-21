import time


class AdimiIMpl:
    def __init__(self, path, logger, ffmpeg):
        self.ffmpeg = ffmpeg
        self.ffmpeg_path = path + f" -y"
        self.logger = logger

    def process(self, workingDir, vidFile, words):
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
                _outputFilename = self.ffmpeg.trim(
                    vidFile, _start, _dur, 1.0, _text, _outputFilename)
                indexFile.write(f"file '{_outputFilename}'\n")

        self.ffmpeg.concat(_indexFilePath, f"\"{workingDir}\\output.mp4\"")
        self.logger.info(
            f"Processing done. Runtime: {self.ffmpeg.secondsToTimecode(time.time() - _startTime, False)}.")
