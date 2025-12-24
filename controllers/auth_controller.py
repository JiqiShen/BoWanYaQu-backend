from flask import Blueprint, request, jsonify
from middleware.auth import generate_token
from models import db, User

auth_bp = Blueprint('auth', __name__)

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
    if User.query.filter_by(username=data['username']).first():
        return jsonify({
            "code": 400,
            "message": "用户名已存在"
        }), 400
        
    # 检查学生证是否已注册
    if User.query.filter_by(student_id=data['student_id']).first():
        return jsonify({
            "code": 400,
            "message": "该学号已注册"
        }), 400
    
    try:
        # 创建用户
        user = User(
            username=data['username'],
            student_id=data['student_id'],
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            college=data.get('college', ''),
            major=data.get('major', ''),
            grade=data.get('grade', '')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # 生成token
        token = generate_token(str(user.id), user.role)
        
        return jsonify({
            "code": 200,
            "message": "注册成功",
            "data": {
                "user_id": user.id,
                "token": token
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
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
    user = User.query.filter_by(username=data['username']).first()
    
    if not user:
        return jsonify({
            "code": 401,
            "message": "用户名或密码错误"
        }), 401
    
    # 验证密码
    if not user.check_password(data['password']):
        return jsonify({
            "code": 401,
            "message": "用户名或密码错误"
        }), 401
    
    # 生成token
    token = generate_token(str(user.id), user.role)
    
    return jsonify({
        "code": 200,
        "message": "登录成功",
        "data": {
            "user_id": user.id,
            "username": user.username,
            "student_id": user.student_id,
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
        
        # 检查是否已有该微信用户
        user = User.query.filter_by(username=f"wechat_{openid[-8:]}").first()
        if not user:
            # 创建新用户
            user = User(
                username=f"wechat_{openid[-8:]}",
                student_id=int(f"2024{int(openid[-6:]) % 10000:04d}"),
                name=f"微信用户{openid[-6:]}",
                role='student'
            )
            user.set_password(openid)  # 使用openid作为密码
            db.session.add(user)
            db.session.commit()
        
        # 生成token
        token = generate_token(str(user.id), user.role)
        
        return jsonify({
            "code": 200,
            "message": "登录成功",
            "data": {
                "token": token,
                "userInfo": {
                    'userId': user.id,
                    'name': user.username,
                    'avatar': user.avatar or 'https://avatar.url/default.png',
                    'role': user.role
                }
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": f"登录失败: {str(e)}"
        }), 500

@auth_bp.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """刷新Token"""
    # 在实际应用中需要验证refresh token
    # 这里简化处理，重新生成token
    from flask import g
    if not hasattr(g, 'user_id'):
        return jsonify({
            "code": 401,
            "message": "未授权"
        }), 401
        
    user = User.query.get(int(g.user_id))
    if not user:
        return jsonify({
            "code": 404,
            "message": "用户不存在"
        }), 404
    
    token = generate_token(str(user.id), user.role)
    
    return jsonify({
        "code": 200,
        "message": "Token刷新成功",
        "data": {
            "token": token
        }
    })