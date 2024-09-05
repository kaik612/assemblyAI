from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import time
import os

app = Flask(__name__)

# Mở CORS cho tất cả các domain
CORS(app)

# API key từ AssemblyAI
API_KEY = '1eede8749d6b4a8e94af2b9f16a2e5ef'
upload_endpoint = 'https://api.assemblyai.com/v2/upload'
transcript_endpoint = 'https://api.assemblyai.com/v2/transcript'

# Đường dẫn để lưu file upload tạm thời
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Tạo thư mục upload nếu chưa tồn tại
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Hàm tải file âm thanh lên AssemblyAI
def upload_file_to_assemblyai(file_path):
    headers = {'authorization': API_KEY}
    with open(file_path, 'rb') as f:
        response = requests.post(upload_endpoint, headers=headers, files={'file': f})
    return response.json().get('upload_url')


# Hàm gửi yêu cầu phiên âm đến AssemblyAI
def request_transcription(audio_url):
    headers = {
        'authorization': API_KEY,
        'content-type': 'application/json'
    }
    data = {
        'audio_url': audio_url,
        'language_code': 'ja'  # Mã ngôn ngữ cho tiếng Nhật
    }
    response = requests.post(transcript_endpoint, headers=headers, json=data)
    return response.json().get('id')


# Hàm lấy kết quả phiên âm từ AssemblyAI
def get_transcription_result(transcription_id):
    headers = {'authorization': API_KEY}
    url = f'{transcript_endpoint}/{transcription_id}'

    while True:
        response = requests.get(url, headers=headers)
        result = response.json()

        if result['status'] == 'completed':
            return result['text']
        elif result['status'] == 'failed':
            return 'Transcription failed'

        time.sleep(5)  # Đợi 5 giây trước khi kiểm tra lại


# Route để upload file âm thanh và trả về kết quả phiên âm
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    try:
        # Bước 1: Tải file lên AssemblyAI
        audio_url = upload_file_to_assemblyai(file_path)

        # Bước 2: Yêu cầu phiên âm
        transcription_id = request_transcription(audio_url)

        # Bước 3: Lấy kết quả phiên âm
        transcription_text = get_transcription_result(transcription_id)

        # Xóa file đã upload sau khi xử lý xong
        os.remove(file_path)

        return jsonify({'transcript': transcription_text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    return "CORS is now enabled for all domains!"

@app.route('/')
def index():
    return render_template('index.html')

# Chạy server Flask
if __name__ == '__main__':
    app.run(debug=True)
