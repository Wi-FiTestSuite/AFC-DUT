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
"""@package routes.py : AFC Simulator APIs for fixed client connected SP AP.

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
import traceback

json_dir_path = os.path.abspath("./QuickTrack-Tool/Test-Services/afc_fc_ap_service/app/test_vectors/")
vectors = {}
recv_request = {"headers": {}, "body": {}}
valid_request = False
sent_response = {}
resp_wait_time = 0
phase = None
filename_prefix = "default"
hold_response = False
script_test_vector = 0
inquiry_file = None

api = Api(
    app=afc_simulator_api_blueprint,
    doc="/swagger",
    title="AFC Simulator APIs for fixed client connected SP AP",
    description="Provides an interface to send request to AFC service",
    version="1.0",
    default="AFC Simulator APIs for fixed client connected SP AP",
    default_label="AFC Simulator API Interface",
    default_mediatype="application/JSON",
)

test_case_control = api.model(
    "test_case_control",
    {
        "unitUnderTest": fields.String(description="Unit Under Test"),
        "purpose": fields.String(description="Purpose"),
        "testVector": fields.Integer(description="Test vector"),
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

def gen_err_resp(req_id, resp_code, short_desc, version, supp_info=None):
    global sent_response
    response_dict = {
        "requestId": req_id,
        "response": {
            "responseCode": resp_code,
            "shortDescription": short_desc,
        }
    }

    if supp_info is not None:
        response_dict["response"]["supplementalInfo"] = supp_info

    sent_response = {
        "availableSpectrumInquiryResponses": [response_dict],
        "version": version
    }
    append_to_inquiry_file(sent_response)
    return sent_response

def append_to_inquiry_file(json_data):
    if inquiry_file:
        if not os.path.exists(inquiry_file):
            open(inquiry_file, 'a').close()
        border = "###########################"
        timestamp = "   " + datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ') + "   "
        with open(inquiry_file, 'a') as f:
            f.write(border + timestamp + border + '\n' + json.dumps(json_data, indent=4) + '\n\n')

# API for DUT
@api.route('/availableSpectrumInquiry')
class AvailableSpectrum(Resource):
    @api.response(200, "Success")
    @api.response(400, "Bad Request")
    def post(self):
        global vectors
        global recv_request
        global sent_response
        global resp_wait_time
        global phase
        global filename_prefix
        global hold_response
        global valid_request
        has_channel = False
        has_freq_range = False
        valid_location_num = 0

        try:
            # Handling request
            # --- Prepare general failure respose ---
            version = ""
            req_id = 0

            recv_request["headers"] = {k:v for k, v in request.headers.items()}
            content_type = request.headers.get('Content-Type')
            append_to_inquiry_file(request.json)
            if (content_type == 'application/json'):
                recv_request["body"] = request.json
            else:
                recv_request["body"] = {}        
                return Response(json.dumps({"message": f"Content-Type {content_type} not supported! Please use application/json."}), mimetype="application/json", status=400)

            Logger.log(LogCategory.DEBUG, f"[afc-fc-ap-api] Received request from fixed client connected SP AP {json.dumps(recv_request, indent=4)}")

            version = recv_request["body"]['version']
            req = recv_request["body"]['availableSpectrumInquiryRequests'][0]
            req_id = req["requestId"]
            # --- ---

            if filename_prefix == "":
                Logger.log(LogCategory.ERROR, f'test vector is not configured')
                return Response(json.dumps(gen_err_resp(req_id, -1, "General Failure", version)),
                                mimetype="application/json", status=200)

            Logger.log(LogCategory.DEBUG, f"version {version} requestId {req_id}")
            dev_desc = req['deviceDescriptor']
            Logger.log(LogCategory.DEBUG, f"serialNumber {dev_desc['serialNumber']}")

            if not isinstance(dev_desc['certificationId'], list):                        
                Logger.log(LogCategory.ERROR, f'invalidParams certificationId: DATA TYPE should be array of object CertificationId')
                return Response(json.dumps(gen_err_resp(req_id, 103, "One or more fields have an invalid value.", version, {"invalidParams": ["certificationId"]})),
                                mimetype="application/json", status=200)

            ruleset_ids = []
            if version == "1.4":
                for certId in dev_desc['certificationId']:
                    Logger.log(LogCategory.DEBUG, f"certificationId - rulesetId {certId['rulesetId']} id {certId['id']}")
                    if isinstance(certId['rulesetId'], str):
                        ruleset_ids.append(certId['rulesetId'])
                    else:
                        Logger.log(LogCategory.ERROR, f'invalidParams rulesetId: DATA TYPE should be string')
                        return Response(json.dumps(gen_err_resp(req_id, 103, "One or more fields have an invalid value.", version, {"invalidParams": ["rulesetId"]})),
                                        mimetype="application/json", status=200)

            else:
                return Response(json.dumps(gen_err_resp(req_id, 100, "version not supported", version)),
                                mimetype="application/json", status=200)
                # for certId in dev_desc['certificationId']:
                #     Logger.log(LogCategory.DEBUG, f"certificationId - nra {certId['nra']} id {certId['id']}")
                # ruleset_ids = dev_desc['rulesetIds']
                # Logger.log(LogCategory.DEBUG, f"rulesetIds {ruleset_ids}")
                # if not isinstance(ruleset_ids, list):                        
                #     Logger.log(LogCategory.ERROR, f'invalidParams rulesetIds: DATA TYPE should be array of string')
                #     return Response(json.dumps(gen_err_resp(req_id, 103, "One or more fields have an invalid value.", version, {"invalidParams": ["rulesetIds"]})),
                #                 mimetype="application/json", status=200)

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
                return Response(json.dumps(gen_err_resp(req_id, -1, "General Failure", version)),
                                mimetype="application/json", status=200)

            field = "inquiredChannels"
            oper_class_list = []
            if field in req:
                oper_class_list = [item["globalOperatingClass"] for item in req[field]]
                Logger.log(LogCategory.DEBUG, f'Inquired globalOperatingClass list {oper_class_list}')
                if len(oper_class_list) > 0:
                    has_channel = True
            field = "inquiredFrequencyRange"
            freq_range_list = []
            if field in req:
                freq_range_list = [(item["lowFrequency"], item["highFrequency"]) for item in req[field]]
                Logger.log(LogCategory.DEBUG, f'Inquired FrequencyRange list {freq_range_list}')
                if len(freq_range_list) > 0:
                    has_freq_range = True
        except KeyError as err:
            Logger.log(LogCategory.ERROR, f'Missing field {err} in received Available Spectrum Request')
            return Response(json.dumps(gen_err_resp(req_id, 102, "Missing Param.", version,
                                                    {"missingParams": [str(err)]})),
                            mimetype="application/json", status=200)

        except Exception as err:
            exception_str = traceback.format_exc()
            Logger.log(LogCategory.ERROR, f'Response Exception\n {exception_str}')
            return Response(json.dumps(gen_err_resp(req_id, -1, "General Failure", version)),
                                mimetype="application/json", status=200)

        valid_request = True

        vec = None
        if script_test_vector:
            vec = f"{script_test_vector}"
        elif has_freq_range and has_channel:
            vec = "3"
        elif has_channel:
            vec = "2"
        elif has_freq_range:
            vec = "1"

        Logger.log(LogCategory.DEBUG, f'test vector {vec} filename_prefix {filename_prefix}')
        if vec:
            if filename_prefix == "default":
                filename = filename_prefix + ".json"
            elif phase:
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
                return Response(json.dumps(gen_err_resp(req_id, -1, "General Failure", version)),
                                mimetype="application/json", status=200)

        # Handling response
        if hold_response:
            Logger.log(LogCategory.DEBUG, f"Hold an Available Spectrum Inquiry Response")
            while hold_response:                    
                sleep(1)
        if resp_wait_time > 0:
            Logger.log(LogCategory.DEBUG, f"Waits for {resp_wait_time} seconds before sending an Available Spectrum Inquiry Response ")
            sleep(resp_wait_time)
        try:
            if vectors:
                sent_response = copy.deepcopy(vectors["responses"])
                sent_response["version"] = version
                resp = sent_response["availableSpectrumInquiryResponses"][0]
                resp["requestId"] = req_id
                resp["availabilityExpireTime"] = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
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
                Logger.log(LogCategory.DEBUG, "*" * 68)
                Logger.log(LogCategory.DEBUG, f"*  [afc-fc-ap-api] Sending an Available Spectrum Inquiry Response  *")
                Logger.log(LogCategory.DEBUG, "*" * 68)
                append_to_inquiry_file(sent_response)
                return Response(json.dumps(sent_response), mimetype="application/json", status=200)
            else:
                Logger.log(LogCategory.ERROR, f"test vector is not found")
                return Response(json.dumps(gen_err_resp(req_id, -1, "General Failure", version)),
                                mimetype="application/json", status=200)
        except Exception as err:
            exception_str = traceback.format_exc()
            Logger.log(LogCategory.ERROR, f'Response Exception\n {exception_str}')
            return Response(json.dumps(gen_err_resp(req_id, -1, "General Failure", version)),
                            mimetype="application/json", status=200)

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
        global hold_response
        global script_test_vector
        tc = request.json
 
        try:
            if "purpose" in tc:                
                phase = None
                vectors = {}
                recv_request = {"headers": {}, "body": {}}
                sent_response = {}
                resp_wait_time = 0
                filename_prefix = f'{tc["unitUnderTest"]}_{tc["purpose"]}_'
            if "testVector" in tc:
                script_test_vector = tc["testVector"]
            if "phase" in tc:
                phase = tc["phase"]
            if "respWaitTime" in tc:
                resp_wait_time = tc["respWaitTime"]                
            if "holdResponse" in tc:
                hold_response = tc["holdResponse"]
                Logger.log(LogCategory.DEBUG, f'holdResponse {hold_response}')

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
        global valid_request
        response = {"currentTestVector": vectors,
                    "receivedRequestHeaders" : recv_request["headers"],
                    "receivedRequest" : recv_request["body"],
                    "sentResponse" : sent_response,
                    "valid_request" : valid_request
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
        global script_test_vector
        global hold_response
        global inquiry_file
        global valid_request
        vectors = {}
        recv_request = {"headers": {}, "body": {}}
        sent_response = {}
        resp_wait_time = 0
        phase = None
        filename_prefix = "default"
        script_test_vector = 0
        hold_response = False
        valid_request = False

        try:
            if request.json.get("inquiryFile"):
                inquiry_file = request.json["inquiryFile"]
            else:
                inquiry_file = None
 
            response = {"message": "Success"}
            return Response(json.dumps(response), mimetype="application/json", status=200)
        except Exception as err:
            response = {"message": f"Exception : {err}"}
            return Response(json.dumps(response), mimetype="application/json", status=400)