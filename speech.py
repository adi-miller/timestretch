import os
import json

class SpeechCli:
    def __init__(self, logger):
        self.logger = logger

    def runSpx(self, key, audFile):
        # command = "spx recognize --endpoint \"wss://westus.onlinects.speech.microsoft.com/recognition/onlinemeeting/v1?TrafficType="\
        #         f"Test&Language=en-us&wordLevelTimestamps=true\" --key {key} --region westus --continuous --output file type json "\
        #         "--output all file name singlerun.json --output all result lexical text --output all offset --output all connection "\
        #         f"message received text message --files {audFile}"
        # self.logger.debug(command)
        # res = os.system(command)
        # if (res != 0):
        #     raise Exception(res)

        words = []
        with open("singlerun.json", 'r') as speechJson:
            for line in speechJson:
                if "RecognitionStatus" in line:
                    try:
                        line = line.strip()
                        line = line[1:-2]
                        line = line.replace("\\", "")
                        jsonLine = json.loads(line)
                        if jsonLine["DisplayText"] != "":
                            print(jsonLine["DisplayText"])
                            maxConfidenceIndex = self.getMaxConfidenceIndex(jsonLine)
                            jsonWords = jsonLine["NBest"][maxConfidenceIndex]["Words"]
                            for jsonWord in jsonWords:
                                words.append((jsonWord["Word"], jsonWord["Offset"]/10000000, (jsonWord["Duration"]/10000000)))
                            continue
                    except Exception as ex:
                        print(ex)
                        pass
        
        return words
    
    def getMaxConfidenceIndex(jsonLine):
        maxConfidence = 0
        maxConfidenceIndex = 0
        
        for i in range(len(jsonLine["NBest"])): 
            newConfidence = jsonLine["NBest"][i]["Confidence"]
            if(newConfidence > maxConfidence):
                maxConfidence = newConfidence
                maxConfidenceIndex = i       
                
        return maxConfidenceIndex
