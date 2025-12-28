from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from models import db

# 导入控制器
from controllers.auth_controller import auth_bp
from controllers.user_controller import user_bp
from controllers.activity_controller import activity_bp
from controllers.registration_controller import registration_bp
from controllers.club_controller import club_bp
from controllers.extractor_controller import extract_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 初始化数据库
    db.init_app(app)

    # 启用CORS
    CORS(app, resources={r"/v1/*": {"origins": "*"}})

    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix='/v1')
    app.register_blueprint(user_bp, url_prefix='/v1')
    app.register_blueprint(activity_bp, url_prefix='/v1')
    app.register_blueprint(registration_bp, url_prefix='/v1')
    app.register_blueprint(club_bp, url_prefix='/v1')
    app.register_blueprint(extract_bp, url_prefix='/v1')

    # 创建数据库表（如果不存在）
    with app.app_context():
        db.create_all()
        # 初始化默认数据
        init_default_data()

    # 统一错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"code": 404, "message": "接口不存在"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500

    # 健康检查
    @app.route('/health')
    def health_check():
        return jsonify({"status": "healthy", "service": "club-activities-api"})

    # 打印可用路由
    with app.app_context():
        print('可用的路由:')
        for rule in app.url_map.iter_rules():
            methods = ','.join(rule.methods)
            print(f'{rule.rule} -> {rule.endpoint} [{methods}]')

    return app


def init_default_data():
    """初始化默认数据"""
    from models import User, Club, Activity, Follow, Registration
    import hashlib

    # 检查是否已有数据
    if User.query.count() == 0:
        # 创建默认管理员用户
        admin = User(
            username='admin',
            student_id=20240001,
            email='admin@example.com',
            college='计算机学院',
            major='计算机科学与技术',
            grade='大四',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)

        # 创建默认测试用户
        test_user = User(
            username='testuser',
            student_id=20240002,
            email='test@example.com',
            college='软件学院',
            major='软件工程',
            grade='大三'
        )
        test_user.set_password('password123')
        db.session.add(test_user)

        # 创建默认社团
        clubs_data = [
            {
                'name': 'ACM算法协会',
                'description': '专注于算法竞赛和编程技能的学术社团',
                'type': '学术科技',
                'contact': 'acm_club@example.com',
                'logo': 'https://example.com/acm_logo.png',
                'manager_id': 1  # 管理员ID
            },
            {
                'name': '篮球社',
                'description': '热爱篮球运动的同学们聚集地',
                'type': '体育健身',
                'contact': 'basketball@example.com',
                'logo': 'https://example.com/basketball_logo.png',
                'manager_id': 1
            },
            {
                'name': '摄影协会',
                'description': '用镜头记录美好瞬间',
                'type': '文化艺术',
                'contact': 'photo@example.com',
                'logo': 'https://example.com/photo_logo.png',
                'manager_id': 1
            }
        ]

        for club_data in clubs_data:
            club = Club(**club_data)
            db.session.add(club)

        db.session.commit()

        # 创建默认活动
        clubs = Club.query.all()
        if clubs:
            import datetime
            activity = Activity(
                title='算法竞赛培训',
                description='每周算法竞赛培训活动',
                start_time=datetime.datetime.utcnow() + datetime.timedelta(days=7),
                end_time=datetime.datetime.utcnow() + datetime.timedelta(days=7, hours=2),
                location='理科楼 301',
                max_participants=100,
                registration_end_time=datetime.datetime.utcnow() + datetime.timedelta(days=6),
                contact_info='acm@example.com',
                tags='算法,竞赛,培训',
                club_id=clubs[0].id,
                creator_id=1
            )
            db.session.add(activity)

            # 测试用户关注第一个社团
            follow = Follow(user_id=2, club_id=1)
            db.session.add(follow)

            # 测试用户报名活动
            registration = Registration(
                user_id=2,
                activity_id=1,
                status='approved'
            )
            db.session.add(registration)

            db.session.commit()

            print("✅ 默认数据初始化完成")
    else:
        print("✅ 数据库已存在，跳过默认数据初始化")


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=1234, debug=True)