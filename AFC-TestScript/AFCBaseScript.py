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

from IndigoTestScripts.TestScript import TestScript
from IndigoTestScripts.helpers.instruction_lib import InstructionLib
from commons.shared_enums import (
    OperationalBand, DutType, SettingsName, UiPopupButtons
)
from IndigoTestScripts.Programs.AFC.afc_enums import AFCParams, GeoArea, Deployment
from IndigoTestScripts.Programs.AFC.afc_lib import AFCLib


class AFCBaseScript(TestScript):
    def __init__(self, dut_type):
        self.operational_band = OperationalBand._6GHz.value
        InstructionLib.set_dut_type(DutType.APUT)

    def setup(self):
        # Reset AFC simulator Test Vector
        AFCLib.reset_afc()
        InstructionLib.afcd_operation({AFCParams.DEVICE_RESET.value: 1})
        InstructionLib.set_band(self.operational_band)
        self.test_ssid = InstructionLib.get_setting(
            SettingsName.TEST_SSID
        ) + InstructionLib.get_setting(SettingsName.INSTALLER_EPOCH_TIME)
        self.band = InstructionLib.get_hw_mode(self.operational_band)

        self.server_conf = AFCBaseScript.add_server_conf()
        need_bss_conf = InstructionLib.get_setting(SettingsName.AFCD_NEED_BSS_CONF)
        if need_bss_conf:
            self.bss_conf = AFCBaseScript.add_bss_conf()
        else:
            self.bss_conf = {}
        self.need_reg_conf = InstructionLib.get_setting(SettingsName.AFCD_NEED_REG_INFO)
        if self.need_reg_conf:
            self.geo_area = InstructionLib.get_setting(SettingsName.AFCD_GEOGRAPHIC_TYPE)
            reg_conf = AFCBaseScript.combine_configs(
                AFCBaseScript.dev_desc_conf(),
                AFCBaseScript.location_conf(geo_area=self.geo_area),
                AFCBaseScript.freq_channel_conf(),
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

    def execute(self):
        pass

    def teardown(self):
        AFCLib.reset_afc()

    def get_testscript_version(self):
        pass

    def get_description(self):
        if not hasattr(self, "description"):
            self.description = ""
        return self.description

    def check_RF_test_result_manually(self, lpi_message, sp_message):
        lpi_support = InstructionLib.get_setting(SettingsName.AFCD_APPROVED_LPI_OPERATION)        
        if lpi_support:
            message = lpi_message
        else:
            message = sp_message
        title = self.__class__.__name__ + " - RF Test Equipment monitors the output of the DUT"
        InstructionLib.post_popup_message(
            message,
            [UiPopupButtons.POP_UP_BUTTON_YES, UiPopupButtons.POP_UP_BUTTON_NO],
            title,
            UiPopupButtons.POP_UP_BUTTON_NO,
        )
        user_button, user_input = InstructionLib.get_popup_response()
        if user_button == UiPopupButtons.POP_UP_BUTTON_YES:
            power_valid = True
        elif user_button == UiPopupButtons.POP_UP_BUTTON_NO:
            power_valid = False
        return power_valid

    @staticmethod
    def dev_desc_conf(serial_number="SN000", cert_nra="FCC", 
            cert_id="CID000", rule_id="US_47_CFR_PART_15_SUBPART_E"):
        dev_config = {}
        dev_config[AFCParams.SERIAL_NUMBER.value] = serial_number
        dev_config[AFCParams.NRA.value] = cert_nra
        dev_config[AFCParams.CERT_ID.value] = cert_id
        dev_config[AFCParams.RULE_SET_ID.value] = rule_id

        return dev_config

    @staticmethod
    def location_conf(geo_area="Ellipse", longitude="37.38193354300452",
            latitude="-121.98586998164663", major_axis=150, minor_axis=150, orient=0, boundary=None,
            height=15, height_type="AGL", vert_uncert=2, deploy=Deployment.Unknown.value):
        loca_config = {}
        if geo_area == "Ellipse":
            loca_config[AFCParams.LOCATION_GEO_AREA.value] = GeoArea.Ellipse.value
            loca_config[AFCParams.ELLIPSE_CENTER.value] = longitude + "," + latitude
            loca_config[AFCParams.ELLIPSE_MAJOR_AXIS.value] = major_axis
            loca_config[AFCParams.ELLIPSE_MINOR_AXIS.value] = minor_axis
            loca_config[AFCParams.ELLIPSE_ORIENTATION.value] = orient
        elif geo_area == "LinearPolygon":
            loca_config[AFCParams.LOCATION_GEO_AREA.value] = GeoArea.LinearPolygon.value
            if boundary is None:
                boundary = "37.382479218209305,-121.9875329371091 37.38271792164739,-121.98371347155712 37.37992163368795,-121.98558028898755"
            loca_config[AFCParams.LINEARPOLY_BOUNDARY.value] = boundary
        elif geo_area == "RadialPolygon":
            loca_config[AFCParams.LOCATION_GEO_AREA.value] = GeoArea.RadialPolygon.value
            loca_config[AFCParams.RADIALPOLY_CENTER.value] = longitude + "," + latitude
            if boundary is None:
                boundary = "30,150 120,150 90,150"
            loca_config[AFCParams.RADIALPOLY_BOUNDARY.value] = boundary

        loca_config[AFCParams.HEIGHT.value] = height
        loca_config[AFCParams.HEIGHT_TYPE.value] = height_type
        loca_config[AFCParams.VERTICAL_UNCERT.value] = vert_uncert
        loca_config[AFCParams.DEPLOYMENT.value] = deploy

        return loca_config

    @staticmethod
    def freq_channel_conf(freq="5925,6425 6525,6875", op_class="131 132 133 134 136", channel=None):
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
    def misc_conf(version="1.3", request_id="0"):
        ap_config = {}
        ap_config[AFCParams.VERSION_NUMBER.value] = version
        ap_config[AFCParams.REQUEST_ID.value] = request_id

        return ap_config

    @staticmethod
    def add_server_conf(server_url="https://testserver.wfatestorg.org/afc-simulator-api"):
        ap_config = {}
        ap_config[AFCParams.AFC_SERVER_URL.value] = server_url

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
    def verify_req_infor(afc_req):
        req = afc_req["availableSpectrumInquiryRequests"][0]
        dev_desc = req.get("deviceDescriptor")
        if not dev_desc:
            return False
        if dev_desc.get("serialNumber") and dev_desc.get("rulesetIds"):
            cert_id_list = dev_desc.get("certificationId")
            if not cert_id_list:
                return False
            if type(cert_id_list) is not list:
                return False
            cert_id = cert_id_list[0]
            if cert_id.get("nra") and cert_id.get("id"):
                return True
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
            else:
                return 20

    @staticmethod
    def save_rf_measurement_report(report_json, file_name):

        json_object = json.dumps(report_json, indent=4)

        with open(os.path.join(InstructionLib.get_current_testcase_log_dir(), file_name), "w") as f:
            f.write(json_object)
