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

# TBD: vendor get from UI settings
vendor = "litepoint"
full_name = ".Programs.AFC." + "spectrum_analyzer_" + vendor
mod = importlib.import_module(full_name, "IndigoTestScripts")
SpectrumAnalyzer = mod.SpectrumAnalyzer

class SpectrumAnalyzerLib:
    @staticmethod
    def spectrum_analyzer_connect():
        return SpectrumAnalyzer().spectrum_analyzer_connect()

    @staticmethod
    def spectrum_analyze(channel, bandwidth = 20, timeout = 0):
        return SpectrumAnalyzer().spectrum_analyze(channel, bandwidth, timeout)

    @staticmethod
    def spectrum_analyze_all(timeout = 0):
        return SpectrumAnalyzer().spectrum_analyze_all(timeout)
