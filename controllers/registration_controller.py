from flask import Blueprint, request, jsonify, g
from middleware.auth import token_required
from models import db, Activity, Registration, User
from datetime import datetime

registration_bp = Blueprint('registration', __name__)

@registration_bp.route('/activities/<activity_id>/register', methods=['POST'])
@token_required
def register_activity(activity_id):
    """报名活动"""
    data = request.get_json() or {}
    
    try:
        user_id = int(g.user_id)
        
        # 检查活动是否存在
        if activity_id.isdigit():
            activity = Activity.query.get(int(activity_id))
        else:
            if activity_id.startswith('act_'):
                act_id = int(activity_id.split('_')[1])
                activity = Activity.query.get(act_id)
            else:
                activity = None
        
        if not activity:
            return jsonify({
                "code": 404,
                "message": "活动不存在"
            }), 404
        
        # 检查是否已报名
        existing_registration = Registration.query.filter_by(user_id=user_id, activity_id=activity.id).first()
        if existing_registration:
            return jsonify({
                "code": 400,
                "message": "您已报名该活动"
            }), 400
        
        # 检查名额
        approved_count = Registration.query.filter_by(activity_id=activity.id, status='approved').count()
        if activity.max_participants > 0 and approved_count >= activity.max_participants:
            return jsonify({
                "code": 400,
                "message": "活动名额已满"
            }), 400
        
        # 检查报名截止时间
        current_time = datetime.utcnow()
        if activity.registration_end_time and current_time > activity.registration_end_time:
            return jsonify({
                "code": 400,
                "message": "报名时间已截止"
            }), 400
        
        # 获取用户信息
        user = User.query.get(user_id)
        
        # 创建报名记录
        registration = Registration(
            user_id=user_id,
            activity_id=activity.id,
            status='pending',  # 默认待审核
            add_to_calendar=data.get('addToCalendar', True),
            reminder_time=datetime.fromisoformat(data['reminderTime'].replace('Z', '+00:00')) if data.get('reminderTime') else None
        )
        
        db.session.add(registration)
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "message": "报名成功，等待审核",
            "data": {
                'registrationId': f"reg_{registration.id:03d}",
                'status': 'pending'
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": f"报名失败: {str(e)}"
        }), 500

@registration_bp.route('/activities/<activity_id>/register', methods=['DELETE'])
@token_required
def cancel_registration(activity_id):
    """取消报名"""
    try:
        user_id = int(g.user_id)
        
        # 查找活动
        if activity_id.isdigit():
            activity = Activity.query.get(int(activity_id))
        else:
            if activity_id.startswith('act_'):
                act_id = int(activity_id.split('_')[1])
                activity = Activity.query.get(act_id)
            else:
                activity = None
        
        if not activity:
            return jsonify({
                "code": 404,
                "message": "活动不存在"
            }), 404
        
        # 查找报名记录
        registration = Registration.query.filter_by(user_id=user_id, activity_id=activity.id).first()
        
        if not registration:
            return jsonify({
                "code": 404,
                "message": "未找到报名记录"
            }), 404
        
        # 检查是否已审核通过，如果已通过需要特殊处理
        if registration.status == 'approved':
            return jsonify({
                "code": 400,
                "message": "报名已审核通过，请联系管理员取消"
            }), 400
        
        try:
            # 删除报名记录
            db.session.delete(registration)
            db.session.commit()
            
            return jsonify({
                "code": 200,
                "message": "取消报名成功"
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "code": 500,
                "message": f"取消报名失败: {str(e)}"
            }), 500
            
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"操作失败: {str(e)}"
        }), 500

@registration_bp.route('/activities/<activity_id>/participants', methods=['GET'])
@token_required
def get_activity_participants(activity_id):
    """查看报名人员名单（社团管理员）"""
    try:
        # 查找活动
        if activity_id.isdigit():
            activity = Activity.query.get(int(activity_id))
        else:
            if activity_id.startswith('act_'):
                act_id = int(activity_id.split('_')[1])
                activity = Activity.query.get(act_id)
            else:
                activity = None
        
        if not activity:
            return jsonify({
                "code": 404,
                "message": "活动不存在"
            }), 404
        
        # 权限检查：检查用户是否为该社团的管理员
        user_id = int(g.user_id)
        if activity.club.manager_id != user_id:
            return jsonify({
                "code": 403,
                "message": "权限不足，只有社团管理员可以查看报名人员"
            }), 403
        
        # 获取该活动的所有报名记录
        registrations = Registration.query.filter_by(activity_id=activity.id).all()
        
        participants = []
        for registration in registrations:
            user = registration.user
            participants.append({
                'user_id': user.id,
                'real_name': user.username,
                'phone': user.phone or '',
                'college': user.college or '',
                'major': user.major or '',
                'registration_time': registration.registration_time.isoformat() + 'Z' if registration.registration_time else None,
                'status': registration.status
            })
        
        return jsonify({
            "code": 200,
            "data": {
                "participants": participants,
                "total": len(participants)
            }
        })
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取报名人员失败: {str(e)}"
        }), 500

@registration_bp.route('/activities/<activity_id>/participants/<int:participant_id>', methods=['PUT'])
@token_required
def review_registration(activity_id, participant_id):
    """审核报名"""
    try:
        data = request.get_json()
        
        if 'status' not in data or data['status'] not in ['approved', 'rejected']:
            return jsonify({
                "code": 400,
                "message": "status参数必须为'approved'或'rejected'"
            }), 400
        
        # 查找活动
        if activity_id.isdigit():
            activity = Activity.query.get(int(activity_id))
        else:
            if activity_id.startswith('act_'):
                act_id = int(activity_id.split('_')[1])
                activity = Activity.query.get(act_id)
            else:
                activity = None
        
        if not activity:
            return jsonify({
                "code": 404,
                "message": "活动不存在"
            }), 404
        
        # 权限检查：检查用户是否为该社团的管理员
        user_id = int(g.user_id)
        if activity.club.manager_id != user_id:
            return jsonify({
                "code": 403,
                "message": "权限不足，只有社团管理员可以审核报名"
            }), 403
        
        # 查找报名记录
        registration = Registration.query.filter_by(activity_id=activity.id, user_id=participant_id).first()
        
        if not registration:
            return jsonify({
                "code": 404,
                "message": "未找到报名记录"
            }), 404
        
        # 更新审核状态
        old_status = registration.status
        registration.status = data['status']
        
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "message": "审核成功"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": f"审核失败: {str(e)}"
        }), 500

# 兼容原有接口
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
        user_id = int(g.user_id)
        
        registrations = Registration.query.filter_by(user_id=user_id).all()
        
        user_registrations = []
        for registration in registrations:
            reg_dict = registration.to_dict(with_activity_info=True)
            user_registrations.append(reg_dict)
        
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