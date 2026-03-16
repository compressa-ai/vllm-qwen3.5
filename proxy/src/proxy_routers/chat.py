"""
This module is responsible for proxying chat completions to the appropriate pod.
It also handles streaming responses.
Streaming in OpenAI lib - https://github.com/openai/openai-python/blob/main/src/openai/_streaming.py
OpenAI docs reference: https://platform.openai.com/docs/api-reference/chat/create
"""

from ast import Yield
from typing import List, Optional
from pydantic import BaseModel, Field
import httpx
from fastapi.exceptions import HTTPException
from fastapi import (
    APIRouter,
    Request,
    Body,
    Response,
    Header
)
from fastapi.responses import StreamingResponse
from tools import app_logger, split_sse_chunks
import os
import traceback

router = APIRouter(
    prefix="/chat/completions"
)

class ChatCompletion(BaseModel):
    model: str
    messages: List[dict]
    tools: Optional[List[dict]] = None
    tool_choice: Optional[str] = None  # e.g. "auto", "none"
    stream: bool = False
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    extra_body: Optional[dict] = None  # e.g. chat_template_kwargs for vLLM


@router.post("")
@router.post("/")
async def proxy_chat_completions(request: Request, authorization: Optional[str] = Header(None),
    accept: Optional[str] = Header(None), payload: ChatCompletion = Body(None)):
    try:
        payload = payload.model_dump(exclude_none=True)
    except Exception as e:
        app_logger.error(f"Incorrect payload: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    extra = payload.pop("extra_body", None)
    if extra:
        payload.update(extra)

    logit_bias = request.app.state.logit_bias
    if logit_bias:
        payload["logit_bias"] = logit_bias
    pod_address = request.app.state.node_address
    payload["model"] = f"{os.getenv("CONTAINER_RESOURCES_PATH", "/app/resources")}/models/models/{payload["model"].replace("/", "_")}"
    pod_url = f"{pod_address}/v1/chat/completions"
    headers = {
        "Authorization": authorization,
        "accept": accept,
        "Content-Type": "application/json"
    }
    is_streaming = payload.get("stream", False)
    
    if is_streaming:
        payload["stream_options"] = {"include_usage": True}
        async def stream_generator():
            current_chunk = None
            try:
                async with httpx.AsyncClient(timeout=request.app.state.proxy_timeout) as client:
                    async with client.stream("POST", pod_url, json=payload, headers=headers) as response:
                        if response.status_code != 200:
                            error_content = await response.aread()
                            app_logger.error(f"Error proxying streaming chat completions: {error_content}")
                            raise HTTPException(status_code=response.status_code, detail=error_content.decode())
                        buffer = ""
                        async for chunk in response.aiter_lines():
                            if not chunk:
                                continue
                            chunk = chunk.rstrip("\r\n")
                            current_chunk = chunk
                            buffer += chunk
                            parts, buffer = split_sse_chunks(buffer)
                            for part in parts:
                                yield f"data: {part}\n\n".encode("utf-8")
                        if buffer.strip():
                            yield f"data: {buffer}\n\n".encode("utf-8")
                        yield b"data: [DONE]\n\n"
            except HTTPException:
                raise
            except Exception as e:
                app_logger.error(f"Error proxying streaming chat completions: {e}")
                if current_chunk is not None:
                    try:
                        chunk_str = current_chunk if isinstance(current_chunk, str) else current_chunk.decode("utf-8", errors="replace")
                        app_logger.error(f"Last chunk (utf-8 decoded): {chunk_str}")
                    except Exception as decode_exc:
                        app_logger.error(f"Failed to decode last chunk: {decode_exc}")
                app_logger.error(traceback.format_exc())
                raise

        response_headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }

        return StreamingResponse(
            stream_generator(),
            status_code=200,
            media_type="text/event-stream",
            headers=response_headers
        )
    else:
        async with httpx.AsyncClient(timeout=request.app.state.proxy_timeout) as client:
            try:
                proxied_response = await client.post(pod_url, json=payload, headers=headers)
                if proxied_response.status_code != 200:
                    app_logger.error(f"vLLM returned {proxied_response.status_code}: {proxied_response.text}")
                return Response(
                    content=proxied_response.content,
                    status_code=proxied_response.status_code,
                    media_type=proxied_response.headers.get("content-type"),
                )
            except Exception as e:
                app_logger.error(f"Error proxying chat completions: {e}")
                raise HTTPException(status_code=500, detail=str(e))

                
                    