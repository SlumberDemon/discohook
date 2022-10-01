from .enums import option_types
from typing import Optional, List, Dict, Any, Union, Callable


class Choice:
    def __init__(self, name: str, value: str):
        self.name = name
        self.value = value

    def to_json(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value
        }


class Option:
    def __init__(self, name: str, description: str, required: bool = False, *,  type_: option_types):
        self.name = name
        self.description = description
        self.required = required
        self.type = type_.value
        self.data: Dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "type": self.type
        }


class StringOption(Option):
    def __init__(
            self,
            name: str,
            description: str,
            *,
            required: Optional[bool] = False,
            max_length: Optional[int] = 100,
            min_length: Optional[int] = 1,
            choices: Optional[List[Choice]] = None,
            auto_complete: Optional[bool] = False,
    ):
        self.choices = choices
        self.auto_complete = auto_complete
        self.max_length = max_length
        self.min_length = min_length
        super().__init__(name, description, required, type_=option_types.string)

    def to_json(self) -> Dict[str, Any]:
        if self.choices:
            self.data["choices"] = [choice.to_json() for choice in self.choices]
        if self.auto_complete:
            self.data["autocomplete"] = self.auto_complete
        if self.max_length:
            self.data["max_length"] = self.max_length
        if self.min_length:
            self.data["min_length"] = self.min_length
        return self.data

class IntegerOption(Option):
    def __init__(
            self,
            name: str,
            description: str,
            *,
            required: Optional[bool] = False,
            max_value: Optional[int] = None,
            min_value: Optional[int] = None,
            choices: Optional[List[Choice]] = None,
            auto_complete: Optional[bool] = False,
    ):
        self.choices = choices
        self.auto_complete = auto_complete
        self.max_value = max_value
        self.min_value = min_value
        super().__init__(name, description, required, type_=option_types.integer)

    def to_json(self) -> Dict[str, Any]:
        if self.choices:
            self.data["choices"] = [choice.to_json() for choice in self.choices]
        if self.auto_complete:
            self.data["autocomplete"] = self.auto_complete
        if self.max_value is not None:
            self.data["max_value"] = self.max_value
        if self.min_value is not None:
            self.data["min_value"] = self.min_value
        return self.data

class NumberOption(Option):
    def __init__(
            self,
            name: str,
            description: str,
            *,
            required: Optional[bool] = False,
            max_value: Optional[float] = None,
            min_value: Optional[float] = None,
            choices: Optional[List[Choice]] = None,
            auto_complete: Optional[bool] = False,
    ):  
        self.choices = choices
        self.auto_complete = auto_complete
        self.max_value = max_value
        self.min_value = min_value
        super().__init__(name, description, required, type_=option_types.number)

    def to_json(self) -> Dict[str, Any]:
        if self.choices:
            self.data["choices"] = [choice.to_json() for choice in self.choices]
        if self.auto_complete:
            self.data["autocomplete"] = self.auto_complete
        if self.max_value is not None:
            self.data["max_value"] = self.max_value
        if self.min_value is not None:
            self.data["min_value"] = self.min_value
        return self.data

class BooleanOption(Option):
    def __init__(
            self,
            name: str,
            description: str,
            *,
            required: Optional[bool] = False,
    ):
        super().__init__(name, description, required, type_=option_types.boolean)

    def to_json(self) -> Dict[str, Any]:
        return self.data

class UserOption(Option):
    def __init__(
            self,
            name: str,
            description: str,
            *,
            required: Optional[bool] = False,
    ):
        super().__init__(name, description, required, type_=option_types.user)

    def to_json(self) -> Dict[str, Any]:
        return self.data

class ChannelOption(Option):
    def __init__(
            self,
            name: str,
            description: str,
            *,
            required: Optional[bool] = False,
            channel_types: Optional[List[int]] = None,
    ):  
        self.channel_types = channel_types  
        super().__init__(name, description, required, type_=option_types.channel)

    def to_json(self) -> Dict[str, Any]:
        if self.channel_types:
            self.data["channel_types"] = self.channel_types
        return self.data

class RoleOption(Option):
    def __init__(
            self,
            name: str,
            description: str,
            *,
            required: Optional[bool] = False,
    ):
        super().__init__(name, description, required, type_=option_types.role)

    def to_json(self) -> Dict[str, Any]:
        return self.data

class MentionableOption(Option):
    def __init__(
            self,
            name: str,
            description: str,
            *,
            required: Optional[bool] = False,
    ):
        super().__init__(name, description, required, type_=option_types.mentionable)

    def to_json(self) -> Dict[str, Any]:
        return self.data

class AttachmentOption(Option):
    def __init__(
            self,
            name: str,
            description: str,
            *,
            required: Optional[bool] = False,
    ):
        super().__init__(name, description, required, type_=option_types.attachment)

    def to_json(self) -> Dict[str, Any]:
        return self.data
