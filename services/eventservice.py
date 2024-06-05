from random import choice

from dataaccess import gymda


def GetRandomSpecialTrainer():
	return choice(gymda.GetAllSpecialTrainers())
