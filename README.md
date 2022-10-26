# **General Information**


This repository includes the following source code for AFC DUT Test Harness. 

* AFC System Simulator - The simulator is a plugin package of Wi-Fi Alliance QuickTrack Test Tool (*1). The simulator is to simulate the AFC system to response to AvaialbleSprectrumInquiryRequest based on the test vectors defined in AFC DUT Test Plan. 
  
* AFC DUT Test Script - The Test Scripts are implemented according to AFC DUT Test Plan, and the implementation is base on Wi-Fi Alliance QuickTrack Test Tool. The test scripts for AFC DUT test can be found in this repository
  
* AFC ControlApp - The ConftolApp is a DUT test control agent to interact with Wi-Fi Alliance QuickTrack Test Tool for test automatiion. The controlApp in this repository is based on the https://github.com/Wi-FiQuickTrack/Wi-FiQuickTrack-ControlAppC 
  

*1 Wi-Fi Alliance QuickTrack Test Tool is a Wi-Fi automation test tool for Wi-Fi Certification. 

<br /><br />
# **How To Use**

The source code of AFC System Simulator and AFC DUT Test Script in this repository are required Wi-Fi Alliance QuickTrack Test Tool. The Wi-Fi Alliance QuickTrack Test Tool Installer will be available to download with acceptance of terms for AFC DUT Test later.


## Apply the changes of AFC System Simulator
AFC System Simulator requires Wi-Fi Alliance QuickTrack Test Tool pre-installed on Ubuntu 20.04.1. 
User can download the afc_simulator_service folder under AFC-DUT/AFC-System-Simulator of this repository, then overwrite the folder, **/usr/local/bin/WFA-QuickTrack-Tool/QuickTrack-Tool/Test-Services/afc_simulator_service** on the QuickTrack Test Tool installed device.

## Apply the changes of AFC DUT Test Script
AFC DUT Test Script requires Wi-Fi Alliance QuickTrack Test Tool pre-installed on Ubuntu 20.04.1. 
User can download all files under AFC-DUT/AFC-TestScript of this repository, then overwrite the files under **/usr/local/bin/WFA-QuickTrack-Tool/IndigoTestScripts/Programs/AFC** on the QuickTrack Test Tool installed device.

## Build AFC ControlApp
DUT vendor can port the AFC ControlApp for their own device for test automation with QuickTrack Test Tool
### AFC DUT ControlApp Customization
DUT vendor can customize the API handler functions in indigo_api_callback_afc.c for their own product.
There are 3 API handlers can be customized.
* afcd_configure_handler
* afcd_operation_handler
* afcd_get_info_handler
### Compiling
ControlApp is implemented in C lanaguage. User might need to modify the makefile based on toolchain

### Executing controlApp
Execute ```./app ```


<br /><br />
# **License**

Copyright (c) 2022 Wi-Fi Alliance                                                

Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted, provided that the above copyright notice and this permission notice appear in all copies.   

THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF ONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
