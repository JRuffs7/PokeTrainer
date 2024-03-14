from dataclasses import dataclass, fields
from models.Event import Event

@dataclass
class Server:
  ServerName: str
  ServerId: int
  ChannelId: int
  CurrentEvent: Event|None

  @classmethod
  def from_dict(cls, dict):
    field_names = {field.name for field in fields(cls)}
    returnObj = cls(**{k: v for k, v in dict.items() if k in field_names})
    returnObj.CurrentEvent = Event.from_dict(returnObj.CurrentEvent) if returnObj.CurrentEvent else None
    return returnObj