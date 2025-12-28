from flask import Blueprint, request, jsonify, g
from flask_sqlalchemy import SQLAlchemy
from middleware.auth import token_required
from models import db, Activity, Club, Registration
from datetime import datetime
import time

db = SQLAlchemy()
activity_bp = Blueprint('activity', __name__)


@activity_bp.route('/activities/latest', methods=['GET'])
def get_latest_activities():
    """获取最新活动"""
    try:
        limit = int(request.args.get('limit', 10))

        # 获取最新活动
        activities = Activity.query \
            .filter_by(status='published') \
            .order_by(Activity.created_at.desc()) \
            .limit(limit) \
            .all()

        # 格式化返回数据
        formatted_activities = []
        for activity in activities:
            formatted_activities.append({
                'activity_id': activity.id,
                'title': activity.title,
                'start_time': activity.start_time,
                'club_name': activity.club.name if activity.club else '',
                'tag': activity.tags.split(',')[0] if activity.tags else '',
                'participant_count': Registration.query.filter_by(activity_id=activity.id, status='approved').count(),
                'max_participants': activity.max_participants
            })

        return jsonify({
            "code": 200,
            "data": {
                "activities": formatted_activities
            }
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取最新活动失败: {str(e)}"
        }), 500


@activity_bp.route('/activities', methods=['GET'])
def get_activities():
    """获取活动列表"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        status = request.args.get('status')  # upcoming, ongoing, ended
        tag = request.args.get('tag', '')
        club_id = request.args.get('club_id', '')
        keyword = request.args.get('keyword', '')
        max_participants = request.args.get('num', '')

        # 构建查询
        query = Activity.query.filter_by(status='published')

        # 状态筛选
        current_time = datetime.utcnow()
        if status == 'upcoming':
            query = query.filter(Activity.start_time > current_time)
        elif status == 'ongoing':
            query = query.filter(Activity.start_time <= current_time, Activity.end_time >= current_time)
        elif status == 'ended':
            query = query.filter(Activity.end_time < current_time)

        # 标签筛选
        if tag:
            query = query.filter(Activity.tags.like(f'%{tag}%'))

        # 社团筛选
        if club_id:
            query = query.filter_by(club_id=club_id)

        if keyword:
            query = query.filter(
                db.or_(
                    Activity.title.ilike(f'%{keyword}%'),
                    Activity.description.ilike(f'%{keyword}%'),
                    Activity.tags.ilike(f'%{keyword}%')
                )
            )

        if max_participants and max_participants != 'all':
            if max_participants == '20':
                query = query.filter(Activity.max_participants <= 20)
            elif max_participants == '20-50':
                query = query.filter(20 < Activity.max_participants <= 50)
            elif max_participants == '50-100':
                query = query.filter(50 < Activity.max_participants <= 100)
            elif max_participants == '100+':
                query = query.filter(Activity.max_participants > 100)

        # 获取总数
        total = query.count()

        # 分页
        activities = query.order_by(Activity.start_time.asc()) \
            .offset((page - 1) * limit) \
            .limit(limit) \
            .all()

        # 转换为字典
        user_id = int(g.user_id) if hasattr(g, 'user_id') else None
        activities_data = [activity.to_dict(user_id=user_id) for activity in activities]

        return jsonify({
            "code": 200,
            "data": {
                "activities": activities_data,
                "total": total,
                "page": page,
                "limit": limit
            }
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取活动列表失败: {str(e)}"
        }), 500


@activity_bp.route('/activities', methods=['POST'])
@token_required
def create_activity():
    """创建活动"""
    data = request.get_json()
    print(data)

    if not data:
        return jsonify({
            "code": 400,
            "message": "请求体必须为JSON格式"
        }), 400

    # 验证必要字段
    required_fields = ['title', 'startTime', 'location']
    if not all(field in data for field in required_fields):
        return jsonify({
            "code": 400,
            "message": "缺少必要字段：title, startTime, location"
        }), 400

    try:
        # 解析时间
        start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00')) if data.get('endTime') else None
        registration_end_time = datetime.fromisoformat(
            data['registration_end_time'].replace('Z', '+00:00')) if data.get('registration_end_time') else None

        # 创建活动
        activity = Activity(
            title=data['title'],
            description=data.get('description', ''),
            start_time=start_time,
            end_time=end_time,
            location=data['location'],
            max_participants=data.get('maxParticipants', 0),
            registration_end_time=registration_end_time,
            contact_info=data.get('contact_info', ''),
            tags=','.join(data.get('tags', [])) if isinstance(data.get('tags'), list) else data.get('tags', ''),
            club_id=data.get('club_id', 1),
            creator_id=int(g.user_id)
        )

        db.session.add(activity)
        db.session.commit()

        return jsonify({
            "code": 200,
            "message": "活动创建成功",
            "data": {
                "activity_id": activity.id,
                "activityId": f"act_{activity.id:03d}"
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": f"创建活动失败: {str(e)}"
        }), 500


@activity_bp.route('/activities/<activity_id>', methods=['GET'])
def get_activity_detail(activity_id):
    """获取活动详情"""
    try:
        # 尝试按ID查找
        if activity_id.isdigit():
            activity = Activity.query.get(int(activity_id))
        else:
            # 尝试解析act_xxx格式
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

        # 获取用户ID（如果有认证）
        user_id = None
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            try:
                token = token[7:]
                from middleware.auth import Config
                import jwt
                data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
                user_id = int(data['user_id'])
            except:
                pass

        activity_detail = activity.to_dict(user_id=user_id)

        return jsonify({
            "code": 200,
            "data": activity_detail
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取活动详情失败: {str(e)}"
        }), 500


@activity_bp.route('/user/registered-activities', methods=['GET'])
@token_required
def get_registered_activities():
    """获取报名成功的活动"""
    try:
        user_id = int(g.user_id)

        # 获取用户已批准报名的活动
        registrations = Registration.query.filter_by(user_id=user_id, status='approved').all()

        registered_activities = []
        for registration in registrations:
            activity = registration.activity
            if activity:
                registered_activities.append({
                    'activity_id': activity.id,
                    'title': activity.title,
                    'start_time': activity.start_time.isoformat() + 'Z' if activity.start_time else None,
                    'end_time': activity.end_time.isoformat() + 'Z' if activity.end_time else None,
                    'location': activity.location,
                    'club_name': activity.club.name if activity.club else '',
                    'participant_count': Registration.query.filter_by(activity_id=activity.id,
                                                                      status='approved').count(),
                    'max_participants': activity.max_participants,
                    'status': activity.status,
                    'is_registered': True
                })

        return jsonify({
            "code": 200,
            "data": {
                "activities": registered_activities,
                "total": len(registered_activities)
            }
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取报名活动失败: {str(e)}"
        }), 500