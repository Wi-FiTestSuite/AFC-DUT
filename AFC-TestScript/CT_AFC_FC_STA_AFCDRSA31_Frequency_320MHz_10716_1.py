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

from IndigoTestScripts.Programs.AFC.AFCBaseScript import AFCBaseScript
from IndigoTestScripts.Programs.AFC.afc_lib import AFCLib
from IndigoTestScripts.Programs.AFC.afc_enums import *
from IndigoTestScripts.Programs.AFC.rf_measurement_validation import RfMeasurementValidation
from IndigoTestScripts.Programs.AFC.spectrum_analyzer_lib import SpectrumAnalyzerLib
from IndigoTestScripts.Programs.AFC.measurement_desc import *
from IndigoTestScripts.helpers.instruction_lib import InstructionLib
from commons.shared_enums import *


class CT_AFC_FC_STA_AFCDRSA31_Frequency_320MHz_10716_1(AFCBaseScript):
    def __init__(self):
        super().__init__(DutType.STAUT)
        self.description = (
            "Successful registration and spectrum access request"
        )

    def setup(self):
        """Setting up all the pre-requisites required for test case execution
        """
        InstructionLib.send_script_status(
            "Step 13: Resetting the AFC DUT to its Initial Pre-test State", 10
        )
        super().setup(is_320mhz = True)
        self.afc_config[AFCParams.BANDWIDTH.value] = TestFrameBandwidth.BW320.value

    def execute(self):
        """Method to execute all the instructions as per test plan after setup."""

        if self.auto_rf_tester and not SpectrumAnalyzerLib().spectrum_analyzer_connect():
            InstructionLib.log_error("Please configure the correct Tester IP Address setting")

        InstructionLib.send_script_status(
            "Step 14 : Configure the AFC DUT", 15
        )
        # setup() in AFCBaseScript created afc_config
        InstructionLib.afcd_configure(self.afc_config)

        # sp_operation = super().monitor_allchans_sp_operation("rfMeasurementReport_step_9.json")
        # InstructionLib.append_measurements(
        #     "AFC_DUT_SP_OPERATION", sp_operation, measure_desc["AFC_DUT_SP_OPERATION"])

        AFCLib.set_afc_response("RSA", test_vector=1, random=True, only_random_power=True, channel_width=320)

        InstructionLib.send_script_status(
            "Step 15 : Send an Available Spectrum Inquiry Request", 20
        )
        InstructionLib.afcd_operation({AFCParams.SEND_SPECTRUM_REQ.value: SpectrumRequestType.Frequency.value})

        InstructionLib.send_script_status(
            "Step 16 : AFC Test Harness validates mandatory registration information", 25
        )
        manual_mode = InstructionLib.get_setting(SettingsName.MANUAL_DUT_MODE)
        if not manual_mode:
            InstructionLib.wait(10)
        InstructionLib.send_script_status(
            "Step 17 : AFC Test Harness sends an Available Spectrum Inquiry Response", 30
        )
        # Get response from AFC Server
        afc_resp = AFCLib.get_afc_status()
        if afc_resp["receivedRequest"]:
            recv_req = True            
        else:
            recv_req = False
        InstructionLib.append_measurements("AFC_DUT_SEND_SPECTRUM_INQUIRYREQUEST_1", recv_req, measure_desc["AFC_DUT_SEND_SPECTRUM_INQUIRYREQUEST"])
        if not recv_req:
            InstructionLib.log_info("AFC DUT doesn't send Spectrum Inquiry Request, Stopping test execution.")
            return

        req_valid = super().verify_req_infor(afc_resp)
        InstructionLib.append_measurements("AFC_DUT_SPECTRUM_INQUIRYREQUEST_VALID_1", req_valid, measure_desc["AFC_DUT_SPECTRUM_INQUIRYREQUEST_VALID"])
        if not req_valid:
            InstructionLib.log_info("Invalid Spectrum Inquiry Request from AFC DUT, Stopping test execution.")
            return

        fc_req_method = InstructionLib.get_setting(SettingsName.AFCD_FC_SEND_REQ_METHOD)
        if fc_req_method == FixedClientSendRequestMethod.OutOfBand.value:
            InstructionLib.send_script_status(
                "Step 18 : Initiate connection procedure between AFC DUT and SP Access Point", 40
            )
            InstructionLib.afcd_operation({AFCParams.CONNECT_SP_AP.value: "1"})

        InstructionLib.send_script_status(
            "Step 19 : RF Test Equipment verification", 50
        )
        InstructionLib.wait(60)

        InstructionLib.afcd_operation({AFCParams.SEND_TEST_FRAME.value: TestFrameBandwidth.BW320.value})

        resp = InstructionLib.afcd_get_info({AFCParams.BANDWIDTH.value: TestFrameBandwidth.BW320.value})
        if resp.status != 0:
            InstructionLib.log_info("Getting infor from AFC DUT Failed!")
            InstructionLib.append_measurements("AFC_DUT_CONFORM_SPECTRUM_INQUIRYRESPONSE_1", False, measure_desc["AFC_DUT_CONFORM_SPECTRUM_INQUIRYRESPONSE"])
            return
        else:
            InstructionLib.log_debug("Response: {}".format(resp.tlvs))
            if not AFCResponseTLV.CENTER_FREQ_INDEX.value in resp.tlvs:
                InstructionLib.log_info("Missing Center Frequency Index TLV in response, Stopping test execution.")
                return
            op_channel = int(resp.tlvs.get(AFCResponseTLV.CENTER_FREQ_INDEX.value))

        power_valid, adjacent_valid = super().validate_rf_measurement_by_freq(afc_resp["sentResponse"], op_channel, "rfMeasurementReport_step_19.json", op_bandwidth=320, is_cfi=True)
        InstructionLib.append_measurements("AFC_DUT_CONFORM_SPECTRUM_INQUIRYRESPONSE_1", power_valid, self.power_valid_desc)
        InstructionLib.append_measurements("AFC_DUT_CONFORM_ADJACENT_FREQUENCIES_EMISSIONS_LIMITS_1", adjacent_valid, measure_desc["AFC_DUT_CONFORM_ADJACENT_FREQUENCIES_EMISSIONS_LIMITS"])

        ###################  phase 2  #####################
        AFCLib.set_afc_response("RSA", test_vector=1, random=True, only_random_power=True, channel_width=320)
        InstructionLib.send_script_status(
            "Step 20 : Trigger the AFC DUT to send to the AFC DUT Test Harness an Available Spectrum Inquiry Request", 55
        )
        InstructionLib.afcd_operation({AFCParams.SEND_SPECTRUM_REQ.value: SpectrumRequestType.Frequency.value})

        InstructionLib.send_script_status(
            "Step 21 : Send an Available Spectrum Inquiry Request", 60
        )

        InstructionLib.send_script_status(
            "Step 22 : AFC Test Harness validates mandatory registration information", 65
        )
        manual_mode = InstructionLib.get_setting(SettingsName.MANUAL_DUT_MODE)
        if not manual_mode:
            InstructionLib.wait(10)
        InstructionLib.send_script_status(
            "Step 23 : AFC Test Harness sends an Available Spectrum Inquiry Response", 70
        )
        # Get response from AFC Server
        afc_resp = AFCLib.get_afc_status()
        if afc_resp["receivedRequest"]:
            recv_req = True            
        else:
            recv_req = False
        InstructionLib.append_measurements("AFC_DUT_SEND_SPECTRUM_INQUIRYREQUEST_2", recv_req, measure_desc["AFC_DUT_SEND_SPECTRUM_INQUIRYREQUEST"])
        if not recv_req:
            InstructionLib.log_info("AFC DUT doesn't send Spectrum Inquiry Request, Stopping test execution.")
            return

        req_valid = super().verify_req_infor(afc_resp)
        InstructionLib.append_measurements("AFC_DUT_SPECTRUM_INQUIRYREQUEST_VALID_2", req_valid, measure_desc["AFC_DUT_SPECTRUM_INQUIRYREQUEST_VALID"])
        if not req_valid:
            InstructionLib.log_info("Invalid Spectrum Inquiry Request from AFC DUT, Stopping test execution.")
            return

        if fc_req_method == FixedClientSendRequestMethod.OutOfBand.value:
            InstructionLib.send_script_status(
                "Step 24 : Initiate connection procedure between AFC DUT and SP Access Point", 80
            )
            InstructionLib.afcd_operation({AFCParams.CONNECT_SP_AP.value: "1"})

        InstructionLib.send_script_status(
            "Step 25 : RF Test Equipment verification", 90
        )
        InstructionLib.wait(self.delay_apply_follow_on_response)

        InstructionLib.afcd_operation({AFCParams.SEND_TEST_FRAME.value: TestFrameBandwidth.BW320.value})

        resp = InstructionLib.afcd_get_info({AFCParams.BANDWIDTH.value: TestFrameBandwidth.BW320.value})
        if resp.status != 0:
            InstructionLib.log_info("Getting infor from AFC DUT Failed!")
            InstructionLib.append_measurements("AFC_DUT_CONFORM_SPECTRUM_INQUIRYRESPONSE_2", False, measure_desc["AFC_DUT_CONFORM_SPECTRUM_INQUIRYRESPONSE"])
            return
        else:
            InstructionLib.log_debug("Response: {}".format(resp.tlvs))
            if not AFCResponseTLV.CENTER_FREQ_INDEX.value in resp.tlvs:
                InstructionLib.log_info("Missing Center Frequency Index TLV in response, Stopping test execution.")
                return
            op_channel = int(resp.tlvs.get(AFCResponseTLV.CENTER_FREQ_INDEX.value))

        power_valid, adjacent_valid = super().validate_rf_measurement_by_freq(afc_resp["sentResponse"], op_channel, "rfMeasurementReport_step_25.json", op_bandwidth=320, is_cfi=True)
        InstructionLib.append_measurements("AFC_DUT_CONFORM_SPECTRUM_INQUIRYRESPONSE_2", power_valid, self.power_valid_desc)
        InstructionLib.append_measurements("AFC_DUT_CONFORM_ADJACENT_FREQUENCIES_EMISSIONS_LIMITS_2", adjacent_valid, measure_desc["AFC_DUT_CONFORM_ADJACENT_FREQUENCIES_EMISSIONS_LIMITS"])

    def teardown(self):
        """Method to reset the AFC DUT after test execution."""
        super().teardown()

    def get_testscript_version(self):
        """Method returns the version number of test scripts."""
        return "1.0"
