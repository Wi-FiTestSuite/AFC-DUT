
# AFC DUT Harness Release 2.0

This release of AFC DUT Harness Release including QuickTrack Tool, AFC Test Module and AFC DUT Module

## QuickTrack Tool
* QuickTrack Tool Installer - 2.0.65.162
    * Functionalities
        * User interface to manage test case sequence
        * Test case execution module to execute test scripts
        * Interface to AFC DUT using configuration and control APIs
        * Report the test result
        * Support FCC and ISED
    * Key Updates 
        * Support test in UNII-5, 6 and 7

## AFC Test Module
* AFC System Sumulator (https://github.com/Wi-FiTestSuite/AFC-DUT/tree/main/AFC-System-Simulator/afc_simulator_service)
    * Functionality  
        * AFC System Simulator module receives Available Spectrum Inquiry Request message from the AFC DUT and responds with pre-defined, based on AFC DUT Test Vectors, Available Spectrum Inquiry Response message
    * Key Updates
        * Support UNII-5, 6 and 7
* AFC Test Scripts (https://github.com/Wi-FiTestSuite/AFC-DUT/tree/main/AFC-TestScript)
    * Functionality
        * Python scripts to control test execution, configure test bed and DUT devices, and record results
    * Key Updates
        * N/A
* AFC Validator
    * Functionality
        * AFC Validator module validates the measurements produced using RF test equipment per the AFC DUT Compliance test plan requirements
    * Key Updates
        * Update the validation for UNII-5, 6 and 7

## AFC DUT Module
* AFC DUT ControlApp (https://github.com/Wi-FiTestSuite/AFC-DUT/tree/main/AFC-ControlAppC)
    * Functionality
        * AFC DUT Control App agent receives and processes the Control APIs. For more information, refer to AFC DUT Control API Specification 
    * Key Updates
        * N/A



# **AFC DUT Harness Release 0.1 - 2022/10/31**

This is the first release of AFC DUT Harness Release, which includes QuickTrack Tool, AFC Test Module and AFC DUT Module

## QuickTrack Tool
* QuickTrack Tool Installer - 2.0.65.46
    * Functionalities
        * User interface to manage test case sequence
        * Test case execution module to execute test scripts
        * Interface to AFC DUT using configuration and control APIs
        * Report the test result 
    * Key Updates 
        * Includes general AFC DUT Configuration settings in UI
        * Includes AFC DUT Test Scripts
        * Includes AFC Simulator implementation to send the AvailableSpectrumInquiryResponse message based on the pre-defined AFC DUT test vector.
        * Manual test mode that allows AFC DUT to configured manually

## AFC Test Module
* AFC System Sumulator (https://github.com/Wi-FiTestSuite/AFC-DUT/tree/main/AFC-System-Simulator/afc_simulator_service)
    * Functionality  
        * AFC System Simulator module receives Available Spectrum Inquiry Request message from the AFC DUT and responds with pre-defined, based on AFC DUT Test Vectors, Available Spectrum Inquiry Response message
    * Key Updates
        * HTTPS service on AFC DUT Harness to handle Available Spectrum Inquiry Request and Response messages based on the AFC DUT Test Vectors
        * Test Vector definitions as per [AFC Device (DUT) Compliance Test Vectors](https://www.wi-fi.org/file/afc-specification-and-test-plans)
        * API interface to dump the received request and transmitted response messages
* AFC Test Scripts (https://github.com/Wi-FiTestSuite/AFC-DUT/tree/main/AFC-TestScript)
    * Functionality
        * Python scripts to control test execution, configure test bed and DUT devices, and record results
    * Key Updates
        * Test Script implementation based on [AFC Device (DUT) Compliance Test plan](https://www.wi-fi.org/file/afc-specification-and-test-plans)
        * Python Test Scripts corresponding to AFC DUT test procedures
        * Test Scripts include user interactions in test sequence
* AFC Validator
    * Functionality
        * AFC Validator module validates the measurements produced using RF test equipment per the AFC DUT Compliance test plan requirements
    * Key Updates
        * The validator is going to implement as the validation methods for test script
        * The methodology is still working in progress. It will be updated once finalizing with TTG and RF equipment vendors.

## AFC DUT Module
* AFC DUT ControlApp (https://github.com/Wi-FiTestSuite/AFC-DUT/tree/main/AFC-ControlAppC)
    * Functionality
        * AFC DUT Control App agent receives and processes the Control APIs. For more information, refer to AFC DUT Control API Specification 
    * Key Updates
        * Implementation of sample AFC DUT Control App for APIs and TLVs based on AFC DUT Control API Specification

