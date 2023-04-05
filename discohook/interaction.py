from .user import User
from .file import File
from .view import View
from .embed import Embed
from .modal import Modal
from .member import Member
from .option import Choice
from .multipart import create_form
from .channel import PartialChannel
from .guild import Guild, PartialGuild
from .enums import InteractionCallbackType
from .message import Message, InteractionResponse, FollowupResponse
from typing import Any, Dict, Optional, List, Union, TYPE_CHECKING
from .params import handle_edit_params, handle_send_params, MISSING, merge_fields

if TYPE_CHECKING:
    from .client import Client


class Interaction:
    """
    Base interaction class for all interactions

    Properties
    ----------
    id: str
        The unique id of the interaction
    type: int
        The type of the interaction
    token: str
        The token of the interaction
    version: int
        The version of the interaction
    application_id: str
        The id of the application that the interaction was triggered for
    data: Optional[Dict[str, Any]]
        The command data payload (if the interaction is a command)
    guild_id: Optional[str]
        The guild id of the interaction
    channel_id: Optional[str]
        The channel id of the interaction
    app_permissions: Optional[int]
        The permissions of the application
    locale: Optional[str]
        The locale of the interaction
    guild_locale: Optional[str]
        The guild locale of the interaction
    
    Parameters
    ----------
    data: Dict[str, Any]
        The interaction data payload
    client: Client
        The request object from fastapi
    """
    def __init__(self, data: Dict[str, Any], client: "Client"):
        self.payload = data
        self.client: "Client" = client
        self.data: Optional[Dict[str, Any]] = data.get("data")

    @property
    def id(self) -> str:
        """
        The unique id of the interaction

        Returns
        -------
        str
        """
        return self.payload["id"]

    @property
    def type(self):
        """
        The type of the interaction

        Returns
        -------
        int
        """
        return self.payload["type"]

    @property
    def token(self) -> str:
        """
        The token of the interaction

        Returns
        -------
        str
        """
        return self.payload["token"]

    @property
    def version(self) -> int:
        """
        The version of the interaction

        Returns
        -------
        int
        """
        return self.payload["version"]

    @property
    def application_id(self) -> str:
        """
        The id of the application that the interaction was triggered for

        Returns
        -------
        str
        """
        return self.payload["application_id"]

    @property
    def guild_id(self) -> Optional[str]:
        """
        The guild id of the interaction

        Returns
        -------
        Optional[str]
        """
        return self.payload.get("guild_id")

    @property
    def channel_id(self) -> str:
        """
        The channel id of the interaction

        Returns
        -------
        Optional[str]
        """
        return self.payload["channel_id"]

    @property
    def app_permissions(self) -> Optional[int]:
        """
        The permissions of the application

        Returns
        -------
        Optional[int]
        """
        return self.payload.get("app_permissions")

    @property
    def locale(self) -> Optional[str]:
        """
        The locale of the interaction

        Returns
        -------
        Optional[str]
        """
        return self.payload.get("locale")

    @property
    def guild_locale(self) -> Optional[str]:
        """
        The guild locale of the interaction

        Returns
        -------
        Optional[str]
        """
        return self.payload.get("guild_locale")

    @property
    def channel(self) -> PartialChannel:
        """
        The channel where the interaction was triggered

        Returns
        -------
        PartialChannel
        """
        return PartialChannel({"id": self.channel_id}, self.client)

    @property
    def author(self) -> Optional[Union[User, Member]]:
        """
        The author of the interaction

        If the interaction was triggered in a guild, this will return a member object else it will return user object.

        Returns
        -------
        Optional[Union[User, Member]]
        """
        member = self.payload.get("member")
        user = self.payload.get("user")
        if member:
            member.update(member.pop("user", {}))
            member["guild_id"] = self.guild_id
            return Member(member, self.client)
        else:
            return User(user, self.client)

    @property
    def guild(self) -> Optional[PartialGuild]:
        if not self.guild_id:
            return
        return PartialGuild(self.guild_id, self.client)
    
    async def fetch_guild(self) -> Optional[Guild]:
        """
        Fetches the guild of the interaction

        Returns
        -------
        Guild
        """
        if self.guild_id:
            resp = await self.client.http.fetch_guild(self.guild_id)
            data = await resp.json()
            return Guild(data, self.client)

    async def send_modal(self, modal: Modal):
        """
        Sends a modal to the interaction

        Parameters
        ----------
        modal: Modal
            The modal to send
        """
        self.client.active_components[modal.custom_id] = modal
        # for comp in modal.components:
        #     self.client.active_components[comp.custom_id] = comp
        payload = {
            "data": modal.to_dict(),
            "type": InteractionCallbackType.modal.value,
        }
        await self.client.http.send_interaction_callback(self.id, self.token, payload)

    async def autocomplete(self, choices: List[Choice]):
        """
        Sends autocomplete choices to the interaction

        Parameters
        ----------
        choices: List[Choice]
            The choices to send
        """
        payload = {
            "type": InteractionCallbackType.autocomplete_result.value,
            "data": {"choices": [choice.to_dict() for choice in choices]},
        }
        await self.client.http.send_interaction_callback(self.id, self.token, payload)

    async def defer(self, ephemeral: bool = False):
        """
        Defers the interaction

        Parameters
        ----------
        ephemeral: bool
            Whether the successive responses should be ephemeral or not
        """
        payload = {
            "type": InteractionCallbackType.deferred_channel_message_with_source.value,
        }
        if ephemeral:
            payload["data"] = {"flags": 64}
        await self.client.http.send_interaction_callback(self.id, self.token, payload)

    async def response(
        self,
        content: Optional[str] = None,
        *,
        embed: Optional[Embed] = None,
        embeds: Optional[List[Embed]] = None,
        view: Optional[View] = None,
        tts: Optional[bool] = False,
        file: Optional[File] = None,
        files: Optional[List[File]] = None,
        ephemeral: Optional[bool] = False,
        suppress_embeds: Optional[bool] = False,
    ) -> InteractionResponse:
        """
        Sends a response to the interaction

        Parameters
        ----------
        content: Optional[str]
            The content of the message to send
        embed: Optional[Embed]
            The embed to send with the message
        embeds: Optional[List[Embed]]
            The list of embeds to send with the message (max 10)
        view: Optional[View]
            The view to send with the message
        tts: Optional[bool]
            Whether the message should be sent as tts or not
        file: Optional[File]
            The file to send with the message
        files: Optional[List[File]]
            The list of files to send with the message
        ephemeral: Optional[bool]
            Whether the message should be ephemeral or not
        suppress_embeds: Optional[bool]
            Whether the embeds should be suppressed or not

        Returns
        -------
        InteractionResponse
        """
        data = handle_send_params(
            content=content,
            embed=embed,
            embeds=embeds,
            view=view,
            tts=tts,
            file=file,
            files=files,
            ephemeral=ephemeral,
            suppress_embeds=suppress_embeds,
        )
        if view:
            self.client.store_inter_token(self.id, self.token)
            self.client.load_components(view)

        payload = {
            "data": data,
            "type": InteractionCallbackType.channel_message_with_source.value,
        }
        await self.client.http.send_interaction_mp_callback(
            self.id, self.token, create_form(payload, merge_fields(file, files)))
        return InteractionResponse(self)

    async def original_response(self) -> Message:
        """
        Gets the original response message of the interaction

        Returns
        -------
        InteractionResponse
            The original response message
        """
        resp = await self.client.http.fetch_original_webhook_message(self.application_id, self.token)
        data = await resp.json()
        return Message(data, self.client)


class ComponentInteraction(Interaction):
    """
    Represents a component interaction subclassed from :class:`Interaction`
    """
    def __init__(self, data: Dict[str, Any], client: "Client"):
        super().__init__(data, client)

    @property
    def message(self) -> Optional[Message]:
        """
        The message that the component was clicked on

        Returns
        -------
        Optional[Message]
            The message that the component was clicked on
        """
        return Message(self.payload["message"], self.client)

    @property
    def originator(self) -> User:
        """
        The user that used the component

        Returns
        -------
        User
        """
        return User(self.message.interaction_data["user"], self.client)

    @property
    def from_originator(self) -> bool:
        """
        Whether the interaction was from the original author of the message

        Returns
        -------
        bool
        """
        return self.originator == self.author

    async def followup(
        self,
        content: Optional[str] = None,
        *,
        embed: Optional[Embed] = None,
        embeds: Optional[List[Embed]] = None,
        view: Optional[View] = None,
        tts: Optional[bool] = False,
        file: Optional[File] = None,
        files: Optional[List[File]] = None,
        ephemeral: Optional[bool] = False,
        suppress_embeds: Optional[bool] = False,
    ) -> FollowupResponse:
        """
        Sends a followup message to the interaction

        Parameters
        ----------
        content: Optional[str]
            The content of the message to send
        embed: Optional[Embed]
            The embed to send with the message
        embeds: Optional[List[Embed]]
            The list of embeds to send with the message (max 10)
        view: Optional[View]
            The view to send with the message
        tts: Optional[bool]
            Whether the message should be sent as tts or not
        file: Optional[File]
            The file to send with the message
        files: Optional[List[File]]
            The list of files to send with the message
        ephemeral: Optional[bool]
            Whether the message should be ephemeral or not
        suppress_embeds: Optional[bool]
            Whether the message should suppress embeds or not
        """
        data = handle_send_params(
            content=content,
            embed=embed,
            embeds=embeds,
            view=view,
            tts=tts,
            file=file,
            files=files,
            ephemeral=ephemeral,
            suppress_embeds=suppress_embeds,
        )
        if view:
            self.client.store_inter_token(self.id, self.token)
            self.client.load_components(view)

        payload = {
            "data": data,
            "type": InteractionCallbackType.channel_message_with_source.value,
        }
        resp = await self.client.http.send_interaction_mp_callback(
            self.id, self.token, create_form(payload, merge_fields(file, files))
        )
        data = await resp.json()
        return FollowupResponse(data, self)

    async def edit_original(
        self,
        content: Optional[str] = MISSING,
        *,
        embed: Optional[Embed] = MISSING,
        embeds: Optional[List[Embed]] = MISSING,
        view: Optional[View] = MISSING,
        tts: Optional[bool] = MISSING,
        file: Optional[File] = MISSING,
        files: Optional[List[File]] = MISSING,
        suppress_embeds: Optional[bool] = MISSING,
    ):
        """
        Edits the original message of the interaction from which the component was interacted.

        Parameters
        ----------
        content: Optional[str]
            The edited content of the message
        embed: Optional[Embed]
            The edited embed of the message
        embeds: Optional[List[Embed]]
            The edited list of embeds of the message
        view: Optional[View]
            The edited view of the message
        tts: Optional[bool]
            Whether the message should be sent as tts or not
        file: Optional[File]
            The edited file of the message
        files: Optional[List[File]]
            The edited list of files of the message
        suppress_embeds: Optional[bool]
            Whether the message should suppress embeds or not
        """
        data = handle_edit_params(
            content=content,
            embed=embed,
            embeds=embeds,
            view=view,
            tts=tts,
            file=file,
            files=files,
            suppress_embeds=suppress_embeds,
        )
        if view is not MISSING and view:
            self.client.store_inter_token(self.id, self.token)
            self.client.load_components(view)

        payload = {
            "data": data,
            "type": InteractionCallbackType.update_message.value,
        }
        await self.client.http.edit_interaction_mp_callback(
            self.id, self.token, create_form(payload, merge_fields(file, files))
        )

    @property
    def origin(self) -> Optional[str]:
        """
        The original token of the interaction (if it is a follow up)

        Returns
        -------
        Optional[str]
        """
        if not self.message:
            return
        parent_id = self.message.interaction_data["id"]
        return self.client.cached_inter_tokens.get(parent_id, "")

    async def original_message(self) -> Optional[Message]:
        """
        Gets the original message of the interaction

        Returns
        -------
        Optional[Message]
        """
        if not self.origin:
            return
        resp = await self.client.http.fetch_original_webhook_message(self.application_id, self.origin)
        data = await resp.json()
        return Message(data, self.client)

    async def delete_original(self):
        """
        Deletes the original message of the interaction
        """
        if not self.origin:
            return
        self.client.cached_inter_tokens.pop(self.id, None)
        await self.client.http.delete_webhook_message(self.application_id, self.origin, "@original")
