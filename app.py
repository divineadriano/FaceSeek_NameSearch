import os
import gradio as gr
import tempfile
from gradio_client import Client, handle_file
import base64

BACKEND = os.getenv("BACKEND")
JS2 = os.getenv("JS2")
MAIN_HTML = os.getenv("MAIN_HTML")
MAIN_JS = os.getenv("MAIN_JS")
HEAD_HTML = os.getenv("HEAD_HTML")
CSS = os.getenv("CSS")

backend = Client(BACKEND)

def base64_to_image(base64_str):
    if ";base64," in base64_str:
        base64_str = base64_str.split(";base64,")[1].strip()
    return base64.b64decode(base64_str + '=' * (-len(base64_str) % 4))

def search_image(base64_image):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            temp_file.write(base64_to_image(base64_image))
            file = temp_file.name
            handle_file(file)
    except Exception as e:
        print(e)
        gr.Info("Please upload an image file.")
        return []

    result_text = backend.predict(
            file=handle_file(file),
            token="", 
            api_name="/search_face"
    )
    os.remove(file)
    return result_text

with gr.Blocks(css=CSS, head=HEAD_HTML, title="DeepSeek? FaceSeek!") as iface:
    html = gr.HTML(MAIN_HTML, max_height=720)
    js_txt = gr.Textbox(label="Base64-Image", elem_id="base64_image", visible=False)
    out_txt = gr.Textbox(label="Result", visible=False)

    search_button = gr.Button("🔍 Free Face Search", elem_id="search_btn", visible=False)

    search_button.click(search_image, inputs=js_txt, outputs=out_txt).success(None, inputs=[out_txt], js=JS2)
    iface.load(None, inputs=None, outputs=html, js=MAIN_JS)

# Launch the interface
iface.launch()