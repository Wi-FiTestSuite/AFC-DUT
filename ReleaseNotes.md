# **AFC DUT Harness Release 0.1 - 2022/10/31**

This is the first release of AFC DUT Harness Release, which includes QuickTrack Tool, AFC Test Module and AFC DUT Module

## QuickTrack Tool
* QuickTrack Tool Installer - 2.0.65.46
    * Functionalities
        * User interface to manage test case sequence
        * Test case execution module to execute test scripts
        * Interface to DUT using configuration and control APIs
        * Display the test result  
    * Key Updates 
        * Includes general AFC DUT Configuration settings in UI
        * Includes 12 AFC DUT Test Scripts in development bundle
        * Includes AFC DUT Simulator to reply the AvailableSpectrumInquiryResponse based on the Test Vector specifid in Test Script.
        * Manaul Test mode is available

## AFC Test Module
* AFC System Sumulator (https://github.com/Wi-FiTestSuite/AFC-DUT/tree/main/AFC-System-Simulator/afc_simulator_service)
    * Module for receiving Spectrum Inquiry request from the AFC DUT and responding with pre-defined Inquiry response 
    * Key Updates
        * HTTPS service on AFC DUT Harness to handle AvailableSpecturmInquiry based on the Test Vectors
        * Test Vector is based on the definition in AFC Device (DUT) Compliance Test Vectors v0.0.1
        * API interface to dump the retrieved Inquiry request and response
        * To indicate the delay of the response
* AFC Test Scripts (https://github.com/Wi-FiTestSuite/AFC-DUT/tree/main/AFC-TestScript)
    * Python scripts to control test execution, configure test bed and DUT devices, and record results
    * Key Updates
        * Test Script implementation is based on AFC Device (DUT) Compliance Test plan v1.2.3
        * 12 Test Scripts are available for 4 AFC DUT Test cases
        * Test Scripts include user interactions in test sequence
        * Validation is implemented as manual validation due to yet finalize the validation methodology. 
* AFC Validator
    * Validates test results produced using RF test equipment against Spectrum Inquiry Response
    * Key Updates
        * The validator is going to implement as the validation methods for test script
        * The methodology is still working in progress. It will be updated once finalizing with TTG and RF equipment vendors.

## AFC DUT Module
* AFC DUT ControlApp (https://github.com/Wi-FiTestSuite/AFC-DUT/tree/main/AFC-ControlAppC)
    * Control App – Agent for receiving and processing the QuickTrack APIs
    * Key Updates
        * Implement the skeleton of APIs and TLVs based on the AFC DUT Contral API Specification

