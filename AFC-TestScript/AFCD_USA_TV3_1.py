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


class AFCD_USA_TV3_1(AFCBaseScript):
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

	# setup() in AFCBaseScript created afc_config
        InstructionLib.afcd_configure(self.afc_config)

        lpi_support = InstructionLib.get_setting(SettingsName.AFCD_APPROVED_LPI_OPERATION)
        if lpi_support:
            # Need to call afcd_get_info() ?
            message = "Confirm the DUT does not transmit above LPI limits"
        else:
            message = "Confirm the DUT does not transmit in the band"
        title = type(self).__name__
        manual_mode = InstructionLib.get_setting(SettingsName.MANUAL_DUT_MODE)
        if not manual_mode:
            InstructionLib.post_popup_message(
                message,
                [UiPopupButtons.POP_UP_BUTTON_YES, UiPopupButtons.POP_UP_BUTTON_NO],
                title,
                UiPopupButtons.POP_UP_BUTTON_NO,
            )
        AFCLib.set_afc_response("USA")

        InstructionLib.send_script_status(
            "Step 2 : Send an Available Spectrum Inquiry Request", 20
        )
        # 0: Default, 1: Channel based, 2: Freq based
        req_type = "0"
        InstructionLib.afcd_operation({AFCParams.SEND_SPECTRUM_REQ.value: req_type})
        if manual_mode:
            InstructionLib.post_popup_message(
                message,
                [UiPopupButtons.POP_UP_BUTTON_YES, UiPopupButtons.POP_UP_BUTTON_NO],
                title,
                UiPopupButtons.POP_UP_BUTTON_NO,
            )

        InstructionLib.send_script_status(
            "Step 3 : AFC Test Harness validates mandatory registration information", 40
        )
        InstructionLib.wait(5)

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
            user_button, user_input = InstructionLib.get_popup_response()
            return

        req_valid = super().verify_req_infor(afc_resp["receivedRequest"])
        InstructionLib.append_measurements("AFC_REG_INFO", req_valid, "Valid mandatory registration information")

        InstructionLib.send_script_status(
            "Step 5 : RF Test Equipment verification", 80
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

    def teardown(self):
        """Method to reset the AFC DUT after test execution."""
        super().teardown()

    def get_testscript_version(self):
        """Method returns the version number of test scripts."""
        return "1.0"
