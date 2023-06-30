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

# This file will be copied to: /usr/local/bin/WFA-QuickTrack-Tool/IndigoTestScripts/Programs/AFC/
import requests
from urllib3.exceptions import InsecureRequestWarning
import json
import os
import subprocess
import shutil
from IndigoTestScripts.helpers.instruction_lib import InstructionLib

class AFCLib:
    @staticmethod
    def set_afc_response(purpose, test_vector, phase=None, resp_wait_time=0, hold_response=False, random=False, only_random_power=False, difference_last_picks=False):
        setting = {
            "unitUnderTest": "AFCD",
            "testVector": test_vector,
            "purpose": purpose
        }
        if resp_wait_time:
            setting["respWaitTime"] = resp_wait_time
        if hold_response:
            setting["holdResponse"] = True
        if phase:
            setting["phase"] = phase
        if only_random_power:
            setting["onlyRandomPower"] = only_random_power

        if random:
            setting["random"] = True
            if difference_last_picks:
                setting["difference_last_picks"] = True

        if "SAU" in purpose:
            setting["random"] = True
            if phase == 2:
                setting["difference_last_picks"] = True            

        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
        res = requests.post(url="http://localhost:5000/afc-simulator-api/set-response", json=setting, verify=False)
        if res.status_code != 200:
            InstructionLib.log_error(f"Set afc response failed, status code: {res.status_code}")
            return None

    @staticmethod
    def set_afc_params(hold_response):
        setting = {
            "holdResponse": hold_response
        }

        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
        res = requests.post(url="http://localhost:5000/afc-simulator-api/set-params", json=setting, verify=False)
        if res.status_code != 200:
            InstructionLib.log_error(f"Set afc parameters failed, status code: {res.status_code}")
            return None

    @staticmethod
    def get_afc_status():
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
        res = requests.get(url="http://localhost:5000/afc-simulator-api/get-status", verify=False)
        if res.status_code != 200:
            InstructionLib.log_error(f"Get current test status failed, status code: {res.status_code}")
            return None
        else:
            json_response =  json.loads(res.text)
            InstructionLib.log_debug(f"current test status : {json.dumps(json_response, indent=4)}")
            return json_response

    @staticmethod
    def reset_afc(type):
        setting = {}
        if type == "setup":
            setting["inquiryFile"] = os.path.join(
                InstructionLib.get_current_testcase_log_dir(), "DUT_Available_Spectrum_Inquiry_Request-Response.txt")
        elif type == "teardown":
            setting["inquiryFile"] = None

        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
        res = requests.post(url="http://localhost:5000/afc-simulator-api/reset", json=setting, verify=False)
        if res.status_code != 200:
            InstructionLib.log_error(f"Reset afc failed, status code: {res.status_code}")
            return None
