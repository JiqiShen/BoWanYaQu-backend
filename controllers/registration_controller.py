from flask import Blueprint, request, jsonify, g
from middleware.auth import token_required

registration_bp = Blueprint('registration', __name__)

# 模拟报名数据
registrations_db = {}

@registration_bp.route('/activities/<activity_id>/registrations', methods=['POST'])
@token_required
def sign_up_activity(activity_id):
    """报名活动"""
    data = request.get_json() or {}
    
    # 检查活动是否存在
    from controllers.activity_controller import activities_db
    activity = activities_db.get(activity_id)
    if not activity:
        return jsonify({
            "code": 404,
            "message": "活动不存在"
        }), 404
    
    # 检查是否已报名
    registration_key = f"{g.user_id}_{activity_id}"
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
    
    try:
        # 创建报名记录
        registration_id = f"reg_{len(registrations_db) + 1:03d}"
        registration = {
            'registrationId': registration_id,
            'userId': g.user_id,
            'activityId': activity_id,
            'signUpTime': '2024-01-10T10:00:00Z',  # 实际应该用当前时间
            'status': 'confirmed',
            'addToCalendar': data.get('addToCalendar', True),
            'reminderTime': data.get('reminderTime')
        }
        
        registrations_db[registration_key] = registration
        
        # 更新活动参与人数
        activity['currentParticipants'] += 1
        
        return jsonify({
            "code": 200,
            "message": "报名成功",
            "data": {
                'registrationId': registration_id,
                'status': 'confirmed'
            }
        })
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"报名失败: {str(e)}"
        }), 500

@registration_bp.route('/activities/<activity_id>/registrations', methods=['DELETE'])
@token_required
def cancel_registration(activity_id):
    """取消报名"""
    registration_key = f"{g.user_id}_{activity_id}"
    
    if registration_key not in registrations_db:
        return jsonify({
            "code": 404,
            "message": "未找到报名记录"
        }), 404
    
    try:
        # 删除报名记录
        del registrations_db[registration_key]
        
        # 更新活动参与人数
        from controllers.activity_controller import activities_db
        activity = activities_db.get(activity_id)
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

@registration_bp.route('/users/registrations', methods=['GET'])
@token_required
def get_user_registrations():
    """获取我的报名列表"""
    try:
        status = request.args.get('status')
        
        user_registrations = []
        for reg_key, registration in registrations_db.items():
            if reg_key.startswith(g.user_id):
                if status and registration['status'] != status:
                    continue
                
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
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取报名列表失败: {str(e)}"
        }), 500