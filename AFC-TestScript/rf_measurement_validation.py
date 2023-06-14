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
import math
from commons.logger import Logger
from commons.shared_enums import (
    LogCategory,
)


class RfMeasurementValidation:
    rf_report = None
    sent_response = None
    center_freq = 0
    chwidth = 0
    resp_avail_freq_info = []
    resp_avail_chan_info = []

    def __init__(self, sent_response, rf_report):
        self.center_freq_allowed_max_psd = 0
        self.debug_printed_freq = set()

        if rf_report:
            self.rf_report = rf_report        
            self.center_freq = rf_report["rfMeasurementReport"]["centralFreq"]
            self.chwidth = rf_report["rfMeasurementReport"]["channelWidth"]
            self.packets = rf_report["rfMeasurementReport"]["data"]
            self.center_chan = (self.center_freq -5950) / 5            

        if sent_response:
            self.sent_response = sent_response
            avail_resp = sent_response["availableSpectrumInquiryResponses"][0]        
            if "availableFrequencyInfo" in avail_resp:
                self.resp_avail_freq_info = avail_resp["availableFrequencyInfo"]
            if "availableChannelInfo" in avail_resp:
                self.resp_avail_chan_info = avail_resp["availableChannelInfo"]       

    def validate_rf_measurement_by_freq(self):
        try:
            if not self.rf_report:
                return False, False
            power_valid = self.__validate_transmit_power_by_freq()
            adjacent_valid = self.__validate_psd_adjacent_frequencies()                
            return power_valid, adjacent_valid
        except Exception as err:            
            Logger.log(LogCategory.ERROR, f'validate_rf_measurement_by_freq Exception: {err}')
            return False, False

    def validate_rf_measurement_by_chan(self):
        try:
            if not self.rf_report:
                return False
            return self.__validate_transmit_power_by_chan()
        except Exception as err:            
            Logger.log(LogCategory.ERROR, f'validate_rf_measurement_by_chan Exception: {err}')
            return False

    def validate_rf_measurement_by_both(self):
        try:
            if not self.rf_report:
                return False, False
            if not self.__validate_transmit_power_by_freq():
                return False, False
            if not self.__validate_transmit_power_by_chan():
                return False, False
            adjacent_valid = self.__validate_psd_adjacent_frequencies()
            return True, adjacent_valid
        except Exception as err:            
            Logger.log(LogCategory.ERROR, f'validate_rf_measurement_by_both Exception: {err}')
            return False, False

    def validate_lpi_transmit_power(self):
        try:
            if not self.packets:
                Logger.log(LogCategory.ERROR, f'No data in rfMeasurementReport')
                return False
            for pkt in self.packets:
                if pkt["maxPSD"] > 5.0:
                    Logger.log(LogCategory.ERROR, f'Packet maxPSD {pkt["maxPSD"]} is above LPI limits 5 dBm/MHz PSD')
                    return False
            return True
        except Exception as err:
            Logger.log(LogCategory.ERROR, f'validate_lpi_transmit_power Exception: {err}')
            return False

    def validate_fc_transmit_power(self, criteria_psd):
        try:
            if not self.packets:
                Logger.log(LogCategory.ERROR, f'No data in rfMeasurementReport')
                return False
            for pkt in self.packets:
                if pkt["maxPSD"] > criteria_psd:
                    Logger.log(LogCategory.ERROR, f'Packet maxPSD {pkt["maxPSD"]} is above limits {criteria_psd} dBm/MHz PSD')
                    return False
            return True
        except Exception as err:
            Logger.log(LogCategory.ERROR, f'validate_fc_transmit_power Exception: {err}')
            return False

    def __validate_psd_adjacent_frequencies(self):
        if not self.resp_avail_freq_info and self.packets:
            Logger.log(LogCategory.ERROR, f'No available availableFrequencyInfo in availableSpectrumInquiryResponses.')
            return False

        if not self.packets:
            Logger.log(LogCategory.ERROR, f'No data in rfMeasurementReport')
            return False

        for pkt in self.packets:
            for psd_info in pkt["freqPsdPerMHz"]:
                if not self.__validate_psd(psd_info["freqMhz"], self.chwidth, psd_info["psdDbmMHz"]):
                    return False
        return True

    def __validate_psd(self, freq, chwidth, psdDbmMHz):
        match_freq_ranges = self.__get_match_freq_ranges(freq, chwidth)
        # if not match_freq_ranges:
        #     if self.center_freq_allowed_max_psd:
        #         allowed_max_psd = self.center_freq_allowed_max_psd
        #         Logger.log(LogCategory.DEBUG, f'__validate_psd : freq {freq} chwidth {chwidth}, can not find matched frequence ranges in availableSpectrumInquiryResponses.')
        #         Logger.log(LogCategory.DEBUG, f'Use center_freq {self.center_freq} allowed_max_psd {allowed_max_psd}')
        #     else:
        #         Logger.log(LogCategory.ERROR, f'__validate_psd : freq {freq} chwidth {chwidth}, can not find matched frequence ranges in availableSpectrumInquiryResponses.')
        #         return False
        if not match_freq_ranges and (self.center_freq != freq):
            # We don't have to check PSD values for adjacent frequencies
            #   that are not available in the AFC response mask.
            return True
        else:
            allowed_max_psd = min([psd for l,h,psd in match_freq_ranges])
            if not self.center_freq_allowed_max_psd and (self.center_freq == freq):
                self.center_freq_allowed_max_psd = allowed_max_psd
                Logger.log(LogCategory.DEBUG, f'self.center_freq {self.center_freq} allowed_max_psd {allowed_max_psd}')
        #Logger.log(LogCategory.DEBUG, f'__validate_psd: freq {freq} chwidth {chwidth} permitted max psd {allowed_max_psd} ')

        for psd in psdDbmMHz:
            if psd > allowed_max_psd:
                Logger.log(LogCategory.ERROR, f'packet psdDbmMHz {psd} is greater than permitted PSD {allowed_max_psd}')
                return False
        return True

    def __validate_transmit_power_by_freq(self):                               
        if not self.resp_avail_freq_info and self.packets:
            Logger.log(LogCategory.ERROR, f'No available availableFrequencyInfo in availableSpectrumInquiryResponses.')
            return False

        if not self.packets:
            Logger.log(LogCategory.ERROR, f'No data in rfMeasurementReport')
            return False

        match_freq_ranges = self.__get_match_freq_ranges(self.center_freq, self.chwidth)
        if not match_freq_ranges:
            Logger.log(LogCategory.ERROR, f'freq {self.center_freq} chwidth {self.chwidth}: can not find matched frequence ranges in availableSpectrumInquiryResponses.')
            return False

        allowed_max_psd = min([psd for l,h,psd in match_freq_ranges])
        Logger.log(LogCategory.DEBUG, f'allowed_max_psd {allowed_max_psd}')
        for pkt in self.packets:
            if pkt["maxPSD"] > allowed_max_psd:
                Logger.log(LogCategory.ERROR, f'packet maxPSD {pkt["maxPSD"]} is greater than permitted max PSD {allowed_max_psd}')
                return False

        return True

    def __validate_transmit_power_by_chan(self):
        if not self.resp_avail_chan_info and self.packets:
            Logger.log(LogCategory.ERROR, f'No available availableChannelInfo in availableSpectrumInquiryResponses.')
            return False

        if not self.packets:
            Logger.log(LogCategory.ERROR, f'No data in rfMeasurementReport')
            return False

        max_eirp = get_channel_max_eirp(self.center_chan, self.resp_avail_chan_info)
        if not max_eirp:
            Logger.log(LogCategory.ERROR, f'channelCfi {self.center_chan} is not avaliable in availableChannelInfo of availableSpectrumInquiryResponses.')
            return False

        for pkt in self.packets:
            if pkt["maxEirp"] > max_eirp:
                Logger.log(LogCategory.ERROR, f'packet EIRP {pkt["maxEirp"]} is greater than Max EIRP {max_eirp}')
                return False
        
        return True

    def __get_match_freq_ranges(self, freq, chwidth):
        freq_range = (int(freq - chwidth/2), int(freq + chwidth/2))
        match_freq_range = []        
        for item in self.resp_avail_freq_info:
            item_freq_range = item["frequencyRange"]
            if is_matched_freq_range((item_freq_range["lowFrequency"], item_freq_range["highFrequency"]) , freq_range):
                match_freq_range.append((item_freq_range["lowFrequency"], item_freq_range["highFrequency"], item["maxPsd"]))
        
        if freq not in self.debug_printed_freq:
            self.debug_printed_freq.add(freq)
            Logger.log(LogCategory.DEBUG, f'--------------------------------------------------------------')
            Logger.log(LogCategory.DEBUG, f'freq {freq} chwidth {chwidth} freq_range {freq_range}')
            Logger.log(LogCategory.DEBUG, f'match_freq_range {match_freq_range}')
        return match_freq_range
    
    def get_sp_limit_by_freq(self, freq, chwidth):
        match_freq_ranges = self.__get_match_freq_ranges(freq, chwidth)
        if match_freq_ranges:
            return min([psd for l,h,psd in match_freq_ranges])
        else:
            return None

    def get_sp_limit_by_chan(self, channel):
        max_eirp = get_channel_max_eirp(channel, self.resp_avail_chan_info)
        if not max_eirp:
            Logger.log(LogCategory.ERROR, f'channelCfi {channel} is not avaliable in availableChannelInfo of availableSpectrumInquiryResponses..')
            return None
        return max_eirp

    def get_sp_limit_by_both(self, channel, chwidth):
        psd = self.get_sp_limit_by_freq(int(5950 + channel*5), chwidth)
        eirp = self.get_sp_limit_by_chan(channel)
        return psd, eirp

def is_matched_freq_range(resp_freq_range, report_freq_range):
    l, h = resp_freq_range
    report_low, report_high = report_freq_range
    if l >= report_low and h <= report_high:
        return True
    return False

def get_channel_max_eirp(channel, resp_chan_info):
    for item in resp_chan_info:
        if channel in item["channelCfi"]:
            idx = item["channelCfi"].index(channel)
            max_eirp = item["maxEirp"][idx]            
            Logger.log(LogCategory.DEBUG, f"channel {channel} idx {idx} max_eirp {max_eirp}")
            return max_eirp

    return None


