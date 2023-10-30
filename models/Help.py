from typing import Dict

class Help:
	Name: str
	ShortString: str
	HelpString: str
	RequiresAdmin: bool

	def __init__(self, dict: Dict | None):
		self.Name = dict.get('Name') or '' if dict else ''
		self.ShortString = dict.get('ShortString') or '' if dict else ''
		self.HelpString = dict.get('HelpString') or '' if dict else ''
		self.RequiresAdmin = dict.get('RequiresAdmin') or True if dict else True