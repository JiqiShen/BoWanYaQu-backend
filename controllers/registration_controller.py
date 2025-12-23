from flask import Blueprint, request, jsonify, g
from middleware.auth import token_required
from datetime import datetime

registration_bp = Blueprint('registration', __name__)

# 模拟报名数据（扩展原有数据）
registrations_db = {
    '1_1': {  # user_id_activity_id
        'registrationId': 'reg_001',
        'userId': 1,
        'activityId': 'act_001',
        'activity_id': 1,
        'signUpTime': '2024-01-10T10:00:00Z',
        'status': 'approved',  # pending, approved, rejected
        'addToCalendar': True,
        'reminderTime': None,
        'real_name': '张三',
        'phone': '13800138000',
        'college': '计算机学院',
        'major': '计算机科学与技术',
        'registration_time': '2024-01-10T10:00:00Z'
    }
}

@registration_bp.route('/activities/<activity_id>/register', methods=['POST'])
@token_required
def register_activity(activity_id):
    """报名活动"""
    data = request.get_json() or {}
    
    try:
        user_id_int = int(g.user_id)
        
        # 检查活动是否存在
        from controllers.activity_controller import activities_db
        activity = activities_db.get(f"act_{int(activity_id):03d}" if activity_id.isdigit() else activity_id)
        if not activity:
            return jsonify({
                "code": 404,
                "message": "活动不存在"
            }), 404
        
        # 检查是否已报名
        registration_key = f"{user_id_int}_{activity.get('activity_id', 0)}"
        if registration_key in registrations_db:
            return jsonify({
                "code": 400,
                "message": "您已报名该活动"
            }), 400
        
        # 检查名额
        if activity['currentParticipants'] >= activity['maxParticipants']:
            return jsonify({
                "code": 400,
                "message": "活动名额已满"
            }), 400
        
        # 检查报名截止时间
        registration_end_time = activity.get('registration_end_time')
        if registration_end_time and datetime.utcnow().isoformat() + 'Z' > registration_end_time:
            return jsonify({
                "code": 400,
                "message": "报名时间已截止"
            }), 400
        
        # 获取用户信息
        from controllers.auth_controller import users_db
        user_key = f"user_{user_id_int:03d}"
        user_info = users_db.get(user_key, {})
        
        # 创建报名记录
        registration_id = f"reg_{len(registrations_db) + 1:03d}"
        registration = {
            'registrationId': registration_id,
            'userId': user_id_int,
            'activityId': activity['activityId'],
            'activity_id': activity.get('activity_id', 0),
            'signUpTime': datetime.utcnow().isoformat() + 'Z',
            'status': 'pending',  # 默认待审核
            'addToCalendar': data.get('addToCalendar', True),
            'reminderTime': data.get('reminderTime'),
            'real_name': user_info.get('username', ''),
            'phone': user_info.get('phone', ''),
            'college': user_info.get('college', ''),
            'major': user_info.get('major', ''),
            'registration_time': datetime.utcnow().isoformat() + 'Z'
        }
        
        registrations_db[registration_key] = registration
        
        # 更新活动参与人数
        activity['currentParticipants'] += 1
        
        return jsonify({
            "code": 200,
            "message": "报名成功，等待审核"
        })
        
    except (ValueError, TypeError) as e:
        return jsonify({
            "code": 400,
            "message": f"参数错误: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"报名失败: {str(e)}"
        }), 500

@registration_bp.route('/activities/<activity_id>/register', methods=['DELETE'])
@token_required
def cancel_registration(activity_id):
    """取消报名"""
    try:
        user_id_int = int(g.user_id)
        activity_key = f"act_{int(activity_id):03d}" if activity_id.isdigit() else activity_id
        
        registration_key = f"{user_id_int}_{int(activity_id)}"
        
        if registration_key not in registrations_db:
            return jsonify({
                "code": 404,
                "message": "未找到报名记录"
            }), 404
        
        # 检查是否已审核通过，如果已通过需要特殊处理
        if registrations_db[registration_key].get('status') == 'approved':
            return jsonify({
                "code": 400,
                "message": "报名已审核通过，请联系管理员取消"
            }), 400
        
        try:
            # 删除报名记录
            del registrations_db[registration_key]
            
            # 更新活动参与人数
            from controllers.activity_controller import activities_db
            activity = activities_db.get(activity_key)
            if activity and activity['currentParticipants'] > 0:
                activity['currentParticipants'] -= 1
            
            return jsonify({
                "code": 200,
                "message": "取消报名成功"
            })
            
        except Exception as e:
            return jsonify({
                "code": 500,
                "message": f"取消报名失败: {str(e)}"
            }), 500
            
    except (ValueError, TypeError) as e:
        return jsonify({
            "code": 400,
            "message": f"参数错误: {str(e)}"
        }), 400

# 新增管理功能接口
@registration_bp.route('/activities/<activity_id>/participants', methods=['GET'])
@token_required
def get_activity_participants(activity_id):
    """查看报名人员名单（社团管理员）"""
    try:
        # 权限检查：检查用户是否为该社团的管理员
        # 这里简化处理，假设所有认证用户都可以查看
        from controllers.activity_controller import activities_db
        activity = activities_db.get(f"act_{int(activity_id):03d}" if activity_id.isdigit() else activity_id)
        
        if not activity:
            return jsonify({
                "code": 404,
                "message": "活动不存在"
            }), 404
        
        # 获取该活动的所有报名记录
        participants = []
        for reg_key, registration in registrations_db.items():
            if registration.get('activity_id') == int(activity_id) or registration.get('activityId') == f"act_{int(activity_id):03d}":
                participants.append({
                    'user_id': registration['userId'],
                    'real_name': registration.get('real_name', ''),
                    'phone': registration.get('phone', ''),
                    'college': registration.get('college', ''),
                    'major': registration.get('major', ''),
                    'registration_time': registration.get('registration_time', ''),
                    'status': registration.get('status', 'pending')
                })
        
        return jsonify({
            "code": 200,
            "data": {
                "participants": participants,
                "total": len(participants)
            }
        })
        
    except (ValueError, TypeError) as e:
        return jsonify({
            "code": 400,
            "message": f"参数错误: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取报名人员失败: {str(e)}"
        }), 500

@registration_bp.route('/activities/<activity_id>/participants/<int:user_id>', methods=['PUT'])
@token_required
def review_registration(activity_id, user_id):
    """审核报名"""
    try:
        data = request.get_json()
        
        if 'status' not in data or data['status'] not in ['approved', 'rejected']:
            return jsonify({
                "code": 400,
                "message": "status参数必须为'approved'或'rejected'"
            }), 400
        
        registration_key = f"{user_id}_{int(activity_id)}"
        
        if registration_key not in registrations_db:
            return jsonify({
                "code": 404,
                "message": "未找到报名记录"
            }), 404
        
        # 更新审核状态
        registrations_db[registration_key]['status'] = data['status']
        
        # 如果拒绝，减少活动参与人数
        if data['status'] == 'rejected':
            from controllers.activity_controller import activities_db
            activity_key = f"act_{int(activity_id):03d}"
            activity = activities_db.get(activity_key)
            if activity and activity['currentParticipants'] > 0:
                activity['currentParticipants'] -= 1
        
        return jsonify({
            "code": 200,
            "message": "审核成功"
        })
        
    except (ValueError, TypeError) as e:
        return jsonify({
            "code": 400,
            "message": f"参数错误: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"审核失败: {str(e)}"
        }), 500

# 保留原有接口，兼容URL
@registration_bp.route('/activities/<activity_id>/registrations', methods=['POST'])
@token_required
def sign_up_activity_old(activity_id):
    """兼容原有报名接口"""
    return register_activity(activity_id)

@registration_bp.route('/users/registrations', methods=['GET'])
@token_required
def get_user_registrations():
    """获取我的报名列表（兼容原有接口）"""
    try:
        user_id_int = int(g.user_id)
        
        user_registrations = []
        for reg_key, registration in registrations_db.items():
            if reg_key.startswith(str(user_id_int)):
                # 获取活动信息
                from controllers.activity_controller import activities_db
                activity = activities_db.get(registration['activityId'])
                if activity:
                    registration_with_activity = registration.copy()
                    registration_with_activity['activityInfo'] = {
                        'title': activity['title'],
                        'startTime': activity['startTime'],
                        'location': activity['location']
                    }
                    user_registrations.append(registration_with_activity)
        
        return jsonify({
            "code": 200,
            "data": {
                "registrations": user_registrations
            }
        })
        
    except (ValueError, TypeError) as e:
        return jsonify({
            "code": 400,
            "message": f"用户ID格式错误: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取报名列表失败: {str(e)}"
        }), 500