from enum import Enum

class AFCParams(int, Enum):
    """List of parameters names that are used in the AFC API request message
    """

    ## @brief Defines the version number of the Available Specutrum Inquiry Request
    #  @note TLV Length: Variable, Value: Float - ex: 1.3
    VERSION_NUMBER = 0xB000

    ## @brief Defines Unique ID to identify an instance of an Available Specutrum Inquiry Request
    #  @note TLV Length: Variable, Value: Alphanumeric value
    REQUEST_ID = 0xB001

    ## @brief Defines The derial number of the DUT
    #  @note TLV Length: Variable, Value: Alphanumeric value
    SERIAL_NUMBER = 0xB002

    ## @brief Defines National Regulatory Authority
    #  @note TLV Length: Variable, Value: String - ex: FCC
    NRA = 0XB003

    ## @brief Defines The certification ID of the DUT
    #  @note TLV Length: Variable, Value: Alphanumeric value
    CERT_ID = 0xB004

    ## @brief Defines The identifier of the regulatory rules supported by the DUT
    #  @note TLV Length: Variable, Value: Alphanumeric value
    RULE_SET_ID = 0xB005

    ## @brief Defines Geographic arear within which the DUT is located
    #  @note TLV Length: 0x01, Value: 0: Ellipse 1:LinearPolygon 2: RadialPolygon
    LOCATION_GEO_AREA = 0xB006

    ## @brief Defines The longitude and latitude of the center of DUT ellipse 
    #  @note TLV Length: Variable, Value: "longitude,latitude"
    ELLIPSE_CENTER = 0xB007

    ## @brief Defines The length of the major semi axis of an ellipse within which the DUT is located
    #  @note TLV Length: Variable, Value: Numeric value
    ELLIPSE_MAJOR_AXIS = 0xB008

    ## @brief Defines The length of the minor semi axis of an ellipse within which the DUT is located
    #  @note TLV Length: Variable, Value: Numeric value
    ELLIPSE_MINOR_AXIS = 0xB009

    ## @brief Defines the orientation of the majorAxis field in decimal degrees, measured clockwise from True North
    #  @note TLV Length: 0x01 to 0x03, Value: 0 - 180
    ELLIPSE_ORIENTATION = 0xB00A


    ## @brief Defines the vertices(longitude and latitude) of a polygon within which the DUT is located
    #  @note TLV Length: Variable, Value: longitude,ltitude list with space separate
    LINEARPOLY_BOUNDARY = 0xB00B


    ## @brief Defines The longitude and latitude of the center of DUT RadialPolygon 
    #  @note TLV Length: Variable, Value: "longitude,latitude"
    RADIALPOLY_CENTER = 0xB00C

    ## @brief Defines the vertices(length and angle) of a polygon within which the DUT is located
    #  @note TLV Length: Variable, Value: length,angle list with space separate
    RADIALPOLY_BOUNDARY = 0xB00D

    ## @brief Defines the height of the DUT antenna in meters
    #  @note TLV Length: Variable, Value: Nemeric value

    HEIGHT = 0xB00E
    ## @brief Defines the reference level for the value of the height field
    #  @note TLV Length: Variable, Value: String
    HEIGHT_TYPE = 0xB00F

    ## @brief Defines the height of the DUT antenna in meters
    #  @note TLV Length: Variable, Value: Nemeric value
    VERTICAL_UNCERT = 0xB010

    ## @brief Indicates DUT is indoor deployment
    #  @note TLV Length: 0x01, Value: 0: unknown 1: indoor 2: outdoor
    DEPLOYMENT = 0xB011

    ## @brief Defines Inquired frequency range
    #  @note TLV Length: Variable, Value: lowfreq,highfreq list with space separate
    FREQ_RANGE = 0xB012

    ## @brief Defines Global operating class
    #  @note TLV Length: Variable, Value: Operating class with space separate
    GLOBAL_OPCL = 0xB013
    ## @brief Defines The list of channel center frequency indices
    #  @note TLV Length: Variable, Value: Channel list with space separate
    CHANNEL_CFI = 0xB014
    
    ## @brief Defines minimum Desired EIRP in units of dBm
    #  @note TLV Length: Variable, Value: Numeric value
    MIN_DESIRED_PWR = 0xB015

    ## @brief Defines Field type and payload of a vendor extension
    #  @note TLV Length: Variable, Value: ID: payload
    VENDOR_EXT = 0xB016

    ## @brief Defines the URL of the AFC server
    #  @note TLV Length: Variable, Value: Alphanumeric value
    AFC_SERVER_URL = 0xB017

    ## @brief Defines the SSID to be configured on the DUT
    #  @note TLV Length: 0x00 to 0x1F, Value: Alphanumeric value
    AFC_TEST_SSID = 0xB018

    ## @brief Trigger DUT to its initial pre-test state
    #  @note TLV Length: 0x01, Value: 0(Reserved) or 1
    DEVICE_RESET = 0xB019

    ## @brief Trigger DUT to send Available Spectrum inquiry request
    #  @note TLV Length: 0x01, Value: 0(Default), 1(Channel), 2(Frequency)
    SEND_SPECTRUM_REQ = 0xB01A

    ## @brief Trigger DUT to power cycle
    #  @note TLV Length: 0x01, Value: 0(Reserved) or 1
    POWER_CYCLE = 0xB01B

    ## @brief Specifies Security Configuration
    #  @note TLV Length: 0x01, Value: 0(SAE) or 1(Reserved)
    SECURITY_TYPE = 0xB01C

    ## @brief Defines the pre-shared keys
    #  @note TLV Length: 0x08 to 0xFF, Value: alphanumeric value
    WPA_PASSPHRASE = 0xB01D

    ## @brief Trigger DUT to send test frames
    #  @note TLV Length: 0x01, Value: 0 - 20MHz, 1 - 40MHz, 2 - 80MHz, 3 - 160MHz, 4 - 320MHz
    SEND_TEST_FRAME = 0xB01E

    ## @brief Specifies DUT's bandwidth
    #  @note TLV Length: 0x01, Value: 0 - 20MHz, 1 - 40MHz, 2 - 80MHz, 3 - 160MHz, 4 - 320MHz
    BANDWIDTH = 0xB01F

    ## @brief Defines the Root certificate file configured on DUT
    #  @note TLV Length: Variable, Value: String
    CA_CERT = 0xB020

    ## @brief Trigger DUT to initiate connection procedure between AFC DUT and SP Access Point
    #  @note TLV Length: 0x01, Value: 0(Reserved) or 1
    CONNECT_SP_AP = 0xB021

class GeoArea(str, Enum):
    Ellipse = "0"
    LinearPolygon = "1"
    RadialPolygon = "2"

class Deployment(str, Enum):
    Unknown = "0"
    Indoor = "1"
    Outdoor = "2"

class TestFrameBandwidth(str, Enum):
    BW20  = "0"
    BW40  = "1"
    BW80  = "2"
    BW160 = "3"
    BW320 = "4"

class SpectrumRequestType(str, Enum):
    Default    = "0"
    Channel    = "1"
    Frequency  = "2"

class FixedClientSendRequestMethod(str, Enum):
    InBand    = "In-band"
    OutOfBand    = "Out-of-band"

class AFCResponseTLV(int, Enum):
    """List of TLV used in the QuickTrack API response and ACK messages from the DUT"""

    # MESSAGE(0xA000), STATUS(0XA001) and
    # CONTROL_APP_VERSOIN(0xA004) are reserved

    ## @brief Current operating frequency
    #  @note TLV Length: Variable, Value: Numeric value
    OPER_FREQ = 0xBC00

    ## @brief Current operating channel
    #  @note TLV Length: Variable, Value: Numeric value
    OPER_CHANNEL = 0xBC01

    ## @brief Current Center Frequency Index
    #  @note TLV Length: Variable, Value: Numeric value
    CENTER_FREQ_INDEX = 0xBC02
