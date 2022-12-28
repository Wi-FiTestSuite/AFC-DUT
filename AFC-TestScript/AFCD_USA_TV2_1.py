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
from IndigoTestScripts.helpers.instruction_lib import InstructionLib
from commons.shared_enums import *


class AFCD_USA_TV2_1(AFCBaseScript):
    def __init__(self):
        super().__init__(DutType.APUT)
        self.description = (
            "Unsuccessful spectrum access request"
        )

    def setup(self):
        """Setting up all the pre-requisites required for test case execution
        """
        InstructionLib.send_script_status(
            "Step 1: Resetting the AFC DUT to its default configuration", 10
        )
        super().setup()

    def execute(self):
        """Method to execute all the instructions as per test plan after setup."""

        if not SpectrumAnalyzerLib().spectrum_analyzer_connect():
            InstructionLib.log_error("Please configure the correct Tester IP Address setting")
            return

	    # setup() in AFCBaseScript created afc_config
        InstructionLib.afcd_configure(self.afc_config)

        InstructionLib.log_info("RF Test Equipment is monitoring the output of the DUT...")
        report = SpectrumAnalyzerLib().spectrum_analyze_all()
        super().save_rf_measurement_report(report, "rfMeasurementReport_step_1.json")
        lpi_support = InstructionLib.get_setting(SettingsName.AFCD_APPROVED_LPI_OPERATION)
        if report:
            if lpi_support:                
                if not RfMeasurementValidation({} , report).validate_lpi_transmit_power():
                    InstructionLib.append_measurements(
                        "AFC_POWER_CONFORM", False, "DUT conforms to the conditons before the Spectrum Inquiry Response")
                    return
            else:
                InstructionLib.log_error(f'The DUT should not transmit in the band if the DUT supports only SP operation')
                InstructionLib.append_measurements(
                        "AFC_POWER_CONFORM", False, "DUT conforms to the conditons before the Spectrum Inquiry Response")
                return

        AFCLib.set_afc_response("USA", test_vector=2)

        InstructionLib.send_script_status(
            "Step 2 : Send an Available Spectrum Inquiry Request", 20
        )
        # 0: Default, 1: Channel based, 2: Freq based
        req_type = "1"
        InstructionLib.afcd_operation({AFCParams.SEND_SPECTRUM_REQ.value: req_type})

        InstructionLib.send_script_status(
            "Step 3 : AFC Test Harness validates mandatory registration information", 40
        )
        manual_mode = InstructionLib.get_setting(SettingsName.MANUAL_DUT_MODE)
        if not manual_mode:
            InstructionLib.wait(10)

        InstructionLib.send_script_status(
            "Step 4 : AFC Test Harness sends an Available Spectrum Inquiry Response", 60
        )
        # Get response from AFC Server
        afc_resp = AFCLib.get_afc_status()
        if afc_resp["receivedRequest"]:
            InstructionLib.append_measurements("AFC_SPEC_REQ", True, "AFC DUT sends an Available Spectrum Inquiry Request")
        else:
            InstructionLib.append_measurements("AFC_SPEC_REQ", False, "AFC DUT sends an Available Spectrum Inquiry Request")
            InstructionLib.log_info("AFC DUT doesn't send Spectrum Inquiry Request, Stopping test execution.")
            return

        req_valid = super().verify_req_infor(afc_resp["receivedRequest"])
        InstructionLib.append_measurements("AFC_REG_INFO", req_valid, "Valid mandatory registration information")

        InstructionLib.send_script_status(
            "Step 5 : RF Test Equipment verification", 80
        )

        InstructionLib.log_info("RF Test Equipment is monitoring the output of the DUT...")
        report = SpectrumAnalyzerLib().spectrum_analyze_all()
        super().save_rf_measurement_report(report, "rfMeasurementReport_step_5.json")        
        if report:
            if lpi_support:                
                if not RfMeasurementValidation({} , report).validate_lpi_transmit_power():
                    InstructionLib.append_measurements(
                        "AFC_POWER_CONFORM", False, "DUT conforms to the conditons before the Spectrum Inquiry Response")
                    return
            else:
                InstructionLib.log_error(f'The DUT should not transmit in the band if the DUT supports only SP operation')
                InstructionLib.append_measurements(
                        "AFC_POWER_CONFORM", False, "DUT conforms to the conditons before the Spectrum Inquiry Response")
                return

        InstructionLib.append_measurements("AFC_POWER_CONFORM", True, "DUT conforms to the conditons in the Spectrum Inquiry Response")

    def teardown(self):
        """Method to reset the AFC DUT after test execution."""
        super().teardown()

    def get_testscript_version(self):
        """Method returns the version number of test scripts."""
        return "1.0"
