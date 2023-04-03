from .user import User
from .role import Role
from .embed import Embed
from .view import View
from .file import File
from .multipart import create_form
from .params import handle_edit_params, MISSING, merge_fields
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Client
    from .interaction import Interaction


class Message:
    """
    Represents a Discord message.

    Attributes
    ----------
    id: :class:`str`
        The id of the message.
    channel_id: :class:`str`
        The id of the channel the message was sent in.
    author: :class:`User`
        The author of the message.
    content: :class:`str`
        The content of the message.
    timestamp: :class:`str`
        The timestamp of the message.
    edited_timestamp: Optional[:class:`str`]
        The timestamp of when the message was last edited.
    tts: :class:`bool`
        Whether the message was sent using text-to-speech.
    mention_everyone: :class:`bool`
        Whether the message mentions everyone.
    mentions: List[:class:`User`]
        The users mentioned in the message.
    mention_roles: List[:class:`Role`]
        The roles mentioned in the message.
    mention_channels: Optional[:class:`dict`]
        The channels mentioned in the message.
    attachments: :class:`dict`
        The attachments in the message.
    embeds: :class:`list`
        The embeds in the message.
    reactions: Optional[:class:`list`]
        The reactions in the message.
        ...
    """
    def __init__(self, payload: Dict[str, Any], client: "Client") -> None:
        self.client = client
        self.data = payload
        self.id = payload.get("id")
        self.type = payload.get("type")
        self.channel_id = payload.get("channel_id")
        self.author = User(payload.get("author"), self.client)
        self.content = payload.get("content")
        self.timestamp = payload.get("timestamp")
        self.edited_timestamp = payload.get("edited_timestamp")
        self.tts = payload.get("tts", False)
        self.mention_everyone = payload.get("mention_everyone", False)
        self.mentions = [User(x, self.client) for x in payload.get("mentions", [])]
        self.mention_roles = [Role(x, self.client) for x in payload.get("mention_roles", [])]
        self.mention_channels = payload.get("mention_channels")
        self.attachments = payload.get("attachments")
        self.embeds = payload.get("embeds")
        self.reactions = payload.get("reactions")
        self.nonce = payload.get("nonce")
        self.pinned = payload.get("pinned", False)
        self.webhook_id = payload.get("webhook_id")
        self.activity = payload.get("activity")
        self.application = payload.get("application")
        self.application_id = payload.get("application_id")
        self.message_reference = payload.get("message_reference")
        self.flags = payload.get("flags")
        self.referenced_message = payload.get("referenced_message")
        self.interaction = payload.get("interaction")
        self.thread = payload.get("thread")
        self.components = payload.get("components")
        self.sticker_items = payload.get("sticker_items")
        self.stickers = payload.get("stickers")
        self.position = payload.get("position")
    
    async def delete(self):
        """
        Deletes the message.
        """
        return await self.client.http.delete_message(self.channel_id, self.id)

    async def edit(
        self,
        content: Optional[str] = MISSING,
        *,
        embed: Optional[Embed] = MISSING,
        embeds: Optional[List[Embed]] = MISSING,
        view: Optional[View] = MISSING,
        tts: Optional[bool] = MISSING,
        file: Optional[Dict[str, Any]] = MISSING,
        files: Optional[List[Dict[str, Any]]] = MISSING,
        suppress_embeds: Optional[bool] = MISSING,
    ):
        """
        Edits the message.

        Parameters
        ----------
        content: Optional[str]
            The new content of the message.
        embed: Optional[Embed]
            The new embed of the message.
        embeds: Optional[List[Embed]]
            The new embeds of the message.
        view: Optional[View]
            The new view of the message.
        tts: Optional[bool]
            Whether the message should be sent with text-to-speech.
        file: Optional[File]
            A file to send with the message.
        files: Optional[List[File]]
            A list of files to send with the message.
        suppress_embeds: Optional[bool]
            Whether the embeds should be suppressed.
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
        if view:
            self.client.load_components(view)
        resp = await self.client.http.edit_channel_message(
            self.channel_id, 
            self.id, 
            create_form(data, merge_fields(file, files))
        )
        data = await resp.json()
        return Message(data, self.client)


class FollowupMessage(Message):
    """
    Represents a followup message sent by an interaction, subclassed from :class:`Message`.
    """
    def __init__(self, payload: dict, interaction: "Interaction") -> None:
        super().__init__(payload, interaction.client)
        self.interaction = interaction

    async def delete(self):
        """
        Deletes the followup message.
        """
        return await self.interaction.client.http.delete_webhook_message(
            self.interaction.application_id,
            self.interaction.token,
            self.id
        )

    async def edit(
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
    ) -> Message:
        """
        Edits the followup message.

        Parameters
        ----------
        same as :meth:`Message.edit`
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
            self.interaction.client.load_components(view)
        self.interaction.client.store_inter_token(self.interaction.id, self.interaction.token)
        resp = await self.client.http.edit_webhook_message(
            self.interaction.application_id,
            self.interaction.token,
            self.id,
            create_form(data, merge_fields(file, files))
        )
        data = await resp.json()
        return Message(data, self.interaction.client)


class ResponseMessage(Message):
    """
    Represents a response message sent by an interaction, subclassed from :class:`Message`.
    """
    def __init__(self, payload: dict, interaction: "Interaction") -> None:
        super().__init__(payload, interaction.client)
        self.interaction = interaction

    async def delete(self):
        """
        Deletes the response message.
        """
        return self.client.http.delete_webhook_message(
            self.interaction.application_id,
            self.interaction.token,
            "@original"
        )

    async def edit(
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
    ) -> Message:
        """
        Edits the response message.

        Parameters
        ----------
        same as :meth:`Message.edit`
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
            self.client.load_components(view)
        self.client.store_inter_token(self.interaction.id, self.interaction.token)
        resp = self.client.http.edit_webhook_message(
            self.interaction.application_id,
            self.interaction.token,
            "@original",
            create_form(data, merge_fields(file, files))
        )
        data = await resp.json()
        return Message(data, self.client)
