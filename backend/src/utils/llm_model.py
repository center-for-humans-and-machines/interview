from typing import List

import requests
import tiktoken
from fastapi import HTTPException
# Note: The openai-python library support for Azure OpenAI is in preview.
from openai import AsyncAzureOpenAI, AsyncOpenAI, OpenAI
from src.models.message import MessageDocument, OpenAIMessage
from src.models.settings import get_settings
from src.utils.configs import models
from src.utils.db import create_message
from src.utils.logging import setup_logger
from tenacity import (RetryError, retry, stop_after_attempt,
                      wait_random_exponential)

logger = setup_logger(__name__)

encoding = tiktoken.get_encoding("cl100k_base")


settings = get_settings()

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(5))
async def completion_with_backoff(client, **kwargs):
    logger.info("here in completion_with_backoff")
    # return await client.chat.completions.create(**kwargs)
    try:
        if (kwargs['model']=="deepseek-ai/DeepSeek-R1"):
            return client.chat.completions.create(**kwargs)

        else:
            return await client.chat.completions.create(**kwargs)

    except Exception as e:
        logger.error("Error occurred in completion_with_backoff: %s", str(e))
        raise  # Re-raise exception after logging it

def init_model_endpoint(model: str) -> AsyncOpenAI | AsyncAzureOpenAI:
    """
    Initialize the model endpoint based on the provided model name.

    This function sets up a global client to interact with either GWDG or OpenAI (including Azure OpenAI)
    based on the specified model. The client is initialized differently depending on the model's source:

    - If the model is found in the "gwdg" list, it uses the GWDG API key and base URL.
    - If the model is found in the "open_ai" list, it checks the base URL to determine if Azure OpenAI should be used.
    - If the base URL contains the substring "azure", it initializes an `AsyncAzureOpenAI` client.
    - Otherwise, it defaults to an `AsyncOpenAI` client.

    Args:
        model (str): The name of the model to initialize.

    Raises:
        KeyError: If the model is not found in either "gwdg" or "open_ai" model lists.

    Returns:
        AsyncOpenAI | AsyncAzureOpenAI: The initialized client for the specified model.
    """
    # Guard clause: Initialize client if the model is in the GWDG list
    if model in models["gwdg"]:
        logger.debug(f"Model {model} found in GWDG models... Loading endpoint.")
        client = AsyncOpenAI(
            api_key=settings.gwdg_api_key, base_url=settings.gwdg_base_url
        )
        return client

    # Guard clause: Initialize client if the model is in the OpenAI list and check for Azure usage
    if model in models["open_ai"]:
        logger.debug(f"Model {model} found in OpenAI models... Loading endpoint.")

        # Check if the OpenAI base URL contains "azure"
        if settings.open_ai_backend.lower() == "azure":
            logger.debug(
                "Azure-specific base URL detected... Using AsyncAzureOpenAI client."
            )
            client = AsyncAzureOpenAI(
                api_key=settings.open_ai_api_key,
                azure_endpoint=settings.open_ai_base_url,
                api_version="2024-02-01",
            )
        elif settings.open_ai_backend.lower() == "openai":
            logger.debug(
                "Standard OpenAI base URL detected... Using AsyncOpenAI client."
            )
            client = AsyncOpenAI(api_key=settings.open_ai_api_key)
        return client

    if model in models["deepseek"]:
        client = OpenAI(api_key=settings.deepseek_key, base_url=settings.deepseek_url)
        return client


    # If the model is not recognized, raise an error
    logger.error(f"Model {model} not found in either GWDG or OpenAI or DeepSeek models.")
    raise KeyError(f"Model {model} is not recognized in available models.")

# this function has been moved from open_ai.py to here because send_message could not be called in other modules.
async def call_model(
    sio_server,
    sid,
    messages: List[OpenAIMessage],
    model: str,
    client: AsyncOpenAI | AsyncAzureOpenAI,
    session_id: str,
    experiment_id: str,
    participant_id: str = None,
) -> OpenAIMessage:

    request_token_count, images_volume_total = calculate_limits(messages)

    if request_token_count > token_count_limit:
        raise TokenError(
            f"Token limit of {request_token_count} for participant {participant_id} exceeded , total token count is {request_token_count}",
            request_token_count,
        )

    if images_volume_total > image_volume_limit:
        raise TokenError(
            f"Image volume limit of {images_volume_total} for participant {participant_id} exceeded , total token count is {images_volume_total}",
            images_volume_total,
        )

    try:
        response = await completion_with_backoff(
            client,
            model=model,
            messages=messages,
            temperature=0.7,
            stream=True,
        )

        full_response = ""
        newMessage = True

        if model == "deepseek-ai/DeepSeek-R1":
            # deepseek with together.ai is not working with "async for" loop
            for chunk in response:
                text_to_send_in_the_current_chunk = ""
                if len(chunk.choices)>0:

                    full_response += chunk.choices[0].delta.content or ""
                    text_to_send_in_the_current_chunk = chunk.choices[0].delta.content or ""

                    if newMessage == False:
                        response_data = {
                            "type": "stream",
                            "data": await create_message(
                                content= text_to_send_in_the_current_chunk or "",
                                role= "assistant",
                            )
                        }

                    else:
                        response_data = {
                            "type": "message",
                            "data": await create_message(
                                content= text_to_send_in_the_current_chunk or "",
                                role= "assistant",
                            )
                        }
                        newMessage=False

                    await sio_server.emit("message_to_client", response_data, sid)
        else:
            async for chunk in response:
                text_to_send_in_the_current_chunk = ""
                if len(chunk.choices)>0:

                    full_response += chunk.choices[0].delta.content or ""
                    text_to_send_in_the_current_chunk = chunk.choices[0].delta.content or ""

                    if newMessage == False:
                        response_data = {
                            "type": "stream",
                            "data": await create_message(
                                content= text_to_send_in_the_current_chunk or "",
                                role= "assistant",
                            )
                        }

                    else:
                        response_data = {
                            "type": "message",
                            "data": await create_message(
                                content= text_to_send_in_the_current_chunk or "",
                                role= "assistant",
                            )
                        }
                        newMessage=False

                    await sio_server.emit("message_to_client", response_data, sid)


        logger.info(f"full_response : {full_response}")

        response_token_count = num_tokens_from_string(full_response)
        total_token_count = request_token_count + response_token_count

        if total_token_count > token_count_limit:
            raise TokenError(
                f"Token limit of {token_count_limit} for participant {participant_id} exceeded , total token count is {total_token_count}",
                total_token_count,
            )

        logger.debug(
            total_token_count, title=f"participant {participant_id} Total Token Count"
        )

        return full_response


    except Exception as e:
        response_data = {
            "type": "message",
            "data": await create_message(
                content=f"An error was occrued for client.chat.completions.create for participant_id {participant_id} : {e}",
                role= "assistant",
            )
        }
        await sio_server.emit("message_to_client", response_data, sid)

        return "ExceptionError" # to make sure the flow of the program is not disrupted. this record will not be saved.


token_count_limit = 8000
image_volume_limit = 2000 * 1024 # the unit is byte (KB * 1024)

def calculate_limits(messages):
    request_token_count = 0
    images_volume_total = 0

    for message in messages:
        if isinstance(message['content'], list):
            for elem in message['content']:
                if elem['type'] == 'text':
                    request_token_count += num_tokens_from_string(elem["text"])

                if elem['type'] == 'image_url':
                    response = requests.get(elem['image_url']['url'])
                    if response.status_code == 200:
                        images_volume_total += len(response.content)
        else:
            request_token_count += num_tokens_from_string(message["content"])

    return request_token_count, images_volume_total

def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


class TokenError(Exception):
    def __init__(self, message, token_count):
        super().__init__(message)
        self.token_count = token_count
