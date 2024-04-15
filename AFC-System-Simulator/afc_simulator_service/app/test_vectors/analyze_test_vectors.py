import os
import json

import os

# Set the path for the directory and file
directory_path = "./analysis"


# Check if the directory exists and create it if it doesn't
if not os.path.exists(directory_path):
    os.makedirs(directory_path)

vectors_folder_path = './'

def get_cfi_from_freq_range(high, low):
    return (((high + low)/2) - 5950)/5

def get_cfi_from_op_channel(op_channel, bw):
    cfi_bw = { 
        40: (3, 11, 19, 27, 35, 43, 51, 59, 67, 75, 83, 91, 99, 107, 115, 123, 131, 139, 147, 155, 163, 171, 179, 187, 195, 203, 211, 219, 227),
        80: (7, 23, 39, 55, 71, 87, 103, 119, 135, 151, 167, 183, 199, 215),
    160: (15, 47, 79, 111, 143, 175, 207)
    }
    if (op_channel % 4) != 1:
        return 0
    for cfi in cfi_bw[bw]:
        if (cfi - bw/10) < op_channel < (cfi + bw/10):
            return cfi

    return 0

def get_full_chanset_from_cfi(cfi, bw):
    start = int(cfi - (bw/10 - 2))
    step = 4
    end = int(cfi + (bw/10 - 2))

    numbers = set(range(start, end+1, step))

    return numbers

def check_bw_from_freq_range(bw, file, cfi_dict):
    file.write(f"\n###### Check {bw}MHz from freq ranges: ######\n")
    avai_freq = []
    for key, value in cfi_dict.items():
        if len(value) != int(bw/20):
            file.write(f"{str(int(key)).ljust(3)} : {value}\n")
        else:
            file.write(f"{str(int(key)).ljust(3)} : {value} - OK\n")
            avai_freq.append(int(key))
    avai_chan = [key for key, value in vector.items() if 'bw' in value and value['bw'] == bw]
    file.write(f"\n~~~ Available {bw}MHz from\n")
    if '_3' in filename or '_1' in filename:
        file.write(f"freq ranges: {avai_freq}")
        if '_3' in filename:
            file.write(f" - No {set(avai_chan)-set(avai_freq)}\n")
        else:
            file.write("\n")
    if '_3' in filename or '_2' in filename:                        
        file.write(f"channelCfi : {avai_chan}\n")
    else:
        file.write("\n")

for filename in os.listdir(vectors_folder_path):
    if filename.endswith('.json'):
        file_path = os.path.join(vectors_folder_path, filename)
        print(f"\n-----------  {filename}  -----------")
        with open(file_path) as f:
            json_content = json.load(f)
            # do something with the json_content
            # print(json_content)
            vector = {}
            cfi40 = {}
            cfi80 = {}
            cfi160 = {}
            resp = json_content["responses"]["availableSpectrumInquiryResponses"][0]
            if 'availableFrequencyInfo' in resp:
                for availableFrequencyInfo in resp["availableFrequencyInfo"]:
                    highFrequency = availableFrequencyInfo["frequencyRange"]["highFrequency"]
                    lowFrequency = availableFrequencyInfo["frequencyRange"]["lowFrequency"]
                    maxPsd = availableFrequencyInfo["maxPsd"]
                    cfi = get_cfi_from_freq_range(highFrequency, lowFrequency)
                    if cfi > 0:
                        vector.setdefault(int(cfi), {})["maxPsd"] = maxPsd
                        cfi40.setdefault(get_cfi_from_op_channel(cfi, 40), []).append(int(cfi))
                        cfi80.setdefault(get_cfi_from_op_channel(cfi, 80), []).append(int(cfi))
                        cfi160.setdefault(get_cfi_from_op_channel(cfi, 160), []).append(int(cfi))
            
            if 'availableChannelInfo' in resp:
                for availableChannelInfo in resp["availableChannelInfo"]:
                    channelCfi = availableChannelInfo["channelCfi"]
                    for index, cfi in enumerate(channelCfi):                        
                        vector.setdefault(int(cfi), {})["maxEirp"] = availableChannelInfo["maxEirp"][index]
                        if availableChannelInfo["globalOperatingClass"] == 131:
                            bw = 20
                        elif availableChannelInfo["globalOperatingClass"] == 132:
                            bw = 40
                        elif availableChannelInfo["globalOperatingClass"] == 133:
                            bw = 80
                        elif availableChannelInfo["globalOperatingClass"] == 134:
                            bw = 160
                        else:
                            bw = 20
                        vector.setdefault(int(cfi), {})["bw"] = bw

            # print(vector)
            analysis_file_path = f'{directory_path}/{filename.replace(".json", ".txt")}'
            with open(analysis_file_path, "w") as file:
                missing_chancfi = []
                missing_freq_range = []
                for key, value in vector.items():
                    if key !=2 and ('bw' not in value or value["bw"] == 20) and '_3' in filename:
                        if 'maxEirp' in value and 'maxPsd' not in value:
                            missing_freq_range.append(key)
                        if 'maxEirp' not in value and 'maxPsd' in value:
                            missing_chancfi.append(key)
                        # file.write(f"{str(int(key)).ljust(3)} : {value} - In channelCfi but not in freq range\n")                    
                    file.write(f"{str(int(key)).ljust(3)} : {value}\n")
                if '_3' in filename:
                    file.write(f"\nIn freq range but not in channelCfi:\n {missing_chancfi}\n")
                    file.write(f"Not in freq range but in channelCfi:\n {missing_freq_range}\n")

                if '_RSA_' in filename:
                    ######################################################################
                    check_bw_from_freq_range(40, file, cfi40)
                    ######################################################################
                    check_bw_from_freq_range(80, file, cfi80)
                    ######################################################################
                    check_bw_from_freq_range(160, file, cfi160)


