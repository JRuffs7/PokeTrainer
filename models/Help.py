from typing import Dict

class Help:
	Name: str
	ShortString: str
	HelpString: str
	RequiresAdmin: bool

	def __init__(self, dict: Dict | None):
		self.Name = dict.get('name') or '' if dict else ''
		self.ShortString = dict.get('shortstring') or '' if dict else ''
		self.HelpString = dict.get('helpstring') or '' if dict else ''
		self.RequiresAdmin = dict.get('requiresadmin') or True if dict else True