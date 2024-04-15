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


class CT_AFC_FC_STA_AFCDUSA32_FrequencyChannel_10658_1(AFCBaseScript):
    def __init__(self):
        super().__init__(DutType.STAUT)
        self.description = (
            "Unsuccessful spectrum access request"
        )

    def setup(self):
        """Setting up all the pre-requisites required for test case execution
        """
        InstructionLib.send_script_status(
            "Step 8: Resetting the AFC DUT to its Initial Pre-test State", 10
        )
        super().setup()

    def execute(self):
        """Method to execute all the instructions as per test plan after setup."""

        tester_error = False
        if self.auto_rf_tester and not SpectrumAnalyzerLib().spectrum_analyzer_connect():
            InstructionLib.log_error("Please configure the correct Tester IP Address setting")
            tester_error = True

        InstructionLib.send_script_status(
            "Step 9 : Configure the AFC DUT", 15
        )
	    # setup() in AFCBaseScript created afc_config
        InstructionLib.afcd_configure(self.afc_config)

        # sp_operation = super().monitor_allchans_sp_operation("rfMeasurementReport_step_9.json")
        # InstructionLib.append_measurements(
        #     "AFC_DUT_SP_OPERATION", sp_operation, measure_desc["AFC_DUT_SP_OPERATION"])

        AFCLib.set_afc_response("USA", test_vector=3)

        InstructionLib.send_script_status(
            "Step 10 : Send an Available Spectrum Inquiry Request", 20
        )
        InstructionLib.afcd_operation({AFCParams.SEND_SPECTRUM_REQ.value: SpectrumRequestType.Default.value})

        InstructionLib.send_script_status(
            "Step 11 : AFC Test Harness validates mandatory registration information", 40
        )
        manual_mode = InstructionLib.get_setting(SettingsName.MANUAL_DUT_MODE)
        if not manual_mode:
            InstructionLib.wait(10)

        InstructionLib.send_script_status(
            "Step 12 : AFC Test Harness sends an Available Spectrum Inquiry Response", 60
        )
        # Get response from AFC Server
        afc_resp = AFCLib.get_afc_status()
        if afc_resp["receivedRequest"]:
            InstructionLib.append_measurements("AFC_DUT_SEND_SPECTRUM_INQUIRYREQUEST", True, measure_desc["AFC_DUT_SEND_SPECTRUM_INQUIRYREQUEST"])
        else:
            InstructionLib.append_measurements("AFC_DUT_SEND_SPECTRUM_INQUIRYREQUEST", False, measure_desc["AFC_DUT_SEND_SPECTRUM_INQUIRYREQUEST"])
            InstructionLib.log_info("AFC DUT doesn't send Spectrum Inquiry Request, Stopping test execution.")
            return

        req_valid = super().verify_req_infor(afc_resp)
        InstructionLib.append_measurements("AFC_DUT_SPECTRUM_INQUIRYREQUEST_VALID", req_valid, measure_desc["AFC_DUT_SPECTRUM_INQUIRYREQUEST_VALID"])
        if not req_valid:
            InstructionLib.log_info("Invalid Spectrum Inquiry Request from AFC DUT, Stopping test execution.")
            return

        fc_req_method = InstructionLib.get_setting(SettingsName.AFCD_FC_SEND_REQ_METHOD)
        if fc_req_method == FixedClientSendRequestMethod.OutOfBand.value:
            InstructionLib.send_script_status(
                "Step 13 : Initiate connection procedure between AFC DUT and SP Access Point", 70
            )
            InstructionLib.afcd_operation({AFCParams.CONNECT_SP_AP.value: "1"})

        InstructionLib.send_script_status(
            "Step 14 : RF Test Equipment verification", 80
        )
        InstructionLib.wait(60)

        power_valid = super().validate_fc_transmit_power("rfMeasurementReport_step_14.json")
        InstructionLib.append_measurements("AFC_DUT_CONFORM_SPECTRUM_INQUIRYRESPONSE", (not tester_error) and power_valid, measure_desc["AFC_DUT_CONFORM_SPECTRUM_INQUIRYRESPONSE"])

    def teardown(self):
        """Method to reset the AFC DUT after test execution."""
        super().teardown()

    def get_testscript_version(self):
        """Method returns the version number of test scripts."""
        return "1.0"
