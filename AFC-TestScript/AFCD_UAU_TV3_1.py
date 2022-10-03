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
from IndigoTestScripts.helpers.instruction_lib import InstructionLib
from commons.shared_enums import *


class AFCD_UAU_TV3_1(AFCBaseScript):
    def __init__(self):
        super().__init__(DutType.APUT)
        self.description = (
            "Unsuccessful spectrum access update"
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

	# setup() in AFCBaseScript created afc_config
        InstructionLib.afcd_configure(self.afc_config)

        lpi_support = InstructionLib.get_setting(SettingsName.AFCD_APPROVED_LPI_OPERATION)
        if lpi_support:
            message = "Confirm the DUT does not transmit above LPI limits"
        else:
            message = "Confirm the DUT does not transmit in the band"
        title = type(self).__name__
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
            InstructionLib.append_measurements("AFC_POWER_CONFORM", False, "DUT conforms to the conditons before the Spectrum Inquiry Response")
            return
        AFCLib.set_afc_response("UAU", phase=1)

        InstructionLib.send_script_status(
            "Step 2 : Send an Available Spectrum Inquiry Request", 20
        )
        # 0: Default, 1: Channel based, 2: Freq based
        req_type = "0"
        InstructionLib.afcd_operation({AFCParams.SEND_SPECTRUM_REQ.value: req_type})

        InstructionLib.send_script_status(
            "Step 3 : AFC Test Harness validates mandatory registration information", 30
        )
        InstructionLib.wait(5)
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

        InstructionLib.wait(60)
        resp = InstructionLib.afcd_get_info({})
        if resp.status != 0:
            InstructionLib.log_info("Getting infor from AFC DUT Failed!")
        else:
            InstructionLib.log_debug("Response: {}".format(resp.tlvs))
        #power = super().get_center_power(afc_resp, resp.tlvs.get(AFCResponseTLV.OPER_FREQ.value), resp.tlvs.get(AFCResponseTLV.OPER_CHANNEL.value))

        InstructionLib.send_script_status(
            "Step 5 : RF Test Equipment verification", 50
        )
        if lpi_support:
            message = "DUT transmit power in the band is < CEILING[LPI limits, SP limits in Spectrum Reponse] and does not exceed limits in adjacent frequencies"
        else:
            message = "DUT conforms to the conditions in Spectrum Response and does not exceed emissoins limits in adjacent frequencies"
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
        #InstructionLib.afcd_upload_result()
        # Verify result based on power from afc_resp
        #Suppression: 20dB PSD at one Mhz outside channel edge, 28dB PSD at 1 BW, 40dB PSD at 1.5 BW
        InstructionLib.append_measurements("AFC_POWER_CONFORM", power_valid, "DUT conforms to the conditons in the Spectrum Inquiry Response")

        InstructionLib.send_script_status(
            "Step 6 : Trigger Power Cycle and Configure the DUT with AFC System URL information", 60
        )
        InstructionLib.afcd_operation({AFCParams.POWER_CYCLE.value: "1"})

        AFCLib.set_afc_response("UAU", phase=2)
        InstructionLib.wait(30)
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
        if lpi_support:
            message = "Confirm the DUT does not transmit above LPI limits for 60 seconds"
        else:
            message = "Confirm the DUT does not transmit in the band for 60 seconds"
        InstructionLib.post_popup_message(
            message,
            [UiPopupButtons.POP_UP_BUTTON_YES, UiPopupButtons.POP_UP_BUTTON_NO],
            title,
            UiPopupButtons.POP_UP_BUTTON_NO,
        )
        recv_req = False
        for i in range(0, 12):
            InstructionLib.wait(5)
            afc_resp = AFCLib.get_afc_status()
            if afc_resp["receivedRequest"] != {}:
               recv_req = True
               break
        if not recv_req:
            user_button, user_input = InstructionLib.get_popup_response()
            if user_button == UiPopupButtons.POP_UP_BUTTON_YES:
                power_valid = True
            elif user_button == UiPopupButtons.POP_UP_BUTTON_NO:
                power_valid = False
            InstructionLib.append_measurements("AFC_POWER_CONFORM_NO_REQ", power_valid, "DUT conforms to the conditons in no Spectrum Inquiry Request case")
            return

        InstructionLib.send_script_status(
            "Step 8 : AFC Test Harness valifates mandatory registration information", 80
        )
        req_valid = super().verify_req_infor(afc_resp["receivedRequest"])
        InstructionLib.append_measurements("AFC_REG_INFO_1", req_valid, "Valid mandatory registration information")

        InstructionLib.send_script_status(
            "Step 9 : AFC Test Harness sends an Available Spectrum Inquiry Response indicating that no frequency ranges and/or channels are available", 90
        )
        InstructionLib.send_script_status(
            "Step 10 : RF Test Equipment verification", 95
        )
        user_button, user_input = InstructionLib.get_popup_response()
        if user_button == UiPopupButtons.POP_UP_BUTTON_YES:
            power_valid = True
        elif user_button == UiPopupButtons.POP_UP_BUTTON_NO:
            power_valid = False
        InstructionLib.append_measurements("AFC_POWER_CONFORM_1", power_valid, "DUT conforms to the conditons in no available frequency ragnes and/or channels")

    def teardown(self):
        """Method to reset the AFC DUT after test execution."""
        super().teardown()

    def get_testscript_version(self):
        """Method returns the version number of test scripts."""
        return "1.0"
