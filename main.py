import os
import requests
from fastapi import FastAPI, Request
import google.generativeai as genai

app = FastAPI()

# Lấy biến môi trường (cấu hình bảo mật)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GEMINI_KEY = os.environ.get("GEMINI_KEY")

# Cấu hình Gemini AI
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def analyze_with_gemini(data: dict) -> str:
    """Gửi dữ liệu đa khung thời gian sang Gemini phân tích"""
    prompt = f"""
    Bạn là chuyên gia phân tích kỹ thuật theo phương pháp Wyckoff và SMC.
    Hãy phân tích tín hiệu giao dịch từ TradingView dưới đây:

    - Cặp tiền: {data.get('ticker')}
    - Tín hiệu tại khung: {data.get('signal_tf')} ({data.get('action')} tại giá {data.get('price')})
    - Xu hướng H1: {data.get('h1_trend')}
    - Xu hướng H4: {data.get('h4_trend')}
    - Xu hướng D1: {data.get('d1_trend')}
    - Volume tại M5: {data.get('volume_status')}

    Yêu cầu:
    1. Lệnh này có đồng thuận với xu hướng lớn (H1/H4) không?
    2. Cấu trúc Wyckoff hiện tại có rủi ro gì (bẫy giá Bull/Bear Trap) không?
    3. Đưa ra lời khuyên NÊN hay KHÔNG NÊN vào lệnh kèm mức Stop Loss tham khảo.
    Viết ngắn gọn, súc tích dưới 150 từ.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Không thể lấy phân tích từ Gemini: {str(e)}"

def send_telegram(text: str):
    """Gửi tin nhắn về Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    
    # 1. Gọi Gemini phân tích
    ai_analysis = analyze_with_gemini(data)
    
    # 2. Soạn nội dung tin nhắn gửi về Telegram
    msg = (
        f"🚨 **TÍN HIỆU TRADINGVIEW MỚI** 🚨\n\n"
        f"• **Mã:** {data.get('ticker')}\n"
        f"• **Hành động:** {data.get('action')}\n"
        f"• **Giá:** {data.get('price')}\n"
        f"• **Khung phát tín hiệu:** {data.get('signal_tf')}\n\n"
        f"🤖 **ĐÁNH GIÁ TỪ GEMINI AI:**\n"
        f"{ai_analysis}"
    )
    
    send_telegram(msg)
    return {"status": "success"}

@app.get("/")
def home():
    return {"status": "Bot Server is running!"}
