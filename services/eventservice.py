import uuid
from dataaccess import eventda
from models.enums import EventType
from models.Event import Event


def GetEvent(eventId: str):
	return eventda.GetEvent(eventId)

def CreateEvent(eventType: EventType):
	newEvent = Event({
		'EventId': uuid.uuid4().hex,
		'EventName': eventType.name,
		'EventType': eventType.value,
		'UserInteractions': {}
	})
	eventda.UpsertEvent(newEvent)
	return newEvent.EventId