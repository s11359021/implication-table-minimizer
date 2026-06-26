import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

# 載入 .env 檔案中的環境變數
load_dotenv()

app = Flask(__name__)
# 允許所有來源的前端請求 (開發測試用)
CORS(app) 

# 設定 Gemini API Key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@app.route('/scan', methods=['POST'])
def scan_image():
    # 檢查前端是否有傳送檔案過來
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    try:
        # 將傳來的檔案轉為 PIL Image 格式
        image = Image.open(file.stream)

        # 改為更高級的推導型 Prompt
        prompt = """
        Analyze this Finite State Machine (FSM) transition table image.
        Perform 2 tasks:
        1. Deduce if it is a 'mealy' or 'moore' machine. (Mealy has different outputs for X=0 and X=1; Moore has a single output per state).
        2. Extract all rows of transitions.

        Return ONLY a raw JSON object matching exactly this schema:
        {
          "detected_type": "mealy",
          "transitions": [
            {"state": "a", "next0": "b", "next1": "c", "out0": "0", "out1": "1"}
          ]
        }
        Notice: If it is a 'moore' machine, set 'detected_type' to "moore", and make 'out0' and 'out1' hold the exact same output value.
        Do NOT wrap the response in ```json markdown blocks.
        """
        
        # 呼叫 Gemini 1.5 Flash (速度最快，適合 OCR)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content([prompt, image])
        
        # 清理回傳字串 (避免 AI 偶爾還是包裝了 Markdown)
        text = response.text.strip()
        if text.startswith('```json'):
            text = text[7:-3].strip()
        elif text.startswith('```'):
            text = text[3:-3].strip()
            
        # 將字串解析為 JSON 物件並回傳給前端
        data = json.loads(text)
        return jsonify(data), 200

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Render 會自動給予一個 PORT 環境變數，如果沒有，我們預設使用 5000
    port = int(os.environ.get("PORT", 5000))
    # host 必須設定為 "0.0.0.0" 才能接收來自外部的連線
    app.run(host="0.0.0.0", port=port)