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
import importlib
from IndigoTestScripts.helpers.instruction_lib import InstructionLib
from commons.shared_enums import SettingsName

SpectrumAnalyzer = None

class SpectrumAnalyzerLib:
    """
    A library for interacting with a spectrum analyzer device.

    Notes:
        - The class provides static methods for connecting to the spectrum analyzer, performing spectrum analysis,
          analyzing all channels, and uploading support data.
        - The specific implementation details of the spectrum analyzer are handled by the vendor-specific modules.
        - Currently, the class supports the "litepoint" vendor, and other vendors can be added by uncommenting and
          updating the code accordingly.
    """

    def __init__(self):
        """
        Initializes the SpectrumAnalyzerLib class.

        Notes:
            - The vendor for the spectrum analyzer is determined based on the configured operation type.
            - The vendor-specific module is imported dynamically based on the determined vendor.
        """
        global SpectrumAnalyzer
        op_type = InstructionLib.get_setting(SettingsName.SPECTRUM_ANALYZER_OP_TYPE)
        if "litepoint" in op_type.lower():
            vendor = "litepoint"
        
        # Uncomment this line for new RF equipment vendor and we can
        #     implement the codes in spectrum_analyzer_vendor_sample.py
        # vendor = "vendor_sample"

        full_name = ".Programs.AFC." + "spectrum_analyzer_" + vendor
        mod = importlib.import_module(full_name, "IndigoTestScripts")
        SpectrumAnalyzer = mod.SpectrumAnalyzer

    @staticmethod
    def spectrum_analyzer_connect():
        """
        Connects to the spectrum analyzer.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        return SpectrumAnalyzer().spectrum_analyzer_connect()

    @staticmethod
    def spectrum_analyze(channel, bandwidth = 20, timeout = 0):
        """
        Performs spectrum analysis on a specific channel.

        Args:
            channel (int): The channel number to perform the spectrum analysis on.
            bandwidth (int, optional): The bandwidth to be used for the analysis. Defaults to 20.
            timeout (int, optional): The timeout value in seconds. If set to 0, performs a single scan. Defaults to 0.

        Returns:
            dict: A dictionary containing the analysis results.

        Notes:
            - The method delegates the spectrum analysis to the SpectrumAnalyzer instance.
        """
        return SpectrumAnalyzer().spectrum_analyze(channel, bandwidth, timeout)

    @staticmethod
    def spectrum_analyze_all(timeout = 0):
        """
        Performs spectrum analysis on all channels.

        Args:
            timeout (int, optional): The timeout value in seconds. If set to 0, performs a single scan across all channels. Defaults to 0.

        Returns:
            list: A list of dictionaries containing the analysis results for each channel.

        Notes:
            - The method delegates the spectrum analysis to the SpectrumAnalyzer instance.
        """
        return SpectrumAnalyzer().spectrum_analyze_all(timeout)

    @staticmethod
    def spectrum_upload_support_data(step):
        """
        Uploads support data related to spectrum analysis.

        Args:
            step (str): The step or identifier of the support data.

        Notes:
            - The method delegates the support data upload to the SpectrumAnalyzer instance.
        """
        SpectrumAnalyzer().spectrum_upload_support_data(step)