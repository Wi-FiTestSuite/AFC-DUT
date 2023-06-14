# Copyright (c) 2022 Wi-Fi Alliance                                                

# Permission to use, copy, modify, and/or distribute this software for any         
# purpose with or without fee is hereby granted, provided that the above           
# copyright notice and this permission notice appear in all copies.                

# THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL                    
# WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED                    
# WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL                     
# THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR                       
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING                        
# FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF                       
# CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT                       
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS                          
# SOFTWARE.

# This file will be copied to: /usr/local/bin/WFA-QuickTrack-Tool/IndigoTestScripts/Programs/AFC/
# This file is vendor specific implementation
import configparser
import os
import shutil
import csv
import math
import traceback
from IndigoTestScripts.helpers.instruction_lib import InstructionLib
from commons.logger import Logger
from commons.shared_enums import (
    LogCategory,
)

# (channel, bandwidth)
all_channels_6g = [(15, 160), (47, 160), (79, 160), (119, 80), (143, 160), (175, 160)]

class SpectrumAnalyzer:

    work_dir = "/usr/local/bin/WFA-QuickTrack-Tool/QuickTrack-Tool/Test-Services/AppData/vendor_sample/"

    def __init__(self):
        self.captured_packets = {}
        self.address = "127.0.0.1"
        self.rf_ports = "RF1A"
        self.error = None

    def spectrum_analyzer_connect(self):
        """
        Check connection of RF equipment.      
        
        Returns:
            bool: returns True if connection is ok else False.
        """
        # If we can check connection of RF equipment, implement it here
        if self.error and "Could not connect to" in self.error:
            Logger.log(LogCategory.ERROR, f"Could not connect to Spectrum Analyzer tester {self.address}")
            return False
        return True

    def spectrum_analyze_all(self, timeout):
        """
        Performs spectrum analysis on all channels for a specified duration.

        Args:
            timeout (float): The duration of the spectrum analysis in seconds.

        Returns:
            list: A list of RF measurement reports generated for each channel and bandwidth combination.

        Raises:
            Exception: If an error occurs during the spectrum analysis.

        Notes:
            - The method utilizes the `__spectrum_analyze` method to perform spectrum analysis for each channel and bandwidth.
            - Captured packets are stored in the `captured_packets` dictionary.
            - Test reports are generated using the `generate_report` method.
            - If the timeout is set to zero, the method performs a single scan across all channels.
        """
        try:
            round = 0
            self.__remove_resluts()
            start = os.times()[4]
            test_report_list = []
            while True:
                round += 1
                for ch, bw in all_channels_6g:
                    pkts = self.__spectrum_analyze(channel=ch, bandwidth=bw)
                    if pkts:
                        key = (ch, bw)
                        if key not in self.captured_packets:
                            self.captured_packets[key] = pkts
                        else:
                            self.captured_packets[key].extend(pkts)

                now = os.times()[4]
                remaining = start + timeout - now
                if remaining <= 0:
                    break

            for key, pkts in self.captured_packets.items():
                ch, bw = key
                test_report_list.append(self.generate_report(ch, bw, pkts))
            return test_report_list
        except Exception as err:
            exception_str = traceback.format_exc()
            Logger.log(LogCategory.ERROR, f'spectrum_analyze_all Exception: {exception_str}')
            return []

    def spectrum_analyze(self, channel, bandwidth, timeout):
        """
        Performs spectrum analysis on a specific channel and bandwidth for a specified duration.

        Args:
            channel (int): The channel number to perform the spectrum analysis on.
            bandwidth (int): The bandwidth to be used for the analysis.
            timeout (float): The duration of the spectrum analysis in seconds.

        Returns:
            dict: A report containing the captured packets and other analysis results.

        Raises:
            Exception: If an error occurs during the spectrum analysis.

        Notes:
            - Captured packets are stored in the `captured_packets` list.
            - The report is generated using the `generate_report` method.
            - If the timeout is set to zero, the method performs a single scan.
        """
        try:
            round = 0
            self.__remove_resluts()
            start = os.times()[4]
            captured_packets = []
            while True:
                round += 1
                captured_packets.extend(self.__spectrum_analyze(
                    channel=channel, bandwidth=bandwidth))

                now = os.times()[4]
                remaining = start + timeout - now
                if remaining <= 0:
                    break
            return self.generate_report(channel, bandwidth, captured_packets)
        except Exception as err:
            exception_str = traceback.format_exc()
            Logger.log(LogCategory.ERROR, f'spectrum_analyze Exception: {exception_str}')
            return {}

    def spectrum_upload_support_data(self, step):
        """
        Uploads support data related to spectrum analysis.

        Args:
            step (str): The step or identifier of the support data.

        Notes:
            - This method assumes that the vendor has generated pcap and csv files during the spectrum analysis process.
            - It checks for existing files in the "Results" directory within the working directory.
            - If a file ends with '.pcap' and has a non-zero size, it is copied to the current testcase log directory
              with the name replaced by the provided step identifier.
            - If a file ends with '.csv', has a non-zero size, and contains 'IQsniffer_results' in its name, it is
              copied to the current testcase log directory with the name replaced by the provided step identifier.
        """
        # This example assumes that vendor has pcap and csv files after
        #     performing a spectrum analysis
        if os.path.exists(os.path.join(self.work_dir, "Results")):
            files = os.listdir(os.path.join(self.work_dir, "Results"))
            for f in files:
                file_path = os.path.join(self.work_dir, "Results",f)
                if f.endswith('.pcap') and os.path.getsize(file_path) > 0:
                    shutil.copy(file_path, os.path.join(InstructionLib.get_current_testcase_log_dir(), f.replace("IQsniffer_pcap", step)))
                if f.endswith('.csv') and os.path.getsize(file_path) > 0 and 'IQsniffer_results' in f:
                    shutil.copy(file_path, os.path.join(InstructionLib.get_current_testcase_log_dir(), f.replace("IQsniffer_results", step)))

    def generate_report(self, channel, bandwidth, captured_packets):
        """
        Generates a report based on the captured packets for a specific channel and bandwidth.

        Args:
            channel (int): The channel number for which the report is generated.
            bandwidth (int): The bandwidth used for the analysis.
            captured_packets (list): A list of captured packets for the specified channel and bandwidth.

        Returns:
            dict: A report containing the RF measurement report.
                {
                    "rfMeasurementReport": {
                        "centralFreq": (5950 + 5 * channel),
                        "channelWidth": bandwidth,
                        "data": [
                            {
                                "maxEirp": float,
                                "maxPSD": float,
                                "freqPsdPerMHz": [
                                    {
                                        "freqMhz": int,
                                        "psdDbmMHz": [N-1, N-2, ..., N-bandwidth]
                                    },
                                    {
                                        "freqMhz": int,
                                        "psdDbmMHz": [N-1, N-2, ..., N-bandwidth]
                                    },
                                    {
                                        "freqMhz": int,
                                        "psdDbmMHz": [N-1, N-2, ..., N-bandwidth]
                                    }
                                ]
                            },
                            ...
                        ]
                    }
                }
                - freqPsdPerMHz contains center, lower and higher freqMhz
                - an item in data list represents a packet
            Example - captured two packets, scan with 20MHz bandwidth
            {
                "rfMeasurementReport": {
                    "centralFreq": 5975,
                    "channelWidth": 20,
                    "data": [
                        {
                            "maxEirp": 14.37963954178672,
                            "maxPSD": 2.450249427795411,
                            "freqPsdPerMHz": [
                                {
                                    "freqMhz": 5975,
                                    "psdDbmMHz": [
                                        -14.595743,
                                        -2.7474346,
                                        1.6685925,
                                        2.1283035,
                                        2.2032871,
                                        2.3282547,
                                        2.258542,
                                        2.282053,
                                        2.3341055,
                                        1.6158638,
                                        1.7312546,
                                        2.4502497,
                                        2.3117905,
                                        2.296504,
                                        2.2784348,
                                        2.191595,
                                        2.086975,
                                        1.8936043,
                                        -1.9260197,
                                        -13.791718
                                    ]
                                },
                                {
                                    "freqMhz": 5955,
                                    "psdDbmMHz": [
                                        -52.243423,
                                        -51.621956,
                                        -50.927757,
                                        -50.22228,
                                        -49.544174,
                                        -48.520924,
                                        -46.34372,
                                        -43.731476,
                                        -41.419655,
                                        -38.995525,
                                        -37.23076,
                                        -35.888985,
                                        -34.62771,
                                        -33.794777,
                                        -32.520016,
                                        -31.101337,
                                        -30.268108,
                                        -29.738064,
                                        -27.46347,
                                        -21.906967
                                    ]
                                },
                                {
                                    "freqMhz": 5995,
                                    "psdDbmMHz": [
                                        -21.294594,
                                        -26.56768,
                                        -29.13749,
                                        -30.23106,
                                        -30.864632,
                                        -31.857117,
                                        -32.43933,
                                        -33.561028,
                                        -35.429504,
                                        -37.30541,
                                        -38.973064,
                                        -41.274536,
                                        -43.595863,
                                        -46.225986,
                                        -47.907116,
                                        -48.870323,
                                        -49.4766,
                                        -50.072918,
                                        -50.529644,
                                        -51.338005
                                    ]
                                }
                            ]
                        },
                        {
                            "maxEirp": 14.343531047981788,
                            "maxPSD": 2.358116859436036,
                            "freqPsdPerMHz": [
                                {
                                    "freqMhz": 5975,
                                    "psdDbmMHz": [
                                        -14.040417,
                                        -2.6904573,
                                        1.6733513,
                                        2.108509,
                                        2.1151142,
                                        2.098915,
                                        2.2306547,
                                        2.358117,
                                        2.31573,
                                        1.6334858,
                                        1.5516195,
                                        2.3449402,
                                        2.3372955,
                                        2.3479948,
                                        2.3040361,
                                        2.0676537,
                                        2.0769691,
                                        1.8371782,
                                        -1.958786,
                                        -13.036552
                                    ]
                                },
                                {
                                    "freqMhz": 5955,
                                    "psdDbmMHz": [
                                        -52.035965,
                                        -51.433533,
                                        -50.91031,
                                        -50.286873,
                                        -49.658943,
                                        -48.664757,
                                        -46.432743,
                                        -43.57498,
                                        -41.284294,
                                        -38.99413,
                                        -37.21743,
                                        -35.8757,
                                        -34.596424,
                                        -33.775158,
                                        -32.529144,
                                        -31.125942,
                                        -30.17891,
                                        -29.574753,
                                        -27.36171,
                                        -21.911026
                                    ]
                                },
                                {
                                    "freqMhz": 5995,
                                    "psdDbmMHz": [
                                        -21.01612,
                                        -26.124092,
                                        -28.77647,
                                        -29.965725,
                                        -30.73948,
                                        -31.718098,
                                        -32.92418,
                                        -34.027946,
                                        -35.4373,
                                        -36.900433,
                                        -38.668053,
                                        -40.83596,
                                        -42.651997,
                                        -45.75826,
                                        -48.045956,
                                        -49.081154,
                                        -49.814713,
                                        -50.2382,
                                        -50.98371,
                                        -51.374603
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
            Example - captured one packet, scan with 40MHz bandwidth
            {
                "rfMeasurementReport": {
                    "centralFreq": 6205,
                    "channelWidth": 40,
                    "data": [
                        {
                            "maxEirp": 21.743835127037574,
                            "maxPSD": 9.997399085998536,
                            "freqPsdPerMHz": [
                                {
                                    "freqMhz": 6205,
                                    "psdDbmMHz": [
                                        -40.06205,
                                        -39.57274,
                                        -38.059616,
                                        -37.430733,
                                        -37.53958,
                                        -36.88626,
                                        -36.13594,
                                        -34.944603,
                                        -33.67262,
                                        -32.875805,
                                        -32.20833,
                                        -32.0852,
                                        -31.368721,
                                        -30.884018,
                                        -30.44078,
                                        -29.779224,
                                        -29.233276,
                                        -29.159462,
                                        -29.311665,
                                        -27.238472,
                                        -10.132347,
                                        5.159256,
                                        9.726682,
                                        9.904937,
                                        9.536005,
                                        9.069638,
                                        8.961992,
                                        9.168873,
                                        9.260004,
                                        8.6824465,
                                        8.789377,
                                        9.733511,
                                        9.997399,
                                        9.969265,
                                        9.920886,
                                        9.892937,
                                        9.752783,
                                        9.280226,
                                        5.2160273,
                                        -8.9937725
                                    ]
                                },
                                {
                                    "freqMhz": 6165,
                                    "psdDbmMHz": [
                                        -49.069668,
                                        -49.034134,
                                        -48.815876,
                                        -48.965073,
                                        -49.10223,
                                        -49.06751,
                                        -48.8534,
                                        -48.97436,
                                        -49.32901,
                                        -48.9915,
                                        -48.849518,
                                        -48.758698,
                                        -48.82367,
                                        -48.942604,
                                        -48.999935,
                                        -48.905334,
                                        -48.95941,
                                        -48.91294,
                                        -48.091095,
                                        -42.249447,
                                        -41.950905,
                                        -47.96365,
                                        -48.114197,
                                        -48.066833,
                                        -48.29618,
                                        -48.319153,
                                        -48.219902,
                                        -47.925705,
                                        -47.85924,
                                        -47.741592,
                                        -47.595806,
                                        -47.324104,
                                        -46.86893,
                                        -46.45525,
                                        -45.846035,
                                        -45.08718,
                                        -44.448063,
                                        -43.978157,
                                        -43.226227,
                                        -41.174908
                                    ]
                                },
                                {
                                    "freqMhz": 6245,
                                    "psdDbmMHz": [
                                        -28.015633,
                                        -28.991505,
                                        -28.794296,
                                        -29.320057,
                                        -30.20438,
                                        -30.693665,
                                        -31.220604,
                                        -31.3219,
                                        -31.590263,
                                        -32.036747,
                                        -32.420975,
                                        -32.63899,
                                        -33.35757,
                                        -34.31435,
                                        -34.92504,
                                        -35.626854,
                                        -36.42221,
                                        -37.440285,
                                        -38.953957,
                                        -39.141953,
                                        -39.649082,
                                        -41.08553,
                                        -42.094185,
                                        -43.122456,
                                        -44.407207,
                                        -46.15406,
                                        -47.31704,
                                        -47.787056,
                                        -48.146763,
                                        -48.389374,
                                        -48.383045,
                                        -48.483047,
                                        -48.837486,
                                        -48.818657,
                                        -49.081146,
                                        -49.147472,
                                        -49.185226,
                                        -49.399895,
                                        -49.31808,
                                        -49.22032
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }

        Notes:
            - If no packets are captured (empty list), an empty test report dictionary is returned.
            - The RF measurement report contains information such as central frequency and channel width.
            - The captured packets are added to the "data" field of the RF measurement report.
        """
        if not captured_packets:
            test_report = {}
        else:
            test_report = {
                "rfMeasurementReport": {
                    "centralFreq": (5950+ 5*channel),
                    "channelWidth": bandwidth,
                    "data": []
                }
            }

        # Process packets and store data in test_report["rfMeasurementReport"]["data"]
        return test_report

    def __spectrum_analyze(self, channel, bandwidth):
        """
        Performs spectrum analysis on a specific channel and bandwidth using RF equipment.

        Args:
            channel (int): The channel number to perform the spectrum analysis on.
            bandwidth (int): The bandwidth to be used for the analysis.

        Returns:
            dict: A list containing the captured packets.

        Notes:
            - The method configures the RF equipment for the spectrum analysis.
            - The vendor-specific binary tool is executed with elevated privileges using sudo.
            - If a "Fatal Error" is encountered during the execution, the error message is stored and an empty dictionary is returned.
        """

        # configure RF equipment

        tool_path = os.getcwd()        
        os.chdir(self.work_dir)
        std_out, std_err = InstructionLib.run_shell_command(f"sudo ./vendor_sample_binary")
        for line in std_out.splitlines():
            if "Fatal Error" in line: # vendor specific
                self.error = line
                return {}
        os.chdir(tool_path)

        # packets = self.__read_csv_file()
        packets = []

        return packets

    def __remove_resluts(self):
        """
        Removes any existing result files from the specified working directory.

        Notes:
            - If the "Results" directory exists in the working directory, all files within it are deleted.
            - This method is intended to be used as part of the setup or cleanup process to ensure a clean state for analysis.
            - The method uses the `os` module to interact with the file system and removes files one by one.
        """
        if os.path.exists(os.path.join(self.work_dir, "Results")):
            files = os.listdir(os.path.join(self.work_dir, "Results"))
            for f in files:
                file_path = os.path.join(self.work_dir, "Results",f)            
                os.remove(file_path)
