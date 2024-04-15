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

import math
import json
import os
import re
import traceback

from IndigoTestScripts.TestScript import TestScript
from IndigoTestScripts.helpers.instruction_lib import InstructionLib
from commons.shared_enums import (
    OperationalBand, DutType, SettingsName, UiPopupButtons
)
from IndigoTestScripts.Programs.AFC.afc_enums import AFCParams, GeoArea, Deployment
from IndigoTestScripts.Programs.AFC.afc_lib import AFCLib
from IndigoTestScripts.Programs.AFC.rf_measurement_validation import RfMeasurementValidation
from IndigoTestScripts.Programs.AFC.spectrum_analyzer_lib import SpectrumAnalyzerLib

class AFCBaseScript(TestScript):
    def __init__(self, dut_type):
        self.operational_band = OperationalBand._6GHz.value
        self.dut_type = dut_type
        InstructionLib.set_dut_type(dut_type)
        self.auto_rf_tester = True
        self.power_valid_desc = "AFC DUT conforms to the conditons in the Spectrum Inquiry Response"
        self.afcd_country_code = InstructionLib.get_setting(SettingsName.AFCD_COUNTRY_CODE)

    def setup(self, http_conf = "afc-https-default", stop_ocsp = False):
        InstructionLib.afcd_operation({AFCParams.DEVICE_RESET.value: 1})
        # start ocsp server before web server !        
        if 'run-6' in http_conf:
            InstructionLib.start_ocsp_server(8888, "-nmin 1")
            InstructionLib.start_web_server(http_conf, test_ocsp=True)
        else:
            InstructionLib.start_ocsp_server(8888)
            InstructionLib.start_web_server(http_conf)

        if stop_ocsp:
            InstructionLib.stop_ocsp_server(8888)
        # Reset AFC simulator Test Vector
        AFCLib.reset_afc("setup")
        InstructionLib.set_band(self.operational_band)
        self.test_ssid = InstructionLib.get_setting(
            SettingsName.TEST_SSID
        ) + InstructionLib.get_setting(SettingsName.INSTALLER_EPOCH_TIME)
        self.band = InstructionLib.get_hw_mode(self.operational_band)

        self.server_conf = AFCBaseScript.add_server_conf()
        need_bss_conf = InstructionLib.get_setting(SettingsName.AFCD_NEED_BSS_CONF)
        if need_bss_conf and (self.dut_type == DutType.APUT):
            self.bss_conf = AFCBaseScript.add_bss_conf()
        else:
            self.bss_conf = {}
        self.need_reg_conf = InstructionLib.get_setting(SettingsName.AFCD_NEED_REG_INFO)
        if self.need_reg_conf:
            self.geo_area = InstructionLib.get_setting(SettingsName.AFCD_GEOGRAPHIC_TYPE)
            reg_conf = AFCBaseScript.combine_configs(
                AFCBaseScript.dev_desc_conf(afcd_country_code=self.afcd_country_code),
                AFCBaseScript.location_conf(geo_area=self.geo_area, afcd_country_code=self.afcd_country_code),
                AFCBaseScript.freq_channel_conf(afcd_country_code=self.afcd_country_code),
                AFCBaseScript.misc_conf()
            )
        else:
            reg_conf = {}
        self.afc_config = AFCBaseScript.combine_configs(
            self.server_conf,
            self.bss_conf,
            reg_conf
        )        
        self.power_cycle_timeout = InstructionLib.get_setting(SettingsName.AFCD_POWER_CYCLE_TIMEOUT)
        self.delay_apply_follow_on_response = InstructionLib.get_setting(SettingsName.AFCD_APPLY_POWER_LIMIT_DELAY)
        op_type = InstructionLib.get_setting(SettingsName.SPECTRUM_ANALYZER_OP_TYPE)
        if "manual" in op_type.lower():
            self.auto_rf_tester = False

        if self.dut_type == DutType.APUT:
            self.lpi_support = InstructionLib.get_setting(SettingsName.AFCD_APPROVED_LPI_OPERATION)
        else:
            self.lpi_support = False
        self.current_testcase_log_dir = InstructionLib.get_current_testcase_log_dir()

    def execute(self):
        pass

    def teardown(self):
        AFCLib.reset_afc("teardown")
        self.collect_rf_measurement_data()

    def get_testscript_version(self):
        pass

    def get_description(self):
        if not hasattr(self, "description"):
            self.description = ""
        return self.description

    def check_RF_test_result_manually(self, lpi_message, sp_message, title):
        if self.lpi_support:
            message = lpi_message
        else:
            message = sp_message

        InstructionLib.post_popup_message(
            message,
            [UiPopupButtons.POP_UP_BUTTON_PASS, UiPopupButtons.POP_UP_BUTTON_FAIL],
            title,
            UiPopupButtons.POP_UP_BUTTON_FAIL,
        )
        user_button, user_input = InstructionLib.get_popup_response()
        if user_button == UiPopupButtons.POP_UP_BUTTON_PASS:
            power_valid = True
        else:
            power_valid = False
        return power_valid

    def monitor_allchans_sp_operation(self, rf_report_file, timeout=0, extra_info=""):
        if self.auto_rf_tester:
            if timeout:
                InstructionLib.log_info(f"During the {timeout} seconds wait time: RF Test Equipment is monitoring the output of the DUT...")
            else:
                InstructionLib.log_info("RF Test Equipment is monitoring the output of the DUT...")
            report_list = SpectrumAnalyzerLib().spectrum_analyze_all(timeout)
            self.save_rf_measurement_report(report_list, rf_report_file)
            SpectrumAnalyzerLib().spectrum_upload_support_data(re.search(r"step_\d+", rf_report_file).group())
            sp_operation = False
            for report in report_list:
                if report:
                    if self.lpi_support:                
                        if not RfMeasurementValidation({} , report).validate_lpi_transmit_power():
                            return True
                    else:
                        InstructionLib.log_error(f'The AFC DUT should not transmit in the band if the AFC DUT supports only SP operation')
                        return True
        else:
            if timeout:
                title = f"During the {timeout} seconds wait time: RF Test Equipment monitors the output of the AFC DUT on all 6GHz channels"
            else:
                title = "RF Test Equipment monitors the output of the AFC DUT on all 6GHz channels"
            sp_operation = not self.check_RF_test_result_manually(
                "Confirm that the AFC DUT does not transmit above LPI limits, 5 dBm/MHz PSD" + extra_info,
                "Confirm that the AFC DUT does not transmit in the band" + extra_info,
                title)
        return sp_operation

    def validate_fc_transmit_power(self, rf_report_file, timeout=0, extra_info=""):
        if self.auto_rf_tester:
            if timeout:
                InstructionLib.log_info(f"During the {timeout} seconds wait time: RF Test Equipment is monitoring the output of the DUT...")
            else:
                InstructionLib.log_info("RF Test Equipment is monitoring the output of the DUT...")
            report_list = SpectrumAnalyzerLib().spectrum_analyze_all(timeout)
            self.save_rf_measurement_report(report_list, rf_report_file)
            SpectrumAnalyzerLib().spectrum_upload_support_data(re.search(r"step_\d+", rf_report_file).group())
            power_valid = True
            for report in report_list:
                if report:
                    criteria_max_psd = (8 - 6) # 8: from SP AP's default vector
                    power_valid = RfMeasurementValidation({} , report).validate_fc_transmit_power(criteria_max_psd)
                    if not power_valid:
                        return False
        else:
            if timeout:
                title = f"During the {timeout} seconds wait time: RF Test Equipment monitors the output of the AFC DUT on all 6GHz channels"
            else:
                title = "RF Test Equipment monitors the output of the AFC DUT on all 6GHz channels"
            power_valid = self.check_RF_test_result_manually(
                "Confirm that the AFC DUT does not transmit above maximum transmit power limits advertised by the Standard Power Access Point for Standard Client Devices in the channel" + extra_info,
                "Confirm that the AFC DUT does not transmit above maximum transmit power limits advertised by the Standard Power Access Point for Standard Client Devices in the channel" + extra_info,
                title)
        return power_valid

    def validate_rf_measurement_by_freq(self, sent_resp, op_channel, rf_report_file, op_bandwidth=20):        
        cfi = op_channel if op_bandwidth == 20 else self.get_cfi_from_op_channel(op_channel, op_bandwidth)
        if cfi == 0:
            InstructionLib.log_error(f"AFC DUT's operating channel {op_channel} is not correct primary 20 MHz channel")
            return False, False

        op_freq = int(5950 + cfi*5)
        sp_limit_psd = RfMeasurementValidation(sent_resp , {}).get_sp_limit_by_freq(op_freq, op_bandwidth)

        if op_bandwidth == 20:
            channel_str = "channel"
        else:
            channel_str = "channel center frequency index"
        if self.lpi_support:
            self.power_valid_desc = f"AFC DUT transmit power in the band is less than CEILING[LPI limits (5 dBm/MHz PSD) , SP limits ({sp_limit_psd} dBm/MHz PSD) in Spectrum Reponse] on {channel_str} {cfi} bandwidth {op_bandwidth}."
        else:
            self.power_valid_desc = f"AFC DUT conforms to the conditions in Spectrum Response ({sp_limit_psd} dBm/MHz PSD) on {channel_str} {cfi} bandwidth {op_bandwidth}."

        if sp_limit_psd is None:
            InstructionLib.log_error(f"AFC DUT's frequence {op_freq} {channel_str} {cfi} bandwidth {op_bandwidth}: The use of an unavailable spectrum is prohibited.")
            return False, False

        if self.auto_rf_tester:
            InstructionLib.log_info(f"RF Test Equipment is monitoring the output of the AFC DUT on {channel_str} {cfi} bandwidth {op_bandwidth} ...")
            report = SpectrumAnalyzerLib().spectrum_analyze(cfi, op_bandwidth)
            self.save_rf_measurement_report(report, rf_report_file)
            SpectrumAnalyzerLib().spectrum_upload_support_data(re.search(r"step_\d+", rf_report_file).group())
            power_valid, adjacent_valid = RfMeasurementValidation(sent_resp, report).validate_rf_measurement_by_freq()
            self.power_valid_desc += f" - Measurement Report: ./{os.path.basename(self.current_testcase_log_dir.rstrip('/'))}/{rf_report_file}"
        else:
            title = f"RF Test Equipment monitors the output of the AFC DUT on {channel_str} {cfi} bandwidth {op_bandwidth}"            
            lpi_message = f"Confirm that the AFC DUT transmit power in the band is less than CEILING[LPI limits (5 dBm/MHz PSD) , SP limits ({sp_limit_psd} dBm/MHz PSD) in Spectrum Reponse] and does not exceed limits in adjacent frequencies"
            sp_message = f"Confirm that the AFC DUT conforms to the conditions in Spectrum Response ({sp_limit_psd} dBm/MHz PSD) and does not exceed emissoins limits in adjacent frequencies"
            if(self.dut_type == DutType.STAUT):
                lpi_message = sp_message
            power_valid = adjacent_valid = self.check_RF_test_result_manually(
                lpi_message,
                sp_message,
                title)

        return power_valid, adjacent_valid

    def validate_rf_measurement_by_chan(self, sent_resp, op_channel, rf_report_file, op_bandwidth=20):
        cfi = op_channel if op_bandwidth == 20 else self.get_cfi_from_op_channel(op_channel, op_bandwidth)
        if cfi == 0:
            InstructionLib.log_error(f"DUT's operating channel {op_channel} is not correct primary 20 MHz channel")
            return False
        op_freq = int(5950 + cfi*5)
        sp_limit_eirp = RfMeasurementValidation(sent_resp , {}).get_sp_limit_by_chan(cfi)

        if op_bandwidth == 20:
            channel_str = "channel"
        else:
            channel_str = "channel center frequency index"
        if self.lpi_support:
            self.power_valid_desc = f"AFC DUT transmit power in the band is less than CEILING[LPI limits (5 dBm/MHz PSD) , SP limits ({sp_limit_eirp} dBm EIRP) in Spectrum Reponse] on {channel_str} {cfi} bandwidth {op_bandwidth}."
        else:
            self.power_valid_desc = f"AFC DUT conforms to the conditions in Spectrum Response ({sp_limit_eirp} dBm EIRP) on {channel_str} {cfi} bandwidth {op_bandwidth}."

        if sp_limit_eirp is None:
            InstructionLib.log_error(f"DUT's frequence {op_freq} {channel_str} {cfi} bandwidth {op_bandwidth}: The use of an unavailable spectrum is prohibited.")
            return False

        if self.auto_rf_tester:
            InstructionLib.log_info(f"RF Test Equipment is monitoring the output of the AFC DUT on {channel_str} {cfi} bandwidth {op_bandwidth} ...")
            report = SpectrumAnalyzerLib().spectrum_analyze(cfi, op_bandwidth)
            self.save_rf_measurement_report(report, rf_report_file)
            SpectrumAnalyzerLib().spectrum_upload_support_data(re.search(r"step_\d+", rf_report_file).group())
            power_valid = RfMeasurementValidation(sent_resp , report).validate_rf_measurement_by_chan()
            self.power_valid_desc += f" - Measurement Report: ./{os.path.basename(self.current_testcase_log_dir.rstrip('/'))}/{rf_report_file}"
        else:
            title = f"RF Test Equipment monitors the output of the AFC DUT on {channel_str} {cfi} bandwidth {op_bandwidth}"
            lpi_message = f"Confirm that the AFC DUT transmit power in the band is less than CEILING[LPI limits (5 dBm/MHz PSD) , SP limits ({sp_limit_eirp} dBm EIRP) in Spectrum Reponse] and does not exceed limits in adjacent frequencies"
            sp_message = f"Confirm that the AFC DUT conforms to the conditions in Spectrum Response ({sp_limit_eirp} dBm EIRP) and does not exceed emissoins limits in adjacent frequencies"
            if(self.dut_type == DutType.STAUT):
                lpi_message = sp_message
            power_valid = self.check_RF_test_result_manually(
                lpi_message,
                sp_message,
                title)

        return power_valid

    def validate_rf_measurement_by_both(self, sent_resp, op_channel, rf_report_file, op_bandwidth=20):
        cfi = op_channel if op_bandwidth == 20 else self.get_cfi_from_op_channel(op_channel, op_bandwidth)
        if cfi == 0:
            InstructionLib.log_error(f"DUT's operating channel {op_channel} is not correct primary 20 MHz channel")
            return False, False
        op_freq = int(5950 + cfi*5)
        sp_limit_psd,  sp_limit_eirp = RfMeasurementValidation(sent_resp , {}).get_sp_limit_by_both(cfi, op_bandwidth)

        if op_bandwidth == 20:
            channel_str = "channel"
        else:
            channel_str = "channel center frequency index"
        if self.lpi_support:
            self.power_valid_desc = f"AFC DUT transmit power in the band is less than CEILING[LPI limits (5 dBm/MHz PSD) , SP limits ({sp_limit_psd} dBm/MHz PSD, {sp_limit_eirp} dBm EIRP) in Spectrum Reponse] on {channel_str} {cfi} bandwidth {op_bandwidth}."
        else:
            self.power_valid_desc = f"AFC DUT conforms to the conditions in Spectrum Response ({sp_limit_psd} dBm/MHz PSD, {sp_limit_eirp} dBm EIRP) on {channel_str} {cfi} bandwidth {op_bandwidth}."

        if sp_limit_psd is None or sp_limit_eirp is None:
            InstructionLib.log_error(f"DUT's center frequence {op_freq} {channel_str} {cfi} bandwidth {op_bandwidth}: The use of an unavailable spectrum is prohibited.")
            return False, False

        if self.auto_rf_tester:
            InstructionLib.log_info(f"RF Test Equipment is monitoring the output of the AFC DUT on {channel_str} {cfi} bandwidth {op_bandwidth} ...")
            report = SpectrumAnalyzerLib().spectrum_analyze(cfi, op_bandwidth)
            self.save_rf_measurement_report(report, rf_report_file)
            SpectrumAnalyzerLib().spectrum_upload_support_data(re.search(r"step_\d+", rf_report_file).group())
            power_valid, adjacent_valid = RfMeasurementValidation(sent_resp , report).validate_rf_measurement_by_both()        
            self.power_valid_desc += f" - Measurement Report: ./{os.path.basename(self.current_testcase_log_dir.rstrip('/'))}/{rf_report_file}"
        else:
            if sp_limit_psd is not None and sp_limit_eirp is not None:
                title = f"RF Test Equipment monitors the output of the AFC DUT on {channel_str} {cfi} bandwidth {op_bandwidth}"
                lpi_message = f"Confirm that the AFC DUT transmit power in the band is less than CEILING[LPI limits (5 dBm/MHz PSD) , SP limits ({sp_limit_psd} dBm/MHz PSD, {sp_limit_eirp} dBm EIRP) in Spectrum Reponse] and does not exceed limits in adjacent frequencies"
                sp_message = f"Confirm that the AFC DUT conforms to the conditions in Spectrum Response ({sp_limit_psd} dBm/MHz PSD, {sp_limit_eirp} dBm EIRP) and does not exceed emissoins limits in adjacent frequencies"
                if(self.dut_type == DutType.STAUT):
                    lpi_message = sp_message
                power_valid = adjacent_valid = self.check_RF_test_result_manually(
                    lpi_message,
                    sp_message,
                    title)

        return power_valid, adjacent_valid

    def collect_rf_measurement_data(self):
        script_name = self.__class__.__name__
        if not self.auto_rf_tester and "USV35" not in script_name:
            title = script_name
            default_button = UiPopupButtons.POP_UP_BUTTON_OK
            InstructionLib.post_popup_message(
                "Please collect all RF Test Equipment measurement data related to this test case before running next one",
                [UiPopupButtons.POP_UP_BUTTON_OK],
                title,
                default_button,
            )
            user_button, user_input = InstructionLib.get_popup_response()

    @staticmethod
    def dev_desc_conf(serial_number="SN000",
            cert_id="CID000", afcd_country_code="US"):
        dev_config = {}
        mapping = {
            'US' : 'US_47_CFR_PART_15_SUBPART_E',
            'CA': 'CA_RES_DBS-06'
        }
        if afcd_country_code in mapping:
            ruleset_id = mapping[afcd_country_code]
        else:
            ruleset_id = 'US_47_CFR_PART_15_SUBPART_E'
        dev_config[AFCParams.SERIAL_NUMBER.value] = serial_number
        dev_config[AFCParams.CERT_ID.value] = cert_id
        dev_config[AFCParams.RULE_SET_ID.value] = ruleset_id

        return dev_config

    @staticmethod
    def location_conf(geo_area="Ellipse", afcd_country_code="US", loc_idx = 0, major_axis=150, minor_axis=150, orient=0, boundary=None,
            height=15, height_type="AGL", vert_uncert=2, deploy=Deployment.Unknown.value):
        mapping = {'US': [{"longitude": "-121.98586998164663", "latitude": "37.38193354300452",
                            "boundary": "-121.9875329371091,37.382479218209305 -121.98371347155712,37.38271792164739 -121.98558028898755,37.37992163368795"},
                          {"longitude": "-97.73618564630566", "latitude": "30.401878963715333",
                            "boundary": "-97.7375329371091,30.402479218209305 -97.73371347155712,30.40271792164739 -97.73558028898755,30.40992163368795"}],
                   'CA': [{"longitude": "-75.70159962256518", "latitude": "45.420456011708055",
                            "boundary": "-75.7075329371091,45.422479218209305 -75.70371347155712,45.42271792164739 -75.70558028898755,45.42992163368795"},
                          {"longitude": "-106.66750238414373", "latitude": "52.15676450871561",
                            "boundary": "-106.6675329371091,52.152479218209305 -106.66371347155712,52.15271792164739 -106.66558028898755,52.15992163368795"}]}
        longitude = mapping[afcd_country_code][loc_idx]["longitude"]
        latitude = mapping[afcd_country_code][loc_idx]["latitude"]
        boundary = mapping[afcd_country_code][loc_idx]["boundary"]
        loca_config = {}
        if geo_area == "Ellipse":
            loca_config[AFCParams.LOCATION_GEO_AREA.value] = GeoArea.Ellipse.value
            loca_config[AFCParams.ELLIPSE_CENTER.value] = longitude + "," + latitude
            loca_config[AFCParams.ELLIPSE_MAJOR_AXIS.value] = major_axis
            loca_config[AFCParams.ELLIPSE_MINOR_AXIS.value] = minor_axis
            loca_config[AFCParams.ELLIPSE_ORIENTATION.value] = orient
        elif geo_area == "LinearPolygon":
            loca_config[AFCParams.LOCATION_GEO_AREA.value] = GeoArea.LinearPolygon.value
            loca_config[AFCParams.LINEARPOLY_BOUNDARY.value] = boundary
        elif geo_area == "RadialPolygon":
            loca_config[AFCParams.LOCATION_GEO_AREA.value] = GeoArea.RadialPolygon.value
            loca_config[AFCParams.RADIALPOLY_CENTER.value] = longitude + "," + latitude
            loca_config[AFCParams.RADIALPOLY_BOUNDARY.value] = "30,150 120,150 90,150"

        loca_config[AFCParams.HEIGHT.value] = height
        loca_config[AFCParams.HEIGHT_TYPE.value] = height_type
        loca_config[AFCParams.VERTICAL_UNCERT.value] = vert_uncert
        loca_config[AFCParams.DEPLOYMENT.value] = deploy

        return loca_config

    @staticmethod
    def freq_channel_conf(afcd_country_code="US", op_class="131 132 133 134 136", channel=None):
        mapping = {'US' : "5925,6425 6525,6875",
                   'CA' : "5925,6875"}
        freq = mapping[afcd_country_code]
        req_config = {}
        # if type is list, casting to string
        if type(freq) is list:
            req_config[AFCParams.FREQ_RANGE.value] = freq[0]
            for i in range(1, len(freq)):
               req_config[AFCParams.FREQ_RANGE.value] += " " 
               req_config[AFCParams.FREQ_RANGE.value] += freq[i] 
        else:
            req_config[AFCParams.FREQ_RANGE.value] = freq
        if op_class:
            req_config[AFCParams.GLOBAL_OPCL.value] = op_class
        if channel:
            req_config[AFCParams.CHANNEL_CFI.value] = channel

        return req_config

    @staticmethod
    def add_bss_conf(
        ssid = "AFC_Wi-Fi",
        security_type="0",
        passphrase="12345678"
    ):
        ap_config = {}
        ap_config[AFCParams.AFC_TEST_SSID.value] = ssid
        ap_config[AFCParams.SECURITY_TYPE.value] = security_type
        if passphrase:
            ap_config[AFCParams.WPA_PASSPHRASE.value] = passphrase
        return ap_config

    @staticmethod
    def misc_conf(version="1.4", request_id="0"):
        ap_config = {}
        ap_config[AFCParams.VERSION_NUMBER.value] = version
        ap_config[AFCParams.REQUEST_ID.value] = request_id        

        return ap_config

    @staticmethod
    def add_server_conf(server_url="https://testserver.wfatestorg.org/afc-simulator-api", ca_cert="afc_ca.pem"):
        ap_config = {}
        ap_config[AFCParams.AFC_SERVER_URL.value] = server_url
        ap_config[AFCParams.CA_CERT.value] = ca_cert

        return ap_config

    @staticmethod
    def combine_configs(*args):
        """Returns the a new combined dictionary of all args.

        Parameters
        ----------
        args
            args
        Returns
        -------
        dict
            Combined configuration
        """
        combined_config = {}
        for config in args:
            for key, value in config.items():
                combined_config[key] = value
        return combined_config

    @staticmethod
    def verify_req_infor(afc_status):
        try:
            return afc_status["valid_request"]
        except Exception as err:
            exception_str = traceback.format_exc()
            InstructionLib.log_error(f'verify_req_infor Exception {exception_str}')
            return False

    @staticmethod
    def get_center_power(afc_resp, freq, channel):
        freq = int(freq)
        channel = int(channel)
        resp = afc_resp["sentResponse"]
        freq_info = resp["availableSpectrumInquiryResponses"][0].get("availableFrequencyInfo")
        chan_info = resp["availableSpectrumInquiryResponses"][0].get("availableChannelInfo")
        power = None
        if chan_info:
            for opcl in chan_info:
                i = 0
                while i < len(opcl["channelCfi"]):
                    if opcl["channelCfi"][i] == channel:
                        power = opcl["maxEirp"][i]
                    i = i + 1
        if freq_info and power is None:
            for freq_range in freq_info:
                if freq_range["frequencyRange"]["lowFrequency"] < freq and freq_range["frequencyRange"]["highFrequency"] > freq:
                    psd = freq_range["maxPsd"]
                    bw = __class__.get_bw_from_cfi(channel) 
                    power = psd + 10 * math.log10(bw)
                    # SP mode max EIRP: 36
                    if power > 36:
                        power = 36
        return power

    @staticmethod
    def get_bw_from_cfi(cfi):
        cfi_list = [7, 23, 39, 55, 71, 87, 135, 151, 167]
        cfi_160m_list = [15, 47, 79, 111, 143, 175, 207]
        if cfi in cfi_160m_list:
            return 160
        for index in cfi_list:
            if cfi == index:
                return 80
            elif cfi == index - 4 or cfi == index + 4:
                return 40
            elif cfi == 123 or cfi == 179:
                return 40

        return 20

    @staticmethod
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

    @staticmethod
    def save_rf_measurement_report(report_json, file_name):

        if not isinstance(report_json, list):
            report_json = [report_json]

        if isinstance(report_json, list):  # Check if report_json is a list
            for index, report in enumerate(report_json):
                if not report:
                    continue
                json_object = json.dumps(report, indent=4)
                if len(report_json) > 1:
                    file_name = f"[{index}]{file_name}.json"
                with open(os.path.join(InstructionLib.get_current_testcase_log_dir(), file_name), "w") as f:
                    f.write(json_object)
        else:
            raise ValueError("Invalid report_json type. Expected dictionary or list of dictionaries.")

