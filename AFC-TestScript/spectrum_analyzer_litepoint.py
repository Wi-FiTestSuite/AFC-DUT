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
from commons.shared_enums import SettingsName
from commons.logger import Logger
from commons.shared_enums import (
    LogCategory,
)

# (channel, bandwidth)
all_channels_6g = [(15, 160), (47, 160), (79, 160), (111, 160), (143, 160), (175, 160)]

class SpectrumAnalyzer:

    work_dir = "/usr/local/bin/WFA-QuickTrack-Tool/QuickTrack-Tool/Test-Services/AppData/IQsniffer/"
    result_csv_file_name = None
    pcap_support = True
    # Sampling rate (MHz)
    sampling_rate_mhz 	= 480
    # Capture length (ms). Maximum length is limited by sampling rate: 3350ms for 40MHz, 1675ms for 80MHz, 838ms for 160MHz, 559ms for 240MHz and 279ms for 480MHz
    capture_ms  		= 250
    uni_path_loss = True

    def __init__(self):
        self.captured_packets = {}
        self.trigger_source = "IMMediate"
        self.packet_duration = 0
        self.packet_duration_list = []
        self.rfdq_margin_us = 10
        self.repeat = 1
        self.address = InstructionLib.get_setting(SettingsName.SPECTRUM_ANALYZER_IP)
        self.rf_ports = InstructionLib.get_setting(SettingsName.SPECTRUM_ANALYZER_RF_PORTS)
        self.error = None
        self.vsa_rlev_auto = False

    def spectrum_analyzer_connect(self):
        self.capture_ms = 10
        self.__spectrum_analyze(1, 20)
        if self.error and "Could not connect to" in self.error:
            Logger.log(LogCategory.ERROR, f"Could not connect to Spectrum Analyzer tester {self.address}")
            return False
        return True

    def spectrum_analyze_all(self, timeout):
        try:
            round = 0
            self.vsa_rlev_auto = False
            self.__remove_resluts()
            start = os.times()[4]
            test_report_list = []
            while True:
                round += 1
                for ch, bw in all_channels_6g:
                    pkts = self.__spectrum_analyze(channel=ch, bandwidth=bw, csv_file_name=f'IQsniffer_results_ch{ch}_bw{bw}_round{round}.csv')                    
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
        try:
            round = 0
            self.vsa_rlev_auto = True
            self.__remove_resluts()

            if not self.spectrum_analyze_pre_run(channel, bandwidth):
                Logger.log(LogCategory.ERROR, f"Error: No packets found in the channel {channel} on RF port {self.rf_ports}")
                return {}
            Logger.log(LogCategory.DEBUG, f"Pre-run detected packet duration: {self.packet_duration_list}")
            self.__remove_resluts()
            self.trigger_source = "RFDQ"
            self.repeat = 10
            start = os.times()[4]
            captured_packets = []
            while True:
                round += 1
                for duration in self.packet_duration_list:
                    self.packet_duration = duration
                    duration_ms = math.ceil(self.packet_duration/1000)
                    self.capture_ms = duration_ms + 1
                    captured_packets.extend(self.__spectrum_analyze(
                        channel=channel, bandwidth=bandwidth, csv_file_name=f'IQsniffer_results_ch{channel}_bw{bandwidth}_round{round}.csv'))

                now = os.times()[4]
                remaining = start + timeout - now
                if remaining <= 0:
                    break
            return self.generate_report(channel, bandwidth, captured_packets, use_psd = True)
        except Exception as err:
            exception_str = traceback.format_exc()
            Logger.log(LogCategory.ERROR, f'spectrum_analyze Exception: {exception_str}')
            return {}

    def generate_report(self, channel, bandwidth, captured_packets, use_psd = False):
        """
        Generates a report based on the captured packets.

        Args:
            channel (int): The channel number.
            bandwidth (int): The bandwidth value.
            captured_packets (list): The list of captured packets.
            use_psd (bool, optional): Flag to indicate whether to include PSD (Power Spectral Density) information
                                    in the report. Defaults to False.

        Returns:
            dict: The generated report in the following format:
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

        Notes:
            - The method checks if there are captured packets available.
            - If no captured packets are available, an empty dictionary is returned as the report.
            - If captured packets are available, the report structure is created with the channel's central frequency,
             bandwidth, and an empty list for data.
            - If `use_psd` is True, the method processes the captured packets for PSD information and adds it to the report.
            - If `use_psd` is False, the method adds the maximum EIRP and
              maximum PSD values from each packet to the report.
            - The log messages are generated to indicate the number of captured packets and the channel information.
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
            if use_psd:
                Logger.log(LogCategory.DEBUG, f"Captured {len(captured_packets)/3} packets in channel {channel} bandwidth {bandwidth}")
                freq_psd_per_mHz = []
                for idx, pkt in enumerate(captured_packets):
                    if int(float(pkt["freq_mhz"])) == self.__convert_ch_to_freq(channel):
                        max_eirp = float(pkt["channel_power_dbm"])
                        max_psd = float(pkt["peak_psd_dbm_mhz"])
                    freq_psd_per_mHz.append({
                        "freqMhz": int(float(pkt["freq_mhz"])),
                        "psdDbmMHz": pkt["psd_dbm_mhz"]
                    })
                    if (idx % 3) == 2:
                        test_report["rfMeasurementReport"]["data"].append(
                            {"maxEirp": max_eirp, "maxPSD": max_psd,
                            "freqPsdPerMHz": freq_psd_per_mHz})
                        freq_psd_per_mHz = []                
            else:
                Logger.log(LogCategory.DEBUG, f"Captured {len(captured_packets)} packets in channel {channel} bandwidth {bandwidth}")
                for pkt in captured_packets:
                    if pkt['packetPower'] and pkt['peakPsdDbmMHz']:
                        test_report["rfMeasurementReport"]["data"].append(
                            {"maxEirp": float(pkt['packetPower']), "maxPSD": float(pkt['peakPsdDbmMHz'])})

        return test_report

    def __spectrum_analyze(self, channel, bandwidth, csv_file_name = None):

        self.__config_ini(channel, bandwidth, csv_file_name)

        tool_path = os.getcwd()        
        os.chdir(self.work_dir)
        std_out, std_err = InstructionLib.run_shell_command(f"sudo ./IQsniffer_test")
        for line in std_out.splitlines():
            if "Fatal Error" in line:
                self.error = line
                return {}
        os.chdir(tool_path)
        packets = self.__read_csv_file()

        return packets

    def spectrum_analyze_pre_run(self, channel, bandwidth):
        self.__remove_resluts()
        packets = (self.__spectrum_analyze(
            channel=channel, bandwidth=bandwidth, csv_file_name=f'IQsniffer_results_ch{channel}_bw{bandwidth}_pre-run.csv'))
        if not packets:
            return False
        for pkt in packets:
            if pkt["packetDurationUs"] != '':
                new_pkt_dur = int(float(pkt["packetDurationUs"]))
            else:
                new_pkt_dur = int(float(pkt["ofdmPacketDurationUs"]))
            out_of_margin = True
            for dur in self.packet_duration_list:
                if abs(dur - new_pkt_dur) <= self.rfdq_margin_us:
                    out_of_margin = False                        
                    break
            if out_of_margin:
                self.packet_duration_list.append(new_pkt_dur)
        self.spectrum_upload_support_data("spectrum_analyze_pre_run")
        return True

    def __config_ini(self, channel, bandwidth, csv_file_name):                  
        ini_file_path = os.path.join(self.work_dir, "lp_scpi_runner.ini")
        if not os.path.isfile(ini_file_path + ".bak"):
            shutil.copy(ini_file_path, ini_file_path + ".bak")

        config = configparser.ConfigParser()
        config.read(ini_file_path)

        config.set('options', 'address', self.address)
        config.set('set', 'band', '6G')
        config.set('set', 'channel', f'{channel}')
        config.set('set', 'bw_mhz', f'{bandwidth}')
        config.set('set', 'rf_ports', self.rf_ports)
        config.set('set', 'sampling_rate_mhz', f'{self.sampling_rate_mhz}')
        config.set('set', 'capture_ms', f'{self.capture_ms}')
        config.set('set', 'trigger_source', f'{self.trigger_source}')
        config.set('set', 'repeat', f'{self.repeat}')
        config.set('set', 'ul_ofdma', '0')
        if self.vsa_rlev_auto:            
            config.set('set', 'vsa_rlev_auto', '1')
            config.set('set', 'vsa_rlev_auto_time_ms', '200')
            config.set('set', 'vsa_rlev_dbm', '0')
        else:
            config.set('set', 'vsa_rlev_auto', '0')
            config.set('set', 'vsa_rlev_dbm', '20')
        config.set('set', 'pcap_support', '1' if self.pcap_support else '0')
        config.set('set', 'uni_path_loss', '1' if self.uni_path_loss else '0')

        if self.trigger_source == "RFDQ":
            config.set('set', 'rfdq_packet_length_us', f'{self.packet_duration}')
            config.set('set', 'rfdq_margin_us', f'{self.rfdq_margin_us}')            
            scan_list = f"{self.__convert_ch_to_freq(channel)}"
            lower_chan = channel - (bandwidth/10)*2
            higher_chan = channel + (bandwidth/10)*2
            if lower_chan > 0:
                scan_list = scan_list + f", {self.__convert_ch_to_freq(lower_chan)}"
            if higher_chan < 185:
                scan_list = scan_list + f", {self.__convert_ch_to_freq(higher_chan)}"
            config.set('set', 'freq_mhz_scan_list', f'{scan_list}')
            config.set('set', 'channel', '')
            config.set('set', 'freq_mhz', f'{self.__convert_ch_to_freq(channel)}')
        else:
            config.set('set', 'freq_mhz_scan_list', "")
            config.set('set', 'freq_mhz', '')
            

        if csv_file_name:
            self.result_csv_file_name = csv_file_name
        else:
            self.result_csv_file_name = f'IQsniffer_results_ch{channel}_bw{bandwidth}.csv'
        config.set('set', 'result_csv_file_name', self.result_csv_file_name)

        with open(ini_file_path, 'w') as configfile:
            config.write(configfile)

    def __remove_resluts(self):
        if os.path.exists(os.path.join(self.work_dir, "Results")):
            files = os.listdir(os.path.join(self.work_dir, "Results"))
            for f in files:
                file_path = os.path.join(self.work_dir, "Results",f)            
                os.remove(file_path)

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
        if os.path.exists(os.path.join(self.work_dir, "Results")):
            files = os.listdir(os.path.join(self.work_dir, "Results"))
            for f in files:
                file_path = os.path.join(self.work_dir, "Results",f)
                if f.endswith('.pcap') and os.path.getsize(file_path) > 0:
                    shutil.copy(file_path, os.path.join(InstructionLib.get_current_testcase_log_dir(), f.replace("IQsniffer_pcap", step)))
                if f.endswith('.csv') and os.path.getsize(file_path) > 0 and 'IQsniffer_results' in f:
                    shutil.copy(file_path, os.path.join(InstructionLib.get_current_testcase_log_dir(), f.replace("IQsniffer_results", step)))

    def __read_csv_file(self):
        if self.trigger_source == "RFDQ":
            csv_filename = os.path.join(self.work_dir, "Results", self.result_csv_file_name.replace(".csv", "_psd.csv") )
        else:    
            csv_filename = os.path.join(self.work_dir, "Results", self.result_csv_file_name)

        if not os.path.isfile(csv_filename):
            self.result_csv_file_name = None
            Logger.log(LogCategory.DEBUG, f"csv file {csv_filename} does not exist")
            return {}

        with open(csv_filename) as f:
            pkts = [{k: v for k, v in row.items()}
                for row in csv.DictReader(f, skipinitialspace=True)]

        if self.trigger_source == "RFDQ":
            psd_pkts = []
            freq = 0
            for pkt in pkts:
                psd = float(pkt["psd_dbm_mhz"])
                if freq != pkt["freq_mhz"]:
                    freq = pkt["freq_mhz"]
                    pkt["psd_dbm_mhz"] = [psd]
                    psd_pkts.append(pkt)
                else:
                    psd_pkts[-1]["psd_dbm_mhz"].append(psd)
            pkts = psd_pkts

        return pkts

    def __convert_ch_to_freq(self, channel):
        return int(5950 + channel*5)

