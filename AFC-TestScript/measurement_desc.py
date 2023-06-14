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

"""@package measurement_desc.py : measurement description.

Contains the description of measurement for AFC DUT.
"""

measure_desc = {
    "AFC_DUT_SP_OPERATION": "AFC DUT transmit with standard power in the band before the Spectrum Inquiry Response",
    "AFC_DUT_SEND_SPECTRUM_INQUIRYREQUEST": "AFC DUT sends an Available Spectrum Inquiry Request",
    "AFC_DUT_SPECTRUM_INQUIRYREQUEST_VALID": "Valid mandatory registration information",
    "AFC_DUT_CONFORM_SPECTRUM_INQUIRYRESPONSE": "AFC DUT conforms to the conditons in the Spectrum Inquiry Response",
    "AFC_DUT_CONFORM_ADJACENT_FREQUENCIES_EMISSIONS_LIMITS": "AFC DUT conforms to not exceed emissions limits in adjacent frequencies",
    "AFC_DUT_SP_OPERATION_NO_REQ": "AFC DUT transmit with standard power in the band in no Spectrum Inquiry Request case",
}
