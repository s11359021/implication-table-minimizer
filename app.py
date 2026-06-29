import os
import json
# =============================================
# Block A: Import 載入套件與環境
# =============================================
from flask import Flask, request, jsonify, render_template  # [flask]
from flask_cors import CORS                                 # [flask-cors]
from dotenv import load_dotenv                              # [python-dotenv]
from google import genai                                    # [google-genai]
from PIL import Image                                       # [pillow]

# =============================================
# Block B: Initialization 系統初始化與安全性設定
# =============================================
# 1. 載入 .env 檔案中的環境變數
load_dotenv()

# 2. 初始化 Flask 應用並啟用跨來源讀取 (CORS)
app = Flask(__name__)
# 允許所有來源的前端請求
CORS(app) 

# 3. 初始化全新的 GenaI Client (SDK 自動抓取環境變數 Key)
client = genai.Client()
# =============================================
# Block C: Routes & Logic 後端路由與 AI 邏輯處理
# =============================================
# --- 新增首頁路由 ---
@app.route('/')
def index():
    # 當使用者以 GET 方法訪問根目錄時，return templates folder 中的 index.html
    return render_template('index.html')
# --- 影像解析 API 路由 ---
@app.route('/scan', methods=['POST'])
def scan_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400 # 400, Bad request
    
    file = request.files['image']
    try:
        # 將前端傳來的 file stream 轉換成 Pillow 影像物件 image
        image = Image.open(file.stream)
        
        # Prompt design: 要求 model 判斷 machine type and extract transition table
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
        
        # Use gemini-3.5-falsh model 並將 prompt & image 帶入 contents
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, image]
        )
        # get returned output 並去除頭尾空白
        text = response.text.strip()        
        # 清除可能殘留 Markdown
        if text.startswith('```json'):
            text = text[7:-3].strip()
        elif text.startswith('```'):
            text = text[3:-3].strip()
            
        # 將字串反序列化為 Py Dict.
        data = json.loads(text)
        # 將 Py Dict. 轉回 JSON format 的 HTTP 回應，並 mark state code 200 OK
        return jsonify(data), 200

    except Exception as e:
        # 擋下非預期錯誤
        print(f"Server Error: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================
# Block D: Execution server 啟動區
# =============================================
if __name__ == '__main__':
    # 從環境變數中取得 PORT，若無則預設 PORT 為 5000
    port = int(os.environ.get("PORT", 5000))
    # host = "0.0.0.0" 允許來自外部網路的連線，而不僅限於 localhost (127.0.0.1)
    app.run(host="0.0.0.0", port=port)