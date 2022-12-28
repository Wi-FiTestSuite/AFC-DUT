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
from IndigoTestScripts.Programs.AFC.AFCBaseScript import AFCBaseScript
from IndigoTestScripts.Programs.AFC.afc_lib import AFCLib
from IndigoTestScripts.Programs.AFC.afc_enums import *
from IndigoTestScripts.Programs.AFC.rf_measurement_validation import RfMeasurementValidation
from IndigoTestScripts.Programs.AFC.spectrum_analyzer_lib import SpectrumAnalyzerLib
from IndigoTestScripts.helpers.instruction_lib import InstructionLib
from commons.shared_enums import *


class AFCD_SAU_TV1_1(AFCBaseScript):
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

        AFCLib.set_afc_response("SAU", test_vector=1, phase=1)

        InstructionLib.send_script_status(
            "Step 2 : Send an Available Spectrum Inquiry Request", 20
        )
        # 0: Default, 1: Channel based, 2: Freq based
        req_type = "2"
        InstructionLib.afcd_operation({AFCParams.SEND_SPECTRUM_REQ.value: req_type})

        InstructionLib.send_script_status(
            "Step 3 : AFC Test Harness validates mandatory registration information", 30
        )
        manual_mode = InstructionLib.get_setting(SettingsName.MANUAL_DUT_MODE)
        if not manual_mode:
            InstructionLib.wait(10)
        InstructionLib.send_script_status(
            "Step 4 : AFC Test Harness sends an Available Spectrum Inquiry Response", 40
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
            "Step 5 : RF Test Equipment verification", 50
        )

        InstructionLib.wait(60)
        resp = InstructionLib.afcd_get_info({})
        if resp.status != 0:
            InstructionLib.log_info("Getting infor from AFC DUT Failed!")
            InstructionLib.append_measurements("AFC_POWER_CONFORM", False, "DUT conforms to the conditons in the Spectrum Inquiry Response")
            return
        else:
            InstructionLib.log_debug("Response: {}".format(resp.tlvs))
            op_channel = int(resp.tlvs.get(AFCResponseTLV.OPER_CHANNEL.value))

        InstructionLib.log_info("RF Test Equipment is monitoring the output of the DUT...")
        report = SpectrumAnalyzerLib().spectrum_analyze(op_channel, super().get_bw_from_cfi(op_channel))
        super().save_rf_measurement_report(report, "rfMeasurementReport_step_5.json")
        power_valid = RfMeasurementValidation(afc_resp["sentResponse"] , report).validate_rf_measurement_by_freq()
        InstructionLib.append_measurements("AFC_POWER_CONFORM", power_valid, "DUT conforms to the conditons in the Spectrum Inquiry Response")

        InstructionLib.send_script_status(
            "Step 6 : Trigger Power Cycle and Configure the DUT with AFC System URL information", 60
        )
        AFCLib.set_afc_response("SAU", test_vector=1, phase=2, resp_wait_time=60)

        report_9 = None
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.monitor_dut_output)

            InstructionLib.afcd_operation({AFCParams.POWER_CYCLE.value: "1"})
            if not manual_mode:
                InstructionLib.wait(self.power_cycle_timeout)

            self.power_cycle_done = True
            report_9 = future.result()

        # New AFC configurations
        if self.need_reg_conf:
            if self.geo_area == "LinearPolygon":
                boundary = "30.403118936839025,-97.73483381300288 30.400055989563008,-97.73637876535906 30.40343355438094,-97.73849234601303"
            else:
                boundary = None
            new_reg_conf = super().combine_configs(
                super().dev_desc_conf(),
                super().location_conf(geo_area=self.geo_area, longitude="30.401878963715333", latitude="-97.73618564630566", boundary=boundary),
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
            "Step 7 : Wait for 60 seconds to monitor the output of the DUT before DUT sends Request", 70
        )
        recv_req = False
        for i in range(0, 12):
            afc_resp = AFCLib.get_afc_status()
            if afc_resp["receivedRequest"] != {} and afc_resp["sentResponse"] != {}:
               recv_req = True
               break
            InstructionLib.wait(5)

        if not recv_req:
            InstructionLib.log_info("RF Test Equipment is monitoring the output of the DUT...")
            report = SpectrumAnalyzerLib().spectrum_analyze_all()
            super().save_rf_measurement_report(report, "rfMeasurementReport_step_7.json")
            if report:
                if lpi_support:                
                    if not RfMeasurementValidation({} , report).validate_lpi_transmit_power():
                        InstructionLib.append_measurements(
                            "AFC_POWER_CONFORM_NO_REQ", False, "DUT conforms to the conditons in no Spectrum Inquiry Request case")
                        return
                else:
                    InstructionLib.log_error(f'The DUT should not transmit in the band if the DUT supports only SP operation')
                    InstructionLib.append_measurements(
                            "AFC_POWER_CONFORM_NO_REQ", False, "DUT conforms to the conditons in no Spectrum Inquiry Request case")
                    return

            InstructionLib.append_measurements(
                            "AFC_POWER_CONFORM_NO_REQ", True, "DUT conforms to the conditons in no Spectrum Inquiry Request case")
            return

        InstructionLib.send_script_status(
            "Step 8 : AFC Test Harness validates mandatory registration information", 80
        )
        req_valid = super().verify_req_infor(afc_resp["receivedRequest"])
        InstructionLib.append_measurements("AFC_REG_INFO_1", req_valid, "Valid mandatory registration information")

        InstructionLib.send_script_status(
            "Step 9 : AFC Test Harness waits for 60 seconds before sending an Available Spectrum Inquiry Response", 90
        )

        if report_9 is None:
            InstructionLib.log_info("RF Test Equipment is monitoring the output of the DUT...")
            report_9 = SpectrumAnalyzerLib().spectrum_analyze_all(timeout=50)
        super().save_rf_measurement_report(report_9, "rfMeasurementReport_step_9.json")
        if report_9:
            if lpi_support:                
                if not RfMeasurementValidation({} , report_9).validate_lpi_transmit_power():
                    InstructionLib.append_measurements(
                        "AFC_POWER_CONFORM_1", False, "DUT conforms to the conditons before AFC Test Harness sends Spectrum Response")                    
            else:
                InstructionLib.log_error(f'The DUT should not transmit in the band if the DUT supports only SP operation')
                InstructionLib.append_measurements(
                    "AFC_POWER_CONFORM_1", False, "DUT conforms to the conditons before AFC Test Harness sends Spectrum Response")
        else:
            InstructionLib.append_measurements(
                "AFC_POWER_CONFORM_1", True, "DUT conforms to the conditons before AFC Test Harness sends Spectrum Response")

        InstructionLib.send_script_status(
            "Step 10 : RF Test Equipment verification", 95
        )
        InstructionLib.wait(60)
        afc_resp = AFCLib.get_afc_status()
        resp = InstructionLib.afcd_get_info({})
        if resp.status != 0:
            InstructionLib.log_info("Getting infor from AFC DUT Failed!")
            InstructionLib.append_measurements("AFC_POWER_CONFORM_2", False, "DUT conforms to the conditons in the Spectrum Inquiry Response")
            return
        else:
            InstructionLib.log_debug("Response: {}".format(resp.tlvs))
            op_channel = int(resp.tlvs.get(AFCResponseTLV.OPER_CHANNEL.value))

        InstructionLib.log_info("RF Test Equipment is monitoring the output of the DUT...")
        report = SpectrumAnalyzerLib().spectrum_analyze(op_channel, super().get_bw_from_cfi(op_channel))
        super().save_rf_measurement_report(report, "rfMeasurementReport_step_10.json")
        power_valid = RfMeasurementValidation(afc_resp["sentResponse"] , report).validate_rf_measurement_by_freq()
        InstructionLib.append_measurements("AFC_POWER_CONFORM_2", power_valid, "DUT conforms to the conditons in the Spectrum Inquiry Response")

    def monitor_dut_output(self):
        report = {}
        recv_req = False
        while not self.power_cycle_done:
            afc_resp = AFCLib.get_afc_status()
            if afc_resp["receivedRequest"] != {}:
                recv_req = True
                break
            InstructionLib.wait(5)

        if recv_req:
            InstructionLib.log_info("RF Test Equipment is monitoring the output of the DUT...")
            report = SpectrumAnalyzerLib().spectrum_analyze_all(timeout=55)
        return report

    def teardown(self):
        """Method to reset the AFC DUT after test execution."""
        super().teardown()

    def get_testscript_version(self):
        """Method returns the version number of test scripts."""
        return "1.0"
