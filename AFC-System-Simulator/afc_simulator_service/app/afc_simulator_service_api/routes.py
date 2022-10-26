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
"""@package routes.py : AFC Simulator APIs.

Contains all the routes that are exposed by the AFC simulator service.
"""
import json
import os
import copy
from datetime import datetime, timedelta
from time import sleep
from flask import request, Response, request_finished
from . import afc_simulator_api_blueprint
from flask_restplus import Api, Resource, fields
from commons.logger import Logger
from commons.shared_enums import (
    LogCategory,
)

json_dir_path = os.path.abspath("./QuickTrack-Tool/Test-Services/afc_simulator_service/app/test_vectors/")
vectors = {}
recv_request = {}
sent_response = {}
resp_wait_time = 0
phase = None
filename_prefix = ""

api = Api(
    app=afc_simulator_api_blueprint,
    doc="/swagger",
    title="AFC Simulator APIs",
    description="Provides an interface to send request to AFC service",
    version="1.0",
    default="AFC Simulator APIs",
    default_label="AFC Simulator API Interface",
    default_mediatype="application/JSON",
)

test_case_control = api.model(
    "test_case_control",
    {
        "unitUnderTest": fields.String(description="Unit Under Test"),
        "purpose": fields.String(description="Purpose"),
        "phase": fields.Integer(description="Different phase of the same test vector"),
        "respWaitTime": fields.Integer(description="Wait time before sending an Available Spectrum Inquiry Response "),
    },
)

def is_inquired_freq_range(freq_range, inquired_list):
    l, h = freq_range
    for low, high in inquired_list:
        if l >= low and h <= high:
            return True
    return False

# API for DUT
@api.route('/availableSpectrumInquiry')
class AvailableSpectrum(Resource):
    @api.response(200, "Success")
    def post(self):
        global vectors
        global recv_request
        global sent_response
        global resp_wait_time
        global phase
        global filename_prefix
        has_channel = False
        has_freq_range = False
        valid_location_num = 0
        recv_request = request.json
        missing_params_resp = {
            "availableSpectrumInquiryResponses": [
                {
                    "requestId": "",
                    "response": {
                        "responseCode": 102,
                        "shortDescription": "One or more fields required to be included in the request are missing.",
                        "supplementalInfo": ""
                    }
                }
            ],
        }
        general_failure_resp = {
            "availableSpectrumInquiryResponses": [
                {
                    "requestId": "",
                    "response": {
                        "responseCode": -1,
                        "shortDescription": "General Failure"
                    },
                }
            ],
        }

        # Handling request
        try:
            req_id = 0
            version = recv_request['version']
            req = recv_request['availableSpectrumInquiryRequests'][0]
            Logger.log(LogCategory.DEBUG, f"version {version} received request {req}")
            req_id = req["requestId"]

            # --- Prepare general failure respose ---
            sent_gen_failure_response = copy.deepcopy(general_failure_resp)
            sent_gen_failure_response['version'] = version
            sent_gen_failure_response['availableSpectrumInquiryResponses'][0]["requestId"] = req_id
            # --- ---

            if filename_prefix == "":
                Logger.log(LogCategory.ERROR, f'test vector is not configured')
                return Response(json.dumps(sent_gen_failure_response), mimetype="application/json", status=200)            

            ruleset_ids = req["deviceDescriptor"]['rulesetIds']
            Logger.log(LogCategory.DEBUG, f"requestId {req_id} rulesetIds {ruleset_ids}")
            Logger.log(LogCategory.DEBUG, f"serialNumber {req['deviceDescriptor']['serialNumber']}")
            certId = req['deviceDescriptor']['certificationId'][0]
            Logger.log(LogCategory.DEBUG, f"certificationId - id {certId['id']} nra {certId['nra']}")

            if "location" in req:
                if 'ellipse' in req['location']:
                    valid_location_num += 1
                    center = req['location']['ellipse']['center']
                    Logger.log(LogCategory.DEBUG, f"center {center['latitude']} {center['longitude']}")
                if 'linearPolygon' in req['location']:
                    valid_location_num += 1
                    Logger.log(LogCategory.DEBUG, f"linearPolygon outerBoundary {req['location']['linearPolygon']['outerBoundary']}")
                if 'radialPolygon' in req['location']:
                    valid_location_num += 1
                    center = req['location']['radialPolygon']['center']
                    Logger.log(LogCategory.DEBUG, f"center {center['latitude']} {center['longitude']}")
                    Logger.log(LogCategory.DEBUG, f"radialPolygon outerBoundary {req['location']['radialPolygon']['outerBoundary']}")

            if valid_location_num != 1:
                Logger.log(LogCategory.ERROR, f'Invalid location object number {valid_location_num}')
                return Response(json.dumps(sent_gen_failure_response), mimetype="application/json", status=200)            

            field = "inquiredChannels"
            if field in req:
                oper_class_list = [item["globalOperatingClass"] for item in req[field]]
                Logger.log(LogCategory.DEBUG, f'Inquired globalOperatingClass list {oper_class_list}')
                if len(oper_class_list) > 0:
                    has_channel = True
            field = "inquiredFrequencyRange"
            if field in req:
                freq_range_list = [(item["lowFrequency"], item["highFrequency"]) for item in req[field]]
                Logger.log(LogCategory.DEBUG, f'Inquired FrequencyRange list {freq_range_list}')
                if len(freq_range_list) > 0:
                    has_freq_range = True
        except KeyError as err:
            sent_response = copy.deepcopy(missing_params_resp)
            Logger.log(LogCategory.ERROR, f'KeyError {err}')
            sent_response['version'] = version
            resp = sent_response['availableSpectrumInquiryResponses'][0]
            resp["requestId"] = req_id
            resp["response"]["supplementalInfo"] = {"missingParams": [str(err)]}
            return Response(json.dumps(sent_response), mimetype="application/json", status=200)
        except Exception as err:            
            Logger.log(LogCategory.ERROR, f'Request Exception {err}')
            return Response(json.dumps(sent_gen_failure_response), mimetype="application/json", status=200)
        
        vec = None
        if has_freq_range and has_channel:
                vec = "3"
        elif has_channel:
                vec = "2"
        elif has_freq_range:
                vec = "1"

        Logger.log(LogCategory.DEBUG, f'test vector {vec} filename_prefix {filename_prefix}')
        if vec:
            if phase:
                filename = filename_prefix + vec + f"_phase{phase}.json"
            else:
                filename = filename_prefix + vec + ".json"
            test_case_file = os.path.join(json_dir_path, filename)
            Logger.log(LogCategory.DEBUG, f'test vector file path: {test_case_file}')
            if os.path.exists(test_case_file):
                with open(test_case_file, "r") as f:
                    vectors = json.load(f)
            else:
                Logger.log(LogCategory.ERROR, f"test vector {filename} is not found")
                return Response(json.dumps(sent_gen_failure_response), mimetype="application/json", status=200)

        # Handling response
        if resp_wait_time > 0:
            sleep(resp_wait_time)
        try:
            if vectors:
                sent_response = copy.deepcopy(vectors["responses"])
                sent_response["version"] = version
                resp = sent_response["availableSpectrumInquiryResponses"][0]
                resp["requestId"] = req_id
                expire_time = datetime.now() + timedelta(days=1)
                resp["availabilityExpireTime"] = expire_time.strftime("%Y-%m-%dT%H:%M:%SZ")
                resp["rulesetId"] = ruleset_ids[0]

                field = "availableChannelInfo"
                if field in resp:
                    chan_info = resp[field]
                    resp[field] = []
                    for item in chan_info:
                        if item["globalOperatingClass"] in oper_class_list:
                            resp[field].append(item)

                field = "availableFrequencyInfo"
                if field in resp:
                    freq_info = resp[field]
                    resp[field] = []
                    for item in freq_info:
                        freq_range = item["frequencyRange"]
                        if is_inquired_freq_range((freq_range["lowFrequency"], freq_range["highFrequency"]) , freq_range_list):
                            resp[field].append(item)

                return Response(json.dumps(sent_response), mimetype="application/json", status=200)
            else:                
                Logger.log(LogCategory.ERROR, f"test vector is not found")
                return Response(json.dumps(sent_gen_failure_response), mimetype="application/json", status=200)
        except Exception as err:            
            Logger.log(LogCategory.ERROR, f'Response Exception {err}')        
            return Response(json.dumps(sent_gen_failure_response), mimetype="application/json", status=200)

# APIs for test scripts
@api.route('/set-response')
class SetResponse(Resource):
    @api.response(200, "Success")
    @api.response(400, "Exception occurs")
    @api.expect(test_case_control, validate=True)
    def post(self):
        global vectors
        global recv_request
        global sent_response
        global resp_wait_time
        global filename_prefix
        global phase
        tc = request.json
        vectors = {}
        recv_request = {}
        sent_response = {}
        resp_wait_time = 0
        phase = None
 
        try:
            filename_prefix = f'{tc["unitUnderTest"]}_{tc["purpose"]}_'
            if "phase" in tc:
                phase = tc["phase"]
            if "respWaitTime" in tc:
                resp_wait_time = tc["respWaitTime"]
                response = {"message": "Success"}
                return Response(json.dumps(response), mimetype="application/json", status=200)
        except Exception as err:
            response = {"message": f"Exception : {err}"}
            return Response(json.dumps(response), mimetype="application/json", status=400)

@api.route('/get-status')
class GetStatus(Resource):
    @api.response(200, "Success")
    def get(self):
        global vectors
        global recv_request
        global sent_response
        response = {"currentTestVector": vectors,
                    "receivedRequest" : recv_request,
                    "sentResponse" : sent_response
                    }
        return Response(json.dumps(response), mimetype="application/json", status=200)

@api.route('/reset')
class SetResponse(Resource):
    @api.response(200, "Success")
    @api.response(400, "Exception occurs")
    def post(self):
        global vectors
        global recv_request
        global sent_response
        global resp_wait_time
        global filename_prefix
        global phase
        vectors = {}
        recv_request = {}
        sent_response = {}
        resp_wait_time = 0
        phase = None
        filename_prefix = ""
 
        try:
            response = {"message": "Success"}
            return Response(json.dumps(response), mimetype="application/json", status=200)
        except Exception as err:
            response = {"message": f"Exception : {err}"}
            return Response(json.dumps(response), mimetype="application/json", status=400)