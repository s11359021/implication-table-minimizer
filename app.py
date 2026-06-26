import os
import json
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

# 載入 .env 檔案中的環境變數
load_dotenv()

app = Flask(__name__)
# 允許所有來源的前端請求
CORS(app) 

# 設定 Gemini API Key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --- 新增首頁路由 ---
@app.route('/')
def index():
    # 這會去 templates 資料夾找 index.html
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    try:
        image = Image.open(file.stream)

        # 修正：將模型改為 stable 的 gemini-1.5-flash
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = """
        Analyze this Finite State Machine (FSM) transition table image.
        Perform 2 tasks:
        1. Deduce if it is a 'mealy' or 'moore' machine.
        2. Extract all rows of transitions.

        Return ONLY a raw JSON object matching exactly this schema:
        {
          "detected_type": "mealy",
          "transitions": [
            {"state": "a", "next0": "b", "next1": "c", "out0": "0", "out1": "1"}
          ]
        }
        Do NOT wrap the response in ```json markdown blocks.
        """
        
        response = model.generate_content([prompt, image])
        
        text = response.text.strip()
        # 清理 Markdown
        if text.startswith('```json'):
            text = text[7:-3].strip()
        elif text.startswith('```'):
            text = text[3:-3].strip()
            
        data = json.loads(text)
        return jsonify(data), 200

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)