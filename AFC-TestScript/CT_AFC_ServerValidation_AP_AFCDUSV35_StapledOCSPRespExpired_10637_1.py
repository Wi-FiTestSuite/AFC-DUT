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
from IndigoTestScripts.Programs.AFC.measurement_desc import *
from IndigoTestScripts.helpers.instruction_lib import InstructionLib
from commons.shared_enums import *


class CT_AFC_ServerValidation_AP_AFCDUSV35_StapledOCSPRespExpired_10637_1(AFCBaseScript):
    def __init__(self):
        super().__init__(DutType.APUT)
        self.description = (
            "Unsuccessful server validation"
        )

    def setup(self):
        """Setting up all the pre-requisites required for test case execution
        """
        InstructionLib.send_script_status(
            "Step 1: Resetting the AFC DUT to its Initial Pre-test State", 10
        )
        super().setup("afc-https-usv-run-6", stop_ocsp=True)

    def execute(self):
        """Method to execute all the instructions as per test plan after setup."""

	    # setup() in AFCBaseScript created afc_config
        InstructionLib.afcd_configure(self.afc_config)
        AFCLib.reset_afc("setup")
        InstructionLib.afcd_operation({AFCParams.SEND_SPECTRUM_REQ.value: SpectrumRequestType.Default.value})

        InstructionLib.send_script_status(
            "Step 2 : AFC Test Harness waits 10 seconds, and verifies no Available Spectrum Inquiry Request is sent to it", 60
        )
        InstructionLib.wait(10)

        # Get response from AFC Server
        afc_resp = AFCLib.get_afc_status()
        if afc_resp["receivedRequest"]:
            recv_req = True            
        else:
            handshake, unknown_ca = InstructionLib.verify_SSL_handshake()
            if not handshake:
                InstructionLib.log_error("Please Trigger AFC DUT to send Spectrum Inquiry Request !")
                return
            if unknown_ca:
                InstructionLib.log_error("Please Configure the AFC DUT with correct root certificate !")
                return
            recv_req = False
        InstructionLib.append_measurements("AFC_DUT_SEND_SPECTRUM_INQUIRYREQUEST", recv_req, measure_desc["AFC_DUT_SEND_SPECTRUM_INQUIRYREQUEST"])

    def teardown(self):
        """Method to reset the AFC DUT after test execution."""
        super().teardown()

    def get_testscript_version(self):
        """Method returns the version number of test scripts."""
        return "1.0"
