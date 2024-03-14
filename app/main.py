import logging
import os
import requests
import time
import uuid
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HF_API_URL = os.environ.get("HF_API_URL")
HF_MODEL_NAME = os.environ.get("HF_MODEL_NAME")
HF_TOKEN = os.environ.get("HF_TOKEN")
headers = {"Authorization": f"Bearer {HF_TOKEN}"}
HF_MODEL_PATH = os.path.join(HF_API_URL, HF_MODEL_NAME)


def query_hf_api(payload, retries=10, delay=1):
    for attempt in range(retries):
        response = requests.post(HF_MODEL_PATH, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()[0]
            generated_text = data.get("generated_text", "")
            response_index = generated_text.find("### Response:")
            if response_index != -1:
                parsed_response = generated_text[
                    response_index + len("### Response:") :
                ].strip()
                return parsed_response
            else:
                logger.error("No '### Response:' marker found in the response.")
                return None
        elif response.status_code == 503:
            logger.warning(
                "Attempt %s: Model is loading, retrying after %s seconds",
                attempt + 1,
                delay,
            )
            time.sleep(delay)
            delay *= 2
        else:
            logger.error("HTTP Error %s: %s", response.status_code, response.json())
            return None
    logger.error("Request timed out. Failed to load the model in time.")
    return None


def construct_prompt_with_responses(instructions_responses):
    base_prompt = """You are an intelligent code snippet generator. 
    Below is an instruction that describes a task. 
    Write a response that appropriately completes the request.\n\n
    ### Instruction"""
    for i, (instruction, response) in enumerate(instructions_responses, start=1):
        base_prompt += (
            f"{i}:\n{instruction}\n\n Show only the code.### Response:\n{response}\n\n"
        )
    return base_prompt


snippets = {}

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def get_snippets(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "snippets": snippets}
    )


@app.post("/snippet/")
async def add_snippet(description: str = Form(...)):
    snippet_id = str(uuid.uuid4())
    prompt = construct_prompt_with_responses([(description, "")])
    logger.info("Sending prompt %s", prompt)
    payload = {"inputs": prompt, "parameters": {"max_length": 100}}
    result = query_hf_api(payload=payload, retries=10, delay=1)
    if result is None:
        snippets[snippet_id] = {"description": description, "api_response": "NA"}
        raise HTTPException(
            status_code=500,
            detail="Failed to get a successful response from the huggingface api.",
        )
    else:
        snippets[snippet_id] = {"description": description, "api_response": result}
    return RedirectResponse(url="/", status_code=303)


@app.get("/delete-snippet/{snippet_id}")
async def delete_snippet(snippet_id: str):
    if snippet_id in snippets:
        del snippets[snippet_id]
    return RedirectResponse(url="/", status_code=303)


@app.post("/feedback/{snippet_id}")
async def add_feedback(snippet_id: str, feedback: str = Form(...)):
    if snippet_id not in snippets:
        raise HTTPException(status_code=404, detail="Snippet not found")

    snippet_info = snippets[snippet_id]
    description = snippet_info["description"]
    prompt = construct_prompt_with_responses(
        [
            (
                f"This is my previous query '{description}' make the following adjustments: {feedback}",
                "",
            )
        ]
    )
    logger.info("GENERATING FEEDBACK: %s", prompt)
    payload = {"inputs": prompt, "parameters": {"max_length": 100}}
    result = query_hf_api(payload=payload, retries=10, delay=1)
    if result is None:
        snippets[snippet_id] = {"description": description, "api_response": "NA"}
        raise HTTPException(
            status_code=500,
            detail="Failed to get a successful response from the huggingface api.",
        )
    else:
        snippets[snippet_id] = {
            "description": f"Initial Query: {description} | Feedback: {feedback}",
            "api_response": result,
        }

    return RedirectResponse(url="/", status_code=303)
