from __future__ import annotations
import asyncio
from fastapi import Request
from .interaction import Interaction
from .command import *
from functools import wraps
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from fastapi.responses import JSONResponse, Response
from typing import Optional, List, Dict, Any, Union, Callable
from .enums import callback_types, interaction_types, command_types, component_types
from .parser import build_prams


async def listener(request: Request):
    signature = request.headers.get("X-Signature-Ed25519")
    timestamp = request.headers.get("X-Signature-Timestamp")
    try:
        key = VerifyKey(bytes.fromhex(request.app.public_key))
        key.verify(str(timestamp).encode() + await request.body(), bytes.fromhex(str(signature)))
    except BadSignatureError:
        return Response(content='request validation failed', status_code=401)
    else:
        interaction = Interaction(**(await request.json()))
        if interaction.type == interaction_types.ping.value:
            return JSONResponse({'type': callback_types.pong.value}, status_code=200)
        elif interaction.type == interaction_types.app_command.value:
            command: ApplicationCommand = request.app.application_commands.get(interaction.app_command_data.id)
            if not command:
                return interaction.response(content='command not implemented!', ephemeral=True)
            else:
                args, kwargs = build_prams(interaction.app_command_data.options, command.callback)
                return await command.callback(interaction, *args, **kwargs)
        elif interaction.type == interaction_types.component.value:
            component_data = interaction.data
            custom_id = component_data.get('custom_id', '')
            component = request.app.ui_factory.get(custom_id, None)
            if custom_id and component:
                return await component._callback(interaction)
        else:
            return JSONResponse({'message': "unhandled interaction type"}, status_code=300)
