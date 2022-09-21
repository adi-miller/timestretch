import os
import json


class SpeechCli:
    def __init__(self, logger):
        self.logger = logger

    def extractSentencesOnly(self, file, outputFile):
        with open(file, 'r') as speechJson:
            with open(outputFile, 'w') as output:
                startAdding = False
                try:
                    for line in speechJson:
                        if startAdding:
                            if "]," in line:
                                break
                            output.writelines(
                                line.strip().strip(",").strip("\"") + " ")

                        if "recognizer.recognized.result.text" in line:
                            startAdding = True
                            continue
                except Exception as ex:
                    print(ex)
                    raise ex

    def runSpxRecognize(self, key, audFile, outputFile):
        command = "spx recognize --endpoint \"wss://westus.onlinects.speech.microsoft.com/recognition/onlinemeeting/v1?TrafficType="\
            f"Test&Language=en-us&wordLevelTimestamps=true\" --key {key} --region westus --continuous --output file type json "\
            f"--output all file name {outputFile} --output all result lexical text --output all offset --output all connection "\
            f"message received text message --files {audFile}"
        self.logger.debug(command)
        res = os.system(command)
        if (res != 0):
            raise Exception(res)

        words = []
        with open(outputFile, 'r') as speechJson:
            for line in speechJson:
                if "RecognitionStatus" in line:
                    try:
                        line = line.strip()
                        line = line[1:-2]
                        line = line.replace("\\", "")
                        jsonLine = json.loads(line)
                        if jsonLine["DisplayText"] != "":
                            # print(jsonLine["DisplayText"])
                            maxConfidenceIndex = self.getMaxConfidenceIndex(
                                jsonLine)
                            jsonWords = jsonLine["NBest"][0]["Words"]
                            for jsonWord in jsonWords:
                                words.append(
                                    (jsonWord["Word"], jsonWord["Offset"]/10000000, (jsonWord["Duration"]/10000000)))
                            continue
                    except Exception as ex:
                        print(ex)
                        pass

        return words

    def getMaxConfidenceIndex(self, jsonLine):
        maxConfidence = 0
        maxConfidenceIndex = 0

        for i in range(len(jsonLine["NBest"])):
            newConfidence = jsonLine["NBest"][i]["Confidence"]
            if (newConfidence > maxConfidence):
                maxConfidence = newConfidence
                maxConfidenceIndex = i

        return maxConfidenceIndex

    def runSpxSynthesized(self, key, file, audFileOutput):
        command = f"spx synthesize --key {key} --region westus --file \"{file}\" --audio output {audFileOutput}"
        self.logger.debug(command)
        res = os.system(command)
        if (res != 0):
            raise Exception(res)
