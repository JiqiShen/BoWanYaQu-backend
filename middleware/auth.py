from functools import wraps
from flask import request, jsonify, g
import jwt
from config import Config
from datetime import datetime, timedelta
from models import User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"code": 401, "message": "Token缺失"}), 401
            
        # 移除 Bearer 前缀
        if token.startswith('Bearer '):
            token = token[7:]
            
        try:
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            user_id = data['user_id']
            
            # 验证用户是否存在
            user = User.query.get(int(user_id))
            if not user:
                return jsonify({"code": 401, "message": "用户不存在"}), 401
            
            g.user_id = user_id
            g.user_role = data.get('role', 'student')
        except jwt.ExpiredSignatureError:
            return jsonify({"code": 401, "message": "Token已过期"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"code": 401, "message": "无效Token"}), 401
            
        return f(*args, **kwargs)
    return decorated

def generate_token(user_id, role='student'):
    """生成JWT Token"""
    payload = {
        'user_id': str(user_id),
        'role': role,
        'exp': datetime.utcnow() + Config.JWT_ACCESS_TOKEN_EXPIRES
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')