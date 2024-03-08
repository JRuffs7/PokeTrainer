class Help:
	Name: str
	ShortString: str
	HelpString: str
	RequiresAdmin: bool

	def __init__(self, dict):
		vars(self).update(dict)