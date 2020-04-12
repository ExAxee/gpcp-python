from json import loads
from utils import ENCODING

class TypeBase:
	@staticmethod
	def fromString(str):
		raise NotImplementedError()

class Bytes(TypeBase):
	@staticmethod
	def fromString(str):
		return str

class String(TypeBase):
	@staticmethod
	def fromString(str):
		return str.decode(ENCODING)

class Integer(TypeBase):
	@staticmethod
	def fromString(str):
		return int(str.decode(ENCODING), base=10)

class HexInteger(TypeBase):
	@staticmethod
	def fromString(str):
		return int(str.decode(ENCODING), base=16)

class Float(TypeBase):
	@staticmethod
	def fromString(str):
		return float(str.decode(ENCODING))

class Json(TypeBase):
	@staticmethod
	def fromString(str):
		return loads(str.decode(ENCODING))