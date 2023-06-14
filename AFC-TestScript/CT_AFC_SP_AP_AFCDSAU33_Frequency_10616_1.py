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

import concurrent.futures
import time
from IndigoTestScripts.Programs.AFC.AFCBaseScript import AFCBaseScript
from IndigoTestScripts.Programs.AFC.afc_lib import AFCLib
from IndigoTestScripts.Programs.AFC.afc_enums import *
from IndigoTestScripts.Programs.AFC.rf_measurement_validation import RfMeasurementValidation
from IndigoTestScripts.Programs.AFC.spectrum_analyzer_lib import SpectrumAnalyzerLib
from IndigoTestScripts.Programs.AFC.measurement_desc import *
from IndigoTestScripts.helpers.instruction_lib import InstructionLib
from commons.shared_enums import *


class CT_AFC_SP_AP_AFCDSAU33_Frequency_10616_1(AFCBaseScript):
    def __init__(self):
        super().__init__(DutType.APUT)
        self.description = (
            "Successful spectrum access update"
        )
        self.power_cycle_done = False

    def setup(self):
        """Setting up all the pre-requisites required for test case execution
        """
        InstructionLib.send_script_status(
            "Step 2: Resetting the AFC DUT to its Initial Pre-test State", 10
        )
        super().setup()

    def execute(self):
        """Method to execute all the instructions as per test plan after setup."""

        if self.auto_rf_tester and not SpectrumAnalyzerLib().spectrum_analyzer_connect():
            InstructionLib.log_error("Please configure the correct Tester IP Address setting")

	    # setup() in AFCBaseScript created afc_config
        InstructionLib.afcd_configure(self.afc_config)

        sp_operation = super().monitor_allchans_sp_operation("rfMeasurementReport_step_2.json")

        InstructionLib.append_measurements(
            "AFC_DUT_SP_OPERATION_1", sp_operation, measure_desc["AFC_DUT_SP_OPERATION"])

        AFCLib.set_afc_response("SAU", test_vector=1, phase=1)

        InstructionLib.send_script_status(
            "Step 3 : Send an Available Spectrum Inquiry Request", 20
        )
        InstructionLib.afcd_operation({AFCParams.SEND_SPECTRUM_REQ.value: SpectrumRequestType.Frequency.value})

        InstructionLib.send_script_status(
            "Step 4 : AFC Test Harness validates mandatory registration information", 30
        )
        manual_mode = InstructionLib.get_setting(SettingsName.MANUAL_DUT_MODE)
        if not manual_mode:
            InstructionLib.wait(10)
        InstructionLib.send_script_status(
            "Step 5 : AFC Test Harness sends an Available Spectrum Inquiry Response", 40
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
        InstructionLib.append_measurements("AFC_DUT_SPECTRUM_INQUIRYREQUEST_VALID_1", req_valid, measure_desc["AFC_DUT_SPECTRUM_INQUIRYREQUEST_VALID"])

        InstructionLib.send_script_status(
            "Step 6 : RF Test Equipment verification", 50
        )

        InstructionLib.wait(60)
        resp = InstructionLib.afcd_get_info({})
        if resp.status != 0:
            InstructionLib.log_info("Getting infor from AFC DUT Failed!")
            InstructionLib.append_measurements("AFC_DUT_CONFORM_SPECTRUM_INQUIRYRESPONSE_1", False, measure_desc["AFC_DUT_CONFORM_SPECTRUM_INQUIRYRESPONSE"])
            return
        else:
            InstructionLib.log_debug("Response: {}".format(resp.tlvs))
            op_channel = int(resp.tlvs.get(AFCResponseTLV.OPER_CHANNEL.value))

        power_valid, adjacent_valid = super().validate_rf_measurement_by_freq(afc_resp["sentResponse"], op_channel, "rfMeasurementReport_step_6.json")
        InstructionLib.append_measurements("AFC_DUT_CONFORM_SPECTRUM_INQUIRYRESPONSE_1", power_valid, self.power_valid_desc)
        InstructionLib.append_measurements("AFC_DUT_CONFORM_ADJACENT_FREQUENCIES_EMISSIONS_LIMITS_1", adjacent_valid, measure_desc["AFC_DUT_CONFORM_ADJACENT_FREQUENCIES_EMISSIONS_LIMITS"])

        InstructionLib.send_script_status(
            "Step 7 : Trigger Power Cycle and Configure the DUT with AFC System URL information", 60
        )

        AFCLib.set_afc_response("SAU", test_vector=1, phase=2, hold_response=True)
        InstructionLib.afcd_operation({AFCParams.POWER_CYCLE.value: "1"})
        if not manual_mode:
            InstructionLib.wait(self.power_cycle_timeout)

        # New AFC configurations
        if self.need_reg_conf:
            if self.geo_area == "LinearPolygon":
                boundary = "-97.73483381300288,30.403118936839025 -97.73637876535906,30.400055989563008 -97.73849234601303,30.40343355438094"
            else:
                boundary = None
            new_reg_conf = super().combine_configs(
                super().dev_desc_conf(),
                super().location_conf(geo_area=self.geo_area, longitude="-97.73618564630566", latitude="30.401878963715333", boundary=boundary),
                super().freq_channel_conf(),
                super().misc_conf()
            )
            self.afc_config = super().combine_configs(
                self.server_conf,
                self.bss_conf,
                new_reg_conf
            )
        # timeout is 15 sec retry is 1, total is 30 sec
        resp = InstructionLib.afcd_configure(self.afc_config)
        if resp.status != 0:
            resp = InstructionLib.afcd_configure(self.afc_config)
            # Retry afcd_configure until DUT is ready???

        InstructionLib.send_script_status(
            "Step 8 : Wait for 60 seconds to monitor the output of the DUT before DUT sends Request", 70
        )
        recv_req = False
        for i in range(0, 12):
            afc_resp = AFCLib.get_afc_status()
            if afc_resp["receivedRequest"] != {}:
               recv_req = True
               break
            InstructionLib.wait(5, custom_msg="Waiting for an available spectrum inquiry request")

        if not recv_req:
            sp_operation = super().monitor_allchans_sp_operation("rfMeasurementReport_step_8.json")
            InstructionLib.append_measurements(
                            "AFC_DUT_SP_OPERATION_NO_REQ", sp_operation, measure_desc["AFC_DUT_SP_OPERATION_NO_REQ"])
            return

        InstructionLib.send_script_status(
            "Step 9 : AFC Test Harness validates mandatory registration information", 80
        )
        req_valid = super().verify_req_infor(afc_resp)
        InstructionLib.append_measurements(
            "AFC_DUT_SPECTRUM_INQUIRYREQUEST_VALID_2", req_valid, measure_desc["AFC_DUT_SPECTRUM_INQUIRYREQUEST_VALID"])

        InstructionLib.send_script_status(
            "Step 10 : AFC Test Harness waits for 60 seconds before sending an Available Spectrum Inquiry Response", 90
        )

        sp_operation = super().monitor_allchans_sp_operation("rfMeasurementReport_step_10.json",
            timeout=60, extra_info="\n\nAvailable Spectrum Inquiry Response will be sent after finishing the monitor and clicking Pass/Fail")
        AFCLib.set_afc_params(hold_response=False)

        InstructionLib.append_measurements(
            "AFC_DUT_SP_OPERATION_2", sp_operation, measure_desc["AFC_DUT_SP_OPERATION"])

        InstructionLib.send_script_status(
            "Step 11 : RF Test Equipment verification", 95
        )
        InstructionLib.wait(60)
        afc_resp = AFCLib.get_afc_status()
        resp = InstructionLib.afcd_get_info({})
        if resp.status != 0:
            InstructionLib.log_info("Getting infor from AFC DUT Failed!")            
            InstructionLib.append_measurements("AFC_DUT_CONFORM_SPECTRUM_INQUIRYRESPONSE_2", False, measure_desc["AFC_DUT_CONFORM_SPECTRUM_INQUIRYRESPONSE"])
            return
        else:
            InstructionLib.log_debug("Response: {}".format(resp.tlvs))
            op_channel = int(resp.tlvs.get(AFCResponseTLV.OPER_CHANNEL.value))

        power_valid, adjacent_valid = super().validate_rf_measurement_by_freq(afc_resp["sentResponse"], op_channel, "rfMeasurementReport_step_11.json")
        InstructionLib.append_measurements("AFC_DUT_CONFORM_SPECTRUM_INQUIRYRESPONSE_2", power_valid, self.power_valid_desc)
        InstructionLib.append_measurements("AFC_DUT_CONFORM_ADJACENT_FREQUENCIES_EMISSIONS_LIMITS_2", adjacent_valid, measure_desc["AFC_DUT_CONFORM_ADJACENT_FREQUENCIES_EMISSIONS_LIMITS"])

    def teardown(self):
        """Method to reset the AFC DUT after test execution."""
        super().teardown()

    def get_testscript_version(self):
        """Method returns the version number of test scripts."""
        return "1.0"
