"""
python3.8
@author: Alexander Nähring
Rohde & Schwarz GmbH & Co KG
Created on 2020-Aug-13
"""
import math
from typing import Tuple
from numbers import Real

__exp = {
    "y": -24,
    "z": -21,
    "a": -18,
    "f": -15,
    "p": -12,
    "n": -9,
    "µ": -6,  # AltGr + M = "micro-symbol"
    "μ": -6,  # Greek My, unicode compatible to "micro-symbol"
    "u": -6,  # some sources use u instead of µ
    "m": -3,
    "c": -2,
    "d": -1,
    "": 0,
    "k": 3,
    "M": 6,
    "G": 9,
    "T": 12,
    "P": 15,
    "E": 18,
    "Z": 21,
    "Y": 24,
}

__prefix = {
    -24: "y",
    -21: "z",
    -18: "a",
    -15: "f",
    -12: "p",
    -12: "n",
    -6: "µ",
    -3: "m",
    -2: "c",
    -1: "d",
    0: "",
    3: "k",
    6: "M",
    9: "G",
    12: "T",
    15: "P",
    18: "E",
    21: "Z",
    24: "Y",
}


def get_si_factor(number: Real) -> Tuple[int, str]:
    """
    get the factor and SI prefix for the given number to be used for displaying in human readable format
    :param number: raw number
    :return: Tuple[factor: int, prefix: str]
    """
    if number == 0:
        exp = 0
        prefix = ""
    else:
        # get exponent aligned to multiples of 3 (0, 3, 6, 9, 12, ...)
        exp = int(math.log10(abs(number)) // 3 * 3)
        exp = max(-24, exp)
        exp = min(+24, exp)
        prefix = __prefix.get(exp, None)
        if prefix is None:
            raise ValueError(f"Could not determine prefix for factor 1e{exp}")
    return 10 ** exp, prefix


def format_number(number: Real, unit: str = "", decimals: int = 2):
    """
    return a string containing the number with an SI prefix, to easily print numbers with units of any magnitude
    examples:
        format_number(1000, "m") -> "1 km"
        format_number(2.23e10, "Hz") -> "22.3 GHz"
    :param number: raw number
    :param unit: unit to append after the SI prefix
    :param decimals: optional, how many decimals to keep when rounding
    :return:
    """
    factor, prefix = get_si_factor(number)
    number = round(number / factor, decimals)
    if int(number) == number:
        number = int(number)
    return f"{number} {prefix}{unit}"
