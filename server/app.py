from flask import Flask, request, jsonify
from PIL import Image
import io
import os
import time
from datetime import datetime

app = Flask(__name__)

# 创建上传文件夹
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        # 获取上传的图片
        if 'image' not in request.files:
            return jsonify({'error': '没有上传图片'}), 400
        
        image_file = request.files['image']
        text = request.form.get('text', '')
        
        # 保存图片
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        image_path = os.path.join(UPLOAD_FOLDER, f'image_{timestamp}.jpg')
        image_file.save(image_path)
        
        # TODO: 在这里添加您的图像处理和文本处理逻辑
        # 这里只是一个示例响应
        response_text = f"收到您的图片和文字：{text}"
        
        # 清理临时文件
        try:
            os.remove(image_path)
        except:
            pass
        
        return jsonify({
            'text': response_text,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 