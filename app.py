import os
import gradio as gr
from io import BytesIO
import zipfile
import tempfile
import random  
import json
from gradio_client import Client, handle_file
import base64
from PIL import Image
from datetime import datetime
from io import BytesIO

BACKEND = os.getenv("BACKEND")
JS2 = os.getenv("JS2")
MAIN_HTML = os.getenv("MAIN_HTML")
MAIN_JS = os.getenv("MAIN_JS")
HEAD_HTML = os.getenv("HEAD_HTML")
CSS = os.getenv("CSS")

STATUS_MESSAGES = {
    301: "Invalid Premium ID!"
}

backend = Client(BACKEND)

def base64_to_image(base64_str):
    if ";base64," in base64_str:
        base64_str = base64_str.split(";base64,")[1].strip()
    return base64.b64decode(base64_str + '=' * (-len(base64_str) % 4))

user_attempts = {}
def clear_old_entries():
    today = datetime.now().date()
    # Create a list of keys to remove
    keys_to_remove = [key for key, value in user_attempts.items() if value != today]
    # Remove old entries
    for key in keys_to_remove:
        del user_attempts[key]

def if_limited(request):
    clear_old_entries()
    user_ip = None
    if request.headers.get("x-forwarded-for"):
        user_ip = request.headers["x-forwarded-for"].split(",")[0]  # First IP in the list

    cookie_value = request.headers.get("cookie", "")
    if "user_id=" in cookie_value:
        user_id = cookie_value.split("user_id=")[1].split(";")[0]
    else:
        user_id = None
    print("##### Coming", user_id, user_ip)
    # Get today's date
    today = datetime.now().date()

    # Check if the user has already tried today (by IP or cookie)
    for key, value in user_attempts.items():
        if (key == user_ip or key == user_id) and value == today:
            return True

    # Record the attempt (store both hashed IP and hashed cookie)
    if user_ip:
        user_attempts[user_ip] = today
    if user_id:
        user_attempts[user_id] = today
    return False

def base64_to_image(base64_str):
    if ";base64," in base64_str:
        base64_str = base64_str.split(";base64,")[1].strip()
    image_data = base64.b64decode(base64_str + '=' * (-len(base64_str) % 4))
    image = Image.open(BytesIO(image_data)).convert('RGB')
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)
    return buffer.read()

def search_image(base64_image, token_txt, request: gr.Request):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
        try:
            temp_file.write(base64_to_image(base64_image))
            file = temp_file.name
            file1 = handle_file(file)
        except Exception as e:
            print(e)
            gr.Info("Please upload an image file.")
            return []

        if token_txt == "" and if_limited(request):
            gr.Info("⏳ Wait for your next free search, or 🚀 Go Premium Search at https://faceseek.online!", duration=10)
            return []

        if token_txt == "KSB311":
            token_txt = ""

        result_text = backend.predict(
                file=file1,
                token=token_txt, 
                api_name="/search_face"
        )

        result = json.loads(result_text)
        outarray = []
        if result['status'] > 300:
            gr.Info(STATUS_MESSAGES[result['status']], duration=10)
            return '{"result": []}'
    return result_text

with gr.Blocks(css=CSS, head=HEAD_HTML, title="FaceSeek - Face Search Online") as iface:
    html = gr.HTML(MAIN_HTML, max_height=720)
    base64_txt = gr.Textbox(label="Base64-Image", elem_id="base64_image", visible=False)
    token_txt = gr.Textbox(label="Token-Text", elem_id="premium_token", visible=False)
    out_txt = gr.Textbox(label="Result", visible=False)

    search_button = gr.Button("🔍 Free Face Search", elem_id="search_btn", visible=False)

    search_button.click(search_image, inputs=[base64_txt, token_txt], outputs=out_txt).success(None, inputs=[out_txt], js=JS2)
    iface.load(None, inputs=None, outputs=html, js=MAIN_JS)

# Launch the interface
iface.launch()