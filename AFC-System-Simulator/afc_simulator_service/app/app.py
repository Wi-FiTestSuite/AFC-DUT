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
"""@package app.py : Point of entry for the device manager app

Package that launches the device manager service, Module responsible for communication with DUT.
"""
import sys
import os
from flask import Flask

sys.path.append(os.path.abspath("./QuickTrack-Tool/Test-Services"))
from afc_simulator_service_api import afc_simulator_api_blueprint
from commons.microservices_helper import MicroserviceHelper

service_name = "PY_AFC_SIMULATOR"
indigo_configs_path = "/var/log/indigo_configs/"
crt_path = os.path.abspath("./QuickTrack-Tool/Test-Services/AppData/testserver_wfatestorg_org.crt")
key_path = os.path.abspath("./QuickTrack-Tool/Test-Services/AppData/testserver.wfatestorg.org.key")

def run_app():
    """Start AFC simulator microservice

    Starts a local flask server on available port and loads the AFC simulator app
    """
    #To hide warning message "Do not use the development server in a production environment"
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None

    app = Flask(__name__)
    app.config["ENV"] = os.environ.get("ENV_MODE")
    service_port = 443
    app.config.swagger_ui_doc_expansion = "list"  # Initial expansion state
    MicroserviceHelper(service_name, service_port)
    app.register_blueprint(afc_simulator_api_blueprint)
    print(os.path.abspath(os.curdir))
    app.run(host="0.0.0.0", port=service_port, ssl_context=(crt_path, key_path))


if __name__ == "__main__":
    run_app()
