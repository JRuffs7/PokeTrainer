from dataaccess import eventda


def GetEventName(eventId: str):
	event = eventda.GetEvent(eventId)
	return event.EventName if event else ''