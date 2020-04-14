from .base_handler import BaseHandler

def command(arg):
	if callable(arg):
		arg.__gpcp_metadata__ = (BaseHandler.FunctionType.command, arg.__name__)
		return arg
	else:
		def wrapper(func):
			func.__gpcp_metadata__ = (BaseHandler.FunctionType.command, arg)
			return func
		return wrapper

def unknownCommand(func):
	func.__gpcp_metadata__ = (BaseHandler.FunctionType.unknown,)
	return func