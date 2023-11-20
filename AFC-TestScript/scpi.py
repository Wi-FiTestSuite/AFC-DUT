"""
python3.8
@author: Alexander Nähring
Rohde & Schwarz GmbH & Co KG
Created on 2020-Aug-13
"""
import os
import sys
import logging
import time
import socket
import struct
import warnings
from typing import Union, List, BinaryIO, Optional, TypeVar, Protocol, Sized, Iterable
import numpy
import numpy as np
from si_prefix import format_number as sif
import traceback
import math
from typing import Tuple
from numbers import Real

_TERMINATE = False

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
	-9: "n",
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
	get the factor and SI psmbmountrefix for the given number to be used for displaying in human readable format
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

SCPI = logging.INFO - 5  # SCPI logs are more important than DEBUG, but less important than INFO
logging.addLevelName(SCPI, "SCPI")
T = TypeVar("T")


def get_digits(number: Union[str, int]) -> int:
	"""
	get number of digits the integer has when represented as string
	:param number: the number to count the digits of as integer or string
	:return: number of digits (length of string representation of the number)
	Args:
		number:

	Returns:

	"""
	return len(str(number))


class SizedIterable(Iterable[T], Sized, Protocol):
	pass


class Instrument:
	"""
	Base instrument class to connect to any T&M instrument supporting SCPI commands over a TCP/IP socket connection.
	"""

	def __init__(self, ip_address: str, port: int = 5025, timeout: int = 10, get_idn: bool = True,
				get_options: bool = False, preset: bool = False, logger: logging.Logger = None):
		"""
		instrument class constructor.
		Connect to the instrument on ip_address, which can also be a hostname or any FQDN resolving to an IP address.
		:param ip_address: IP address or resolvable name.
		:param port: port number to connect to, default = 5025.
		:param timeout: socket timeout in seconds, or None (blocking), default = 10.
		:param get_idn: whether to request the instrument identification string when connecting, default = True.
			The instrument identification can be accessed using the instrument.idn property.
		:param get_options: whether to request the instrument option string when connecting, default = False.
			The option list can be accessed using the instrument.opt property.
		:param preset: whether to preset the device when connecting, default = False.
			Will call the instrument.preset() method.
		:param logger: optionally specify a logging.Logger,
			if no logger is specified, logging.getLogger(__name__ + "." + ip_address) is used
		"""

		self.__ipaddress = ip_address
		self.__port = port
		self.__socket = None
		self.__timeout = timeout
		self.__buffer_size = 32 * 2 ** 10  # 32 kiByte
		self.__idn_string = ""
		self.__options = None
		self.__termination = b"\n"

		# init logger for this instrument
		self.__logger: Optional[logging.Logger] = logger
		self.__default_logger: logging.Logger = logging.getLogger(__name__ + "." + self.__ipaddress.replace(".", "-"))

		# connect to the instrument
		self.connect(get_idn=get_idn, get_opt=get_options, preset=preset)

	def __del__(self):
		"""
		delete instrument instance, closes the socket
		:return:
		"""
		if self.__socket:
			self.__socket.close()

	def _logger(self) -> logging.Logger:
		"""
		internal logging helper function, return the current or default logger
		:return:
		:rtype:
		"""
		return self.__logger or self.__default_logger

	@classmethod
	def from_instrument(cls, instr: "Instrument") -> "Instrument":
		"""
		Create new instrument instance from an existing instrument
		:param instr: Instrument instance to copy
		:return: copy of instr
		"""
		instr._logger().debug("Create copy of instrument instance")
		return cls(instr.__ipaddress, instr.__port, instr.__timeout, preset=False, logger=instr.logger)

	@property
	def socket(self):
		return self.__socket

	@property
	def ip(self) -> str:
		return self.__ipaddress

	@property
	def idn(self) -> str:
		"""
		the instrument identification string
		"""
		if self.__idn_string == "":
			self.__idn_string = self.query("*IDN?")
		return self.__idn_string

	@property
	def idn_list(self) -> List[str]:
		"""
		the instrument identification string split as list
		"""
		return self.idn.split(",", 3)

	@property
	def idn_company(self) -> str:
		return self.idn_list[0]

	@property
	def idn_name(self) -> str:
		return self.idn_list[1]

	@property
	def idn_serial(self) -> str:
		return self.idn_list[2]

	@property
	def idn_firmware(self) -> str:
		return self.idn_list[3]

	@property
	def opt(self) -> List[str]:
		"""
		return the instrument option string as list of options
		:return:
		"""
		if self.__options is None:
			self.__options = self.query("*OPT?").split(",")
			if "" in self.__options:
				self.__options.remove("")
		return self.__options

	def connect(self, get_idn: bool = True, get_opt: bool = False, preset: bool = False) -> bool:
		"""
		Establish socket connection to the instrument. Is automatically called when instantiating the Instrument obj.
		Socket can raise a ConnectionRefused error if target host cannot be connected.
		:param get_idn: whether to request the instrument identification string when connecting, default = true
		:param get_opt: whether to request the instrument option string when connecting, default = false
		:param preset: whether to preset the device when connecting, default = false
		:return: True if connection succeeded.
		"""

		self._logger().debug(f"connect to instrument at {self.__ipaddress}")
		# todo use socket.create_connection() for IP4 and IP6 support, and easy timeout handling
		self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.__socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
		self.__socket.settimeout(self.__timeout)
		self.__socket.connect((self.__ipaddress, self.__port))
		if preset:
			self.preset()
		# Clear Error Queue
		self.write("*CLS")
		if get_idn:
			_ = self.idn
		if get_opt:
			_ = self.opt
		self._logger().debug(f"connection to {self.__ipaddress} successful")
		return True

	def close(self):
		"""
		Close socket connection
		:return:
		"""
		self._logger().debug("close instrument socket")
		self.__socket.close()
		self.__idn_string = ""
		self.__options = []

	@property
	def logger(self) -> Optional[logging.Logger]:
		"""
		Get assigned instrument logger (None when using default logger)
		:return: logger
		"""
		return self.__logger

	@logger.setter
	def logger(self, logger: logging.Logger = None):
		"""
		Set new logger for this instrument
		:param logger: new logger to use, None = default logger
		"""
		self.__logger = logger

	@property
	def termination(self) -> bytes:
		"""
		Return termination bytes used for sending to and reading from the instrument
		"""
		return self.__termination

	@termination.setter
	def termination(self, termination: bytes):
		"""
		Set termination bytes used for sending to and reading from the instrument
		"""
		self.__termination = termination

	##########
	# Low level functions (read, write)

	def __write_bytes(self, data: bytes) -> int:
		"""
		write data from memory to the socket
		:param data: bytes to write
		:return: number of bytes sent to socket
		"""
		self.__socket.sendall(data)
		return len(data)

	def __write_stream(self, fd: BinaryIO) -> int:
		"""
		write data from a file descriptor (file in binary mode or BytesIO object) to the socket
		:param fp: file descriptor in binary mode to read from
		:return: number of bytes sent to socket
		"""
		b = 0
		while True:
			chunk = fd.read(self.__buffer_size)
			if not chunk:
				break
			b += len(chunk)
			self.__socket.sendall(chunk)
		return b

	def __read_until_termination(self) -> bytes:
		assert self.__termination, "termination character(s) must not be empty"
		assert self.__buffer_size > len(self.__termination), "termination sequence must fit in one data chunk"
		data = b""
		chunks: List[bytes] = []
		# last_time = time.time()
		while True:
			chunk: bytes = self.__socket.recv(self.__buffer_size)
			if chunk:
				# last_time = time.time()
				# append byte chunks to list instead of reallocating new (immutable) bytes string every time
				if self.__termination in chunk:
					# during read it is expected that there is no more content after a termination character
					# because data is only sent after it is actively requested from the instrument.
					# However, it can theoretically happen, that there is more data after the termination sequence.
					# This data is currently lost, as the chunk is truncated and the remaining bytes are skipped.
					# The VISA driver has a low level function that return always when a termination is found,
					# even when requesting more binary data. Essentially this represents an additional buffer layer.
					# TODO implement a low-level socket read function that keeps track of the "buffer" bytes
					chunks.append(chunk[:chunk.find(self.__termination)])
					return b"".join(chunks)
				else:
					chunks.append(chunk)

				# if termination-marker is more than one byte, marker might be split over 2 chunks
				if len(self.__termination) > 2 and len(chunks) > 1:
					# check if termination is found in last two chunks
					if self.__termination in b"".join(chunks[-2:]):
						# combine data and return data up to termination sequence
						data = b"".join(chunks)
						data = data[:data.find(self.__termination)]
						return data
			else:
				# socket did not receive anything, try again after a short time
				# only occurs if no timeout set and non-blocking
				time.sleep(0.001)

	def __read_bytes(self, length: int) -> bytes:
		"""
		Read bytes from the socket.
		:param length: bytes to read
		:return: data as bytes
		"""
		chunks = []
		bytes_left = length
		if length <= 0:
			raise ValueError("Length must be a positive integer")
		while bytes_left > 0:
			buffer = min(self.__buffer_size, bytes_left)
			chunk = self.__socket.recv(buffer)
			if chunk:
				chunks.append(chunk)
				bytes_left -= len(chunk)
		data = b"".join(chunks)
		return data

	def __read_to_stream(self, fp: BinaryIO, length: int):
		"""
		Read bytes from the socket.
		:param fp: binary data stream to write the received data to
		:param length: bytes to read
		:return: data as bytes
		"""
		bytes_left = length
		if length <= 0:
			raise ValueError("Length must be a positive integer")
		while bytes_left > 0:
			buffer = min(self.__buffer_size, bytes_left)
			chunk = self.__socket.recv(buffer)
			fp.write(chunk)
			bytes_left -= len(chunk)

	##########
	# User level functions

	def write(self, cmd: str, termination: bool = True, _suppress_log: bool = False) -> "Instrument":
		"""
		write a string to the instrument
		:param cmd: command to send to the instrument
		:param termination: whether to send the termination bytes after the command
		:param _suppress_log: whether to log the transfer
		:return:
		"""
		if _TERMINATE:
			print("Terminating...")
			raise ValueError("Terminated.")
			
		if not _suppress_log:
			self._logger().log(SCPI, "<< " + cmd)
		data = cmd.encode("ASCII")
		if termination:
			data += self.__termination
		self.__write_bytes(data)
		return self

	def write_bytes(self, data: bytes, termination: bool = False, _suppress_log: bool = False) -> "Instrument":
		"""
		Write bytes to the instrument
		:param data: byte sequence to send
		:param termination: whether to send the termination bytes after command
		:param _suppress_log: whether to log the transfer
		:return:
		"""
		if not _suppress_log:
			self._logger().log(SCPI, "<< [" + str(len(data)) + " Bytes of binary data]")
		if termination:
			data += self.__termination
		self.__write_bytes(data)
		return self

	def write_binary(self, data: bytes, termination: bool = False, _suppress_log: bool = False):
		warnings.warn("write_binary is deprecated, use write_bytes instead", DeprecationWarning)
		self.write_bytes(data=data, termination=termination, _suppress_log=_suppress_log)

	def write_binary_stream(self, fp: BinaryIO, termination: bool = False, _suppress_log: bool = False) -> "Instrument":
		"""
		write binary data from binary stream to instrument
		:param fp: BinaryIO / file-like object
		:param termination: Send message termination sequence at the end
		:param _suppress_log: suppress log message
		:return:
		"""
		if not _suppress_log:
			self._logger().log(SCPI, "<< [Sending data from binary stream...]")
		b = self.__write_stream(fp)
		if termination:
			self.__write_bytes(self.__termination)
		if not _suppress_log:
			self._logger().log(SCPI, f"<< [{sif(b)}Bytes sent]")
		return self

	def read_bytes(self, n_bytes: int, _suppress_log: bool = False) -> bytes:
		"""
		Reads exactly n_bytes from the instrument.
		:param n_bytes: number of bytes to read from the socket
		:param _suppress_log: whether to suppress any log output for this method, default = False
		:return: received data as bytes
		"""
		data = self.__read_bytes(n_bytes)
		if not _suppress_log:
			self._logger().log(SCPI, f">> [received {len(data)} bytes]")
		return data

	def read(self, _suppress_log: bool = False) -> str:
		"""
		Read from the instrument until termination character is found.
		Attention: potential bytes available on the socket after termination character may be discarded!
		:param _suppress_log: whether to suppress any log output for method, default = False
		:return: ASCII decoded message
		"""
		if _TERMINATE:
			print("Terminating...")
			raise ValueError("Terminated.")

		data = self.__read_until_termination()
		# decode bytes as ASCII string
		data = data.decode("ASCII")
		if not _suppress_log:
			self._logger().log(SCPI, ">> " + data)
		return data

	def query(self, command: str, _suppress_log: bool = False) -> str:
		"""
		write to socket and directly read response
		:param command: command to write
		:param _suppress_log: whether to suppress any log output for method, default = False
		:return: instrument reply as string
		"""
		self.write(command, _suppress_log=_suppress_log)
		return self.read(_suppress_log=_suppress_log)

	def __getitem__(self, item: str) -> str:
		item = item.strip()
		# add ? if not in command
		# "?" can be anywhere, not necessarily at the end, e.g. if query needs parameters
		if "?" not in item:
			item = item + "?"
		return self.query(item)

	def __setitem__(self, key, value: Union[str, int, float, bool]):
		if isinstance(value, bool):
			value = int(value)
		self.write(f"{key} {value}")

	@property
	def timeout(self):
		"""
		Returns the specified timeout, 'None' meaning blocking socket
		"""
		return self.__socket.gettimeout()

	@timeout.setter
	def timeout(self, timeout):
		"""
		Set the timeout for the connection (non blocking socket).
		For a blocking socket, use 'None'
		"""
		self.__timeout = timeout
		self.__socket.settimeout(self.__timeout)

	def get_system_error(self) -> str:
		"""
		Return system error
		"""
		result = self.query("SYST:ERR?")
		err_no = int(result.split(",", 1)[0])
		if err_no:
			return result
		else:
			return ""

	def get_all_errors(self) -> List[str]:
		errors: List[str] = []
		while err := self.get_system_error():
			errors.append(err)
		return errors

	# TODO enable "streaming" of large data to file, instead of reading everything to memory first
	def read_binary_block(self, dtype: str = None, numpy_dtype: numpy.dtype = None, fp: BinaryIO = None,
						filename: Union[str, bytes, os.PathLike] = "") -> Optional[Union[bytes, List, int]]:
		"""
		Reads binary data from the instrument.
		The binary data is expected as a binary block of format #dlll<binary>\n with
			d = number of digits of binary block length
			l = length of binary data in bytes
			<binary> binary block data
			if length has more than 9 digits: #(dd)llllllllll<binary>\n
		The raw binary data can be
			- returned as raw data
			- returned as an unpacked list of values of the given data type
			- written to a file-like object (BinaryIO)

		:param dtype: datatype string for interpreting the binary block as list of elements (c.f. struct.unpack)
		:param numpy_dtype: datatype for interpreting the binary block as numpy array (c.f. numpy.frombuffer)
		:param fp: file-like object to write the raw binary data string to, default = None
		:param filename: path to a file to write the raw binary data string to, default = ""
		:return: list of values of the defined datatype
			or numpy array of the defined datatype
			or raw byte string,
			or number of received bytes when streaming to fp or writing to file
		"""
		t = time.perf_counter()

		# read header
		b = self.read_bytes(1, _suppress_log=True)
		if b != b'#':
			raise ValueError(f"binary block must start with #, got {b}")
		byte = self.read_bytes(1, _suppress_log=True)
		if byte == b'(':
			# multiple digits
			digits = ''
			while (byte := self.read_bytes(1, _suppress_log=True)) != b')':
				digits += byte.decode("ASCII")
			digits = int(digits)
		else:
			digits = int(byte.decode("ASCII"))
		length = int(self.read_bytes(digits, _suppress_log=True).decode("ASCII"))

		# read data
		data = None
		if filename:
			fp = open(filename, "wb")
		if fp:
			# read to file or other binary IO
			rx_size = self.__read_to_stream(fp, length)
		else:
			# or read into data buffer
			data = self.read_bytes(length, _suppress_log=True)
			rx_size = len(data)

		# read termination character
		term = self.read_bytes(len(self.__termination), _suppress_log=True)
		if term != self.__termination:
			raise ValueError("termination character not found")

		t = max(time.perf_counter() - t, 1e-9)  # min 1 ns
		self._logger().log(SCPI, ">> [received {sif(rx_size, 'Byte')} of data in {sif(t, 's')} ({sif(rx_size * 8 / t, 'Bit/s')})]")

		if filename:
			fp.close()
		if fp:
			return rx_size

		# unpack binary data to requested datatype
		if numpy_dtype:
			data = np.frombuffer(data, numpy_dtype)
		elif dtype:
			bytes_per_value = {
				"f": 4, "d": 8,
				"q": 8, "Q": 8, "l": 4, "L": 4, "i": 4, "I": 4, "h": 2, "H": 2,
				"b": 1, "B": 1, "?": 1,
			}.get(dtype, 0)
			if bytes_per_value:
				n_values = length // bytes_per_value
				if length % bytes_per_value == 0:
					data = list(struct.unpack(dtype * n_values, data))
				else:
					self._logger().error("binary data length mismatch, cannot unpack binary data")

		return data

	def query_binary_block(self, cmd: str, dtype: str = None, numpy_dtype: numpy.dtype = None, filename: str = "",
						fp: BinaryIO = None) -> Union[bytes, List, int]:
		"""
		write command to and subsequently read binary data block from instrument
		:param cmd: command to write to the instrument
		:param dtype: datatype string for interpreting the binary block, optional
		:param numpy_dtype: numpy datatype for interpreting the binary block, optional
		:param fp: fileobject to write data to, optional
		:return: dict of valued of the defined datatype or raw bytestring
		"""
		self.write(cmd)
		return self.read_binary_block(dtype=dtype, numpy_dtype=numpy_dtype, filename=filename, fp=fp)

	# TODO enable streaming of large data from file or file-like object instead of reading to memory
	def write_binary_block(self, data: bytes = None, fp: BinaryIO = None, cmd: str = ""):
		"""
		write binary block to the instrument
		:param data: block data
		:return:
		"""
		if fp:
			cp = fp.tell()
			size = fp.seek(0, os.SEEK_END) - cp
			fp.seek(cp)
		else:
			size = len(data)
		digits = len(str(size))
		if digits > 9:
			digits = f"({digits})"
		header = f"{cmd}#{digits}{size}"
		if fp:
			self.write_binary(header.encode("ASCII"), _suppress_log=True)
			self.write_binary_stream(fp, termination=True)
		else:
			self.write_binary(header.encode("ASCII") + data, termination=True)

	def download_file(self, remote_filename: str, local_filename: str):
		return self.query_binary_block(f"MMEM:DATA? '{remote_filename}'", filename=local_filename)

	def upload_file(self, local_filename: str, remote_filename: str):
		with open(local_filename, "rb") as fp:
			return self.write_binary_block(fp=fp, cmd=f"MMEM:DATA '{remote_filename}',")

	def reset(self, preset: bool = True):
		"""
		Reset the connection:
		abort all pending operations, clear error queue, close instrument connection and reconnect.
		:param preset: whether to preset the device after reconnection, default = True
		"""
		self.write("ABORt;*CLS")
		self.close()
		self.connect(preset=preset)

	def preset(self):
		"""
		preset the device and wait for preset to finish
		:return:
		"""
		self.write("*RST")
		self.wait()

	def wait(self, timeout: float = None) -> "Instrument":
		"""
		wait until all operations are complete
		:param timeout: cancel the wait after given timeout in seconds, default = 0 (no timeout)
		:return:
		"""
		start_time = time.time()  # no perf_counter() required
		self._logger().log(SCPI, "<< *OPC;*ESR?")
		# self._log().log(SCPI, "waiting for operation complete...")
		while True:  # loop to allow try/except to re-try
			try:
				while not int(self.query("*OPC;*ESR?", _suppress_log=True)) & 1:
					if timeout and 0 < timeout < time.time() - start_time:
						self._logger().error("timeout while waiting for OPC")
						raise TimeoutError("timeout while waiting for OPC")
					time.sleep(0.001)
			except socket.timeout:
				time.sleep(0.001)
				continue  # socket timeout while waiting for OPC
				# or re-raise as TimeoutError
			break
		t = time.time() - start_time
		self._logger().log(SCPI, f"OPC after {sif(t, 's')}")
		return self

	@classmethod
	def wait_all(cls, instruments: SizedIterable["Instrument"], absolute: bool = False, timeout: float = 0) -> List[
		float]:
		"""
		wait for all passed instruments to OPC, return waiting time for each instrument
		:param instruments: List of instruments
		:param absolute: instead of waiting time, return absolute time.time() when instrument is OPC
		:param timeout: rise TimeoutError when waiting longer than timeout (in seconds)
		:return: List of duration waited for each instrument
		"""
		start_time = time.time()
		times = [0.0] * len(instruments)
		done = []
		for instrument in instruments:
			instrument._logger().log(SCPI, "<< *OPC;ESR?")
		while True:
			for i, instrument in enumerate(instruments):
				if instrument in done:
					continue
				if int(instrument.query("*OPC;*ESR?", _suppress_log=True)) & 1:
					t = time.time()
					if absolute:
						times[i] = t
					else:
						times[i] = t - start_time
					done.append(instrument)
					instrument._logger().log(SCPI, f"OPC after {sif(t - start_time, 's')}")
			if len(done) == len(instruments):
				# all done
				break
			if timeout and (time.time() - start_time) > timeout:
				for instrument in instruments:
					if instrument not in done:
						instrument._logger().log(SCPI, f"timeout while waiting for OPC")
				timeout_idns = ", ".join([inst.idn + "(" + inst.ip + ")" for inst in instruments if inst not in done])
				raise TimeoutError("Timeout while waiting for OPC: " + timeout_idns)
		return times
