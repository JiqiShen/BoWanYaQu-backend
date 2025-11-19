from flask import Flask, jsonify
from flask_cors import CORS
from config import Config

# 导入控制器
from controllers.auth_controller import auth_bp
from controllers.user_controller import user_bp
from controllers.activity_controller import activity_bp
from controllers.registration_controller import registration_bp
from controllers.club_controller import club_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 启用CORS
    CORS(app, resources={r"/v1/*": {"origins": "*"}})
    
    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix='/v1')
    app.register_blueprint(user_bp, url_prefix='/v1')
    app.register_blueprint(activity_bp, url_prefix='/v1')
    app.register_blueprint(registration_bp, url_prefix='/v1')
    app.register_blueprint(club_bp, url_prefix='/v1')
    
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
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=1234, debug=True)