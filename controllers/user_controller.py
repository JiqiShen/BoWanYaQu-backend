from flask import Blueprint, request, jsonify, g
from middleware.auth import token_required

user_bp = Blueprint('user', __name__)

# 从auth_controller导入用户数据库
from controllers.auth_controller import users_db

@user_bp.route('/user/profile', methods=['GET'])
@token_required
def get_user_profile():
    """获取用户信息"""
    # 从数据库查找用户（注意：g.user_id是字符串，需要转换为数字ID）
    try:
        user_id_int = int(g.user_id)
    except ValueError:
        return jsonify({
            "code": 400,
            "message": "用户ID格式错误"
        }), 400
    
    # 查找用户
    user_found = None
    for user_data in users_db.values():
        if user_data['user_id'] == user_id_int:
            user_found = user_data
            break
    
    if not user_found:
        return jsonify({
            "code": 404,
            "message": "用户不存在"
        }), 404
    
    # 返回用户信息（不包含密码）
    profile = {
        'user_id': user_found['user_id'],
        'username': user_found['username'],
        'student_id': user_found['student_id'],
        'email': user_found.get('email', ''),
        'phone': user_found.get('phone', ''),
        'college': user_found.get('college', ''),
        'major': user_found.get('major', ''),
        'grade': user_found.get('grade', ''),
        'created_at': user_found.get('created_at', '')
    }
    
    return jsonify({
        "code": 200,
        "data": profile
    })

@user_bp.route('/user/profile', methods=['PUT'])
@token_required
def update_user_profile():
    """修改用户信息"""
    data = request.get_json()
    
    # 从数据库查找用户
    try:
        user_id_int = int(g.user_id)
    except ValueError:
        return jsonify({
            "code": 400,
            "message": "用户ID格式错误"
        }), 400
    
    # 查找用户ID
    user_key = None
    for key, user_data in users_db.items():
        if user_data['user_id'] == user_id_int:
            user_key = key
            break
    
    if not user_key:
        return jsonify({
            "code": 404,
            "message": "用户不存在"
        }), 404
    
    # 可更新的字段
    update_fields = ['username', 'email', 'phone', 'college', 'major', 'grade']
    
    # 检查用户名是否已存在（如果要更新用户名）
    if 'username' in data and data['username'] != users_db[user_key]['username']:
        for user_data in users_db.values():
            if user_data['user_id'] != user_id_int and user_data['username'] == data['username']:
                return jsonify({
                    "code": 400,
                    "message": "用户名已存在"
                }), 400
    
    # 更新用户信息
    for field in update_fields:
        if field in data:
            users_db[user_key][field] = data[field]
    
    return jsonify({
        "code": 200,
        "message": "修改成功"
    })