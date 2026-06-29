import os
import json
import base64
from flask import Flask, render_template, request, jsonify
from groq import Groq
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數 (這樣 Groq 才能自動抓到 GROQ_API_KEY)
load_dotenv()

app = Flask(__name__)

# 初始化 Groq Client
groq_client = Groq()

# ==========================================
# 1. 網頁首頁路由：當使用者輸入網址時，把前端畫面給他
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

# ==========================================
# 2. AI 掃描路由：負責接收圖片並呼叫 Groq Llama 3.2
# ==========================================
@app.route('/scan', methods=['POST'])
def scan_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
        
    file = request.files['image']
    
    try:
        # 將前端傳來的文件流讀取並轉換為 Base64 字串
        image_data = file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')

        # 定義要給 AI 的提示詞
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
        
        # 呼叫 Groq 上的 Llama 4 vision model
        # 原來的 Gemini model 太熱門了，常常 503
        completion = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.1, 
        )
        
        # 取得 AI 回傳的文字結果
        text = completion.choices[0].message.content.strip()

        # 清除可能殘留的 Markdown 區塊
        if text.startswith('```json'):
            text = text[7:-3].strip()
        elif text.startswith('```'):
            text = text[3:-3].strip()
            
        data = json.loads(text)
        return jsonify(data), 200

    except Exception as e:
        print("Backend Error:", e)
        return jsonify({"error": str(e)}), 500

# ==========================================
# 3. 啟動伺服器的開關 (修正 Render Port 綁定問題)
# ==========================================
if __name__ == '__main__':
    # 動態抓取 Render 分配的 PORT，如果是本地端開發則預設使用 5000
    port = int(os.environ.get('PORT', 5000))
    
    # 必須加上 host='0.0.0.0'，Render 才掃描得到
    app.run(host='0.0.0.0', port=port)