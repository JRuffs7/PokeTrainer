from dataclasses import dataclass, fields

@dataclass
class Server:
  ServerName: str = ''
  ServerId: int = 0
  ChannelId: int = 0
  LastActivity: str = ''

  @classmethod
  def from_dict(cls, dict):
    field_names = {field.name for field in fields(cls)}
    returnObj = cls(**{k: v for k, v in dict.items() if k in field_names})
    return returnObj