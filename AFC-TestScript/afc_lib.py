# Copyright (c) 2020 Wi-Fi Alliance                                                

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
from IndigoTestScripts.helpers.instruction_lib import InstructionLib

class AFCLib:
    @staticmethod
    def set_afc_response(purpose, phase=None, resp_wait_time=0):
        setting = {
            "unitUnderTest": "AFCD",
            "purpose": purpose
        }
        if resp_wait_time:
            setting["respWaitTime"] = resp_wait_time
        if phase:
            setting["phase"] = phase
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
        res = requests.post(url="https://localhost/afc-simulator-api/set-response", json=setting, verify=False)
        if res.status_code != 200:
            InstructionLib.log_error(f"Set current test status failed, status code: {res.status_code}")
            return None

    @staticmethod
    def get_afc_status():
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
        res = requests.get(url="https://localhost/afc-simulator-api/get-status", verify=False)
        if res.status_code != 200:
            InstructionLib.log_error(f"Get current test status failed, status code: {res.status_code}")
            return None
        else:
            json_response =  json.loads(res.text)
            InstructionLib.log_debug(f"current test status : {json_response}")
            return json_response

    @staticmethod
    def reset_afc():
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
        res = requests.post(url="https://localhost/afc-simulator-api/reset", verify=False)
        if res.status_code != 200:
            InstructionLib.log_error(f"Set current test status failed, status code: {res.status_code}")
            return None