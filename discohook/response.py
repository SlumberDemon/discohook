from typing import TYPE_CHECKING, Optional, List, Union, Any, Dict

from .embed import Embed
from .errors import InteractionTypeMismatch
from .enums import InteractionCallbackType, InteractionType
from .file import File
from .multipart import create_form
from .message import Message
from .modal import Modal
from .option import Choice
from .params import MISSING, handle_edit_params, handle_send_params, merge_fields
from .view import View

if TYPE_CHECKING:
    from .interaction import Interaction


class InteractionResponse:
    """
    Represents a response message sent by an interaction
    """

    def __init__(self, interaction: "Interaction") -> None:
        self.inter = interaction

    async def delete(self):
        """
        Deletes the response message.
        """
        await self.inter.client.http.delete_webhook_message(
            self.inter.application_id, self.inter.token, "@original"
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
        if view and view is not MISSING:
            self.inter.client.load_components(view)
        self.inter.client.store_inter_token(self.inter.id, self.inter.token)
        resp = await self.inter.client.http.edit_webhook_message(
            self.inter.application_id,
            self.inter.token,
            "@original",
            create_form(data, merge_fields(file, files)),
        )
        data = await resp.json()
        return Message(self.inter.client, data)


class FollowupResponse:
    """
    Represents a followup message sent by an interaction, subclassed from :class:`Message`.
    """

    def __init__(self, payload: Dict[str, Any], interaction: "Interaction") -> None:
        self.message = Message(interaction.client, payload)
        self.interaction = interaction

    async def delete(self):
        """
        Deletes the followup message.
        """
        return await self.interaction.client.http.delete_webhook_message(
            self.interaction.application_id,
            self.interaction.token,
            self.message.id,
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
        if view and view is not MISSING:
            self.interaction.client.load_components(view)
        self.interaction.client.store_inter_token(self.interaction.id, self.interaction.token)
        resp = await self.interaction.client.http.edit_webhook_message(
            self.interaction.application_id,
            self.interaction.token,
            self.message.id,
            create_form(data, merge_fields(file, files)),
        )
        data = await resp.json()
        return Message(self.interaction.client, data)


class ResponseAdapter:
    """
    Represents a response message sent by an interaction
    """

    def __init__(self, interaction: "Interaction") -> None:
        self.inter = interaction

    async def send(
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
            self.inter.client.store_inter_token(self.inter.id, self.inter.token)
            self.inter.client.load_components(view)

        payload = {
            "data": data,
            "type": InteractionCallbackType.channel_message_with_source.value,
        }
        await self.inter.client.http.send_interaction_mp_callback(
            self.inter.id, self.inter.token, create_form(payload, merge_fields(file, files))
        )
        self.inter._responded = True
        return InteractionResponse(self.inter)

    async def send_modal(self, modal: Union[Modal, Any]):
        """
        Sends a modal to the interaction

        Parameters
        ----------
        modal: Modal
            The modal to send
        """
        if self.inter.type not in (InteractionType.component, InteractionType.app_command):
            raise InteractionTypeMismatch(f"Method not supported for {self.inter.type}")
        self.inter.client.active_components[modal.custom_id] = modal
        payload = {
            "data": modal.to_dict(),
            "type": InteractionCallbackType.modal.value,
        }
        await self.inter.client.http.send_interaction_callback(self.inter.id, self.inter.token, payload)

    async def autocomplete(self, choices: List[Choice]):
        """
        Sends autocomplete choices to the interaction (max 25)

        Parameters
        ----------
        choices: List[Choice]
            The choices to send
        """
        if self.inter.type != InteractionType.autocomplete:
            raise InteractionTypeMismatch(f"Method not supported for {self.inter.type}")
        choices = choices[:25]
        payload = {
            "type": InteractionCallbackType.autocomplete.value,
            "data": {"choices": [choice.to_dict() for choice in choices]},
        }
        await self.inter.client.http.send_interaction_callback(self.inter.id, self.inter.token, payload)

    async def defer(self, ephemeral: bool = False) -> InteractionResponse:
        """
        Defers the interaction

        Parameters
        ----------
        ephemeral: bool
            Whether the successive responses should be ephemeral or not (only for Application Commands)
        """
        payload = {}
        if self.inter.type == InteractionType.component:
            payload["type"] = InteractionCallbackType.deferred_update_component_message.value
        elif self.inter.type == InteractionType.app_command or self.inter.type == InteractionType.modal_submit:
            payload["type"] = InteractionCallbackType.deferred_channel_message_with_source.value
            if ephemeral:
                payload["data"] = {"flags": 64}
        else:
            raise InteractionTypeMismatch(f"Method not supported for {self.inter.type}")

        await self.inter.client.http.send_interaction_callback(self.inter.id, self.inter.token, payload)
        self.inter._responded = True
        return InteractionResponse(self.inter)

    async def update_message(
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
    ) -> None:
        """
        Edits the message, the component was attached to

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
        if self.inter.type in (InteractionType.autocomplete, InteractionType.app_command):
            raise InteractionTypeMismatch(f"Method not supported for {self.inter.type}")

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
        if view and view is not MISSING:
            self.inter.client.load_components(view)
        self.inter.client.store_inter_token(self.inter.id, self.inter.token)
        payload = {"type": InteractionCallbackType.update_component_message.value, "data": data}
        await self.inter.client.http.send_interaction_mp_callback(
            self.inter.id, self.inter.token, create_form(payload, merge_fields(file, files))
        )

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
        Sends a follow-up message to a deferred interaction

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
        payload = handle_send_params(
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
            self.inter.client.store_inter_token(self.inter.id, self.inter.token)
            self.inter.client.load_components(view)
        resp = await self.inter.client.http.send_webhook_message(
            self.inter.application_id, self.inter.token, create_form(payload, merge_fields(file, files))
        )
        data = await resp.json()
        return FollowupResponse(data, self.inter)