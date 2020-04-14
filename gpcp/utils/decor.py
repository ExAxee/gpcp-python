from .base_handler import BaseHandler
from .base_types import String, Integer, Float

def command(arg):
	def getArgumentTypes(func):
		typedArguments = func.__annotations__

		argumentTypes = []
		for argName in func.__code__.co_varnames[2:]:
			argumentType = typedArguments.get(argName, String)

			if argumentType == int:
				argumentType = Integer
			elif argumentType == str:
				argumentType = String
			elif argumentType == float:
				argumentType = Float

			argumentTypes.append(argumentType)

		return argumentTypes

	if callable(arg):
		arg.__gpcp_metadata__ = (BaseHandler.FunctionType.command, arg.__name__, getArgumentTypes(arg))
		return arg
	else:
		def wrapper(func):
			func.__gpcp_metadata__ = (BaseHandler.FunctionType.command, arg, getArgumentTypes(func))
			return func
		return wrapper

def unknownCommand(func):
	func.__gpcp_metadata__ = (BaseHandler.FunctionType.unknown,)
	return func