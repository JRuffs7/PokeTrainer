# exception_decor.py
import functools
import logging

def create_logger():
	"""
	Creates a logging object and returns it
	"""
	logger = logging.getLogger("example_logger")
	logger.setLevel(logging.INFO)
	
	# create the logging file handler
	fh = logging.FileHandler("error_logs/errors.log")
	fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
	formatter = logging.Formatter(fmt)
	fh.setFormatter(formatter)
	
	# add handler to logger object
	logger.addHandler(fh)
	return logger


def exception_log(function):
	"""
	A decorator that wraps the passed in function and logs 
	exceptions should one occur
	"""
	@functools.wraps(function)
	async def wrapper(*args, **kwargs):
		try:
			logger = create_logger()
			return await function(*args, **kwargs)
		except:
			# log the exception
			err = f"There was an exception in command '{function.__name__}'"
			logger.exception(f"\nERROR - {function.__name__}\n{err}\n\n")
			
			# re-raise the exception
			raise
	return wrapper