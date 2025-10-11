from flask import Flask, request, jsonify, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from flask import render_template
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))
CORS(app)

# MongoDB 設定(請自行替換為實際連線字串)
mongo_uri = os.environ.get("MONGO_URI")
if not mongo_uri:
    raise ValueError("請先設定環境變數 MONGO_URI")
app.config["MONGO_URI"] = mongo_uri
mongo = PyMongo(app)
# 確認 mongo 正確初始化
if not mongo or not hasattr(mongo, 'db'):
    raise RuntimeError("MongoDB 連線初始化失敗")

users_coll = mongo.db.users

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')
    
# 註冊 API
@app.route('/api/register', methods=['POST'])
def register():
    # 用 request.form 接表單資料
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    if not username or not email or not password:
        return "缺少必填欄位", 400  # 表單提交，直接回文字即可

    if users_coll.find_one({'username': username}):
        return "使用者名稱已存在", 400

    hashed_pw = generate_password_hash(password)
    users_coll.insert_one({
        'username': username,
        'email': email,
        'password': hashed_pw
    })
    
    return redirect('/login')  # 註冊成功後跳轉到登入頁


# 登入 API
@app.route('/api/login', methods=['POST'])
def login():
    # 用 request.form 接表單資料
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return "缺少帳號或密碼", 400  # 這裡可以直接回文字，表單提交會跳頁

    user = users_coll.find_one({'username': username})
    if user and check_password_hash(user['password'], password):
        session['user_id'] = str(user['_id'])
        session['username'] = user['username']
        return redirect('/')  # 登入成功後跳回首頁
    else:
        return "帳號或密碼錯誤", 401


# 登出 API
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/')  # 登出後跳回首頁


# 取得登入狀態
@app.route('/api/status', methods=['GET'])
def status():
    if 'user_id' in session:
        return jsonify({"logged_in": True, "username": session.get('username')})
    else:
        return jsonify({"logged_in": False})

# 影片清單保護範例
@app.route('/api/videos', methods=['GET'])
def get_videos():
    if 'user_id' not in session:
        return jsonify({'error': '請先登入'}), 401

    videos = [
        {"id": 1, "title": "手語入門教學", "url": "https://example.com/video1.mp4"},
        {"id": 2, "title": "手語進階技巧", "url": "https://example.com/video2.mp4"},
    ]
    return jsonify({'videos': videos})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
