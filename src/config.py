import json
from typing import Any, List

import discord

class Configuration:
    def __init__(self, json_str=None):
        if json_str:
            json_data = json.loads(json_str)
            self.create(json_data)

    def create(self, json_data):
        for key, value in json_data.items():
            attr_type = getattr(self, key).__class__
            if issubclass(attr_type, Configuration):
                setattr(self, key, attr_type(value))
            else:
                setattr(self, key, value)
    
    def to_dict(self):
        return {key: self._serialize_attr(value) for key, value in self.__dict__.items()}
    
    def _serialize_attr(self, attr: Any) -> Any:
        if isinstance(attr, Configuration):
            return attr.to_dict()
        elif isinstance(attr, list):
            return [self._serialize_attr(item) for item in attr]
        elif isinstance(attr, discord.SelectOption):
            return {
                "label": attr.label,
                "value": attr.value,
                "description": attr.description
            }
        elif isinstance(attr, discord.CategoryChannel):
            return attr.id
        else:
            return attr
    
    def __repr__(self):
        return f'Configuration({self.__dict__})'


class TicketConfiguration(Configuration):
    def __init__(self, json_str):
        super().__init__(json_str)
    
    def create(self, json_data):
        self.topics: List[discord.SelectOption] = []
        for topic in json_data["topics"]:
            self.topics.append(discord.SelectOption(
                label = topic["name"],
                value = topic["value"],
                description = topic["description"]
            ))

        self.ticket_category_id = json_data["ticket_category"]
    
    def get_ticket_category(self, guild: discord.Guild):
        return guild.get_channel(self.ticket_category_id)

class RolesConfiguration(Configuration):
    def __init__(self, json_str):
        super().__init__(json_str)
    
    def create(self, json_data):
        self.moderator = json_data["moderator"]