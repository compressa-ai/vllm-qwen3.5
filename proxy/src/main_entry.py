from fastapi import FastAPI, APIRouter
import httpx
import re
import os
import argparse
import uvicorn
from tools import app_logger
from proxy_routers import models, chat, completions
from logit_bias import prepare_logit_bias, get_tokenizer

app = FastAPI()
app.state.proxy_timeout = httpx.Timeout(timeout=None, connect=10.0)
app.state.logit_bias = None

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(models.router)
v1_router.include_router(chat.router)
v1_router.include_router(completions.router)
app.include_router(v1_router)


@app.on_event("startup")
async def startup_event():
    try:
        model_pth = [dir for dir in os.listdir("/app/resources/models/models/") if re.sub(r"[^a-zA-Z0-9.]", "", dir) == re.sub(r"[^a-zA-Z0-9.]", "", os.getenv("MODEL_NAME"))][0]
        app.state.logit_bias = prepare_logit_bias(get_tokenizer("/app/resources/models/models/" + model_pth))
        if not app.state.logit_bias:
            app_logger.warning(f"Logit bias was not prepared")
    except Exception as e:
        app_logger.warning(f"Logit bias was not loaded: {e}")
    app.state.node_address = f"http://{os.getenv('LLM_HOST', 'qwen3-5')}:{os.getenv('LLM_PORT', 8000)}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default=os.getenv("DISPATCHER_PORT", 8001), type=int, dest="port")
    parser.add_argument("--host", default="0.0.0.0", type=str, dest="host")
    args = vars(parser.parse_args())

    uvicorn.run(app, **args)

