from flask import Blueprint, request, jsonify
from middleware.auth import generate_token
import hashlib
import uuid
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

# 模拟用户数据存储（实际应该用数据库）
users_db = {
    'user_001': {
        'user_id': 1,
        'username': 'testuser',
        'student_id': 20210001,
        'password_hash': hashlib.sha256('password123'.encode()).hexdigest(),  # 密码: password123
        'email': 'test@example.com',
        'phone': '13800138000',
        'college': '计算机学院',
        'major': '计算机科学与技术',
        'grade': '大三',
        'created_at': '2024-01-01T00:00:00Z'
    }
}

# 学生证号到用户ID的映射
student_id_to_user = {20210001: 'user_001'}

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    # 验证必要字段
    required_fields = ['username', 'password', 'student_id']
    if not all(field in data for field in required_fields):
        return jsonify({
            "code": 400,
            "message": "缺少必要字段：username, password, student_id"
        }), 400
    
    # 检查用户名是否已存在
    for user in users_db.values():
        if user['username'] == data['username']:
            return jsonify({
                "code": 400,
                "message": "用户名已存在"
            }), 400
        
    # 检查学生证是否已注册
    if data['student_id'] in student_id_to_user:
        return jsonify({
            "code": 400,
            "message": "该学号已注册"
        }), 400
    
    try:
        # 生成用户ID
        user_id = f"user_{len(users_db) + 1:03d}"
        user_db_id = len(users_db) + 1
        
        # 创建用户对象
        user = {
            'user_id': user_db_id,
            'username': data['username'],
            'student_id': data['student_id'],
            'password_hash': hashlib.sha256(data['password'].encode()).hexdigest(),
            'email': data.get('email', ''),
            'phone': data.get('phone', ''),
            'college': data.get('college', ''),
            'major': data.get('major', ''),
            'grade': data.get('grade', ''),
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'role': 'student'  # 默认角色为学生
        }
        
        # 存储用户
        users_db[user_id] = user
        student_id_to_user[data['student_id']] = user_id
        
        # 生成token
        token = generate_token(str(user_db_id), user['role'])
        
        return jsonify({
            "code": 200,
            "message": "注册成功",
            "data": {
                "user_id": user_db_id,
                "token": token
            }
        }), 201
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"注册失败: {str(e)}"
        }), 500

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    # 验证必要字段
    if 'username' not in data or 'password' not in data:
        return jsonify({
            "code": 400,
            "message": "缺少username或password"
        }), 400
    
    # 查找用户
    user = None
    for user_data in users_db.values():
        if user_data['username'] == data['username']:
            user = user_data
            break
    
    if not user:
        return jsonify({
            "code": 401,
            "message": "用户名或密码错误"
        }), 401
    
    # 验证密码
    password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
    if password_hash != user['password_hash']:
        return jsonify({
            "code": 401,
            "message": "用户名或密码错误"
        }), 401
    
    # 生成token
    token = generate_token(str(user['user_id']), user['role'])
    
    return jsonify({
        "code": 200,
        "message": "登录成功",
        "data": {
            "user_id": user['user_id'],
            "username": user['username'],
            "student_id": user['student_id'],
            "token": token
        }
    })

@auth_bp.route('/auth/wechat-login', methods=['POST'])
def wechat_login():
    """微信登录（兼容原有接口）"""
    data = request.get_json()
    code = data.get('code') if data else None
    
    if not code:
        return jsonify({
            "code": 400,
            "message": "缺少code参数"
        }), 400
    
    try:
        # 模拟用户数据
        openid = f"mock_openid_{code}"
        user_info = {
            'userId': f"user_{openid[-8:]}",
            'name': f"用户{openid[-6:]}",
            'avatar': "https://avatar.url/default.png",
            'role': 'student'
        }
        
        # 生成token
        token = generate_token(user_info['userId'], user_info['role'])
        
        return jsonify({
            "code": 200,
            "message": "登录成功",
            "data": {
                "token": token,
                "userInfo": user_info
            }
        })
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"登录失败: {str(e)}"
        }), 500

@auth_bp.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """刷新Token（需要重构以使用新token系统）"""
    # 在实际应用中需要验证refresh token
    # 这里简化处理
    from flask import g
    if not hasattr(g, 'user_id'):
        return jsonify({
            "code": 401,
            "message": "未授权"
        }), 401
        
    # 获取用户角色
    user = users_db.get(f"user_{g.user_id:03d}")
    role = user['role'] if user else 'student'
    
    token = generate_token(str(g.user_id), role)
    
    return jsonify({
        "code": 200,
        "message": "Token刷新成功",
        "data": {
            "token": token
        }
    })