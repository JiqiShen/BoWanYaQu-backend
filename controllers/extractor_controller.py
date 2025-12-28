from flask import Blueprint, request, jsonify
import json
import time
from openai import OpenAI
import os
from dotenv import load_dotenv
from extractor.activity_info_extractor import Activity_info_extractor
from extractor.wechat_article_extractor import Wechat_article_extractor

# 修正Blueprint名称，使其与变量名一致
extract_bp = Blueprint('extract', __name__)


@extract_bp.route('/extract/wechat', methods=['POST'])
def extract_wechat():
    try:
        # 从请求中获取文章URL（而不是硬编码）
        data = request.get_json()
        if not data or 'article_url' not in data:
            return jsonify({
                'code': 400,
                'message': '缺少文章URL参数',
                'data': None
            }), 400

        article_url = data['article_url']
        print(article_url)
        load_dotenv()

        # 从环境变量获取API密钥
        api_key = os.getenv('ALIYUN_API_KEY')

        # 初始化客户端
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

        # 提取文章内容
        extractor = Wechat_article_extractor()
        article_content = extractor.extract_article_content(article_url)
        print(article_content)
        if not article_content:
            return jsonify({
                'code': 500,
                'message': '文章内容提取失败',
                'data': None
            }), 500

        # 提取活动信息
        activity_extractor = Activity_info_extractor(client)
        activity_info = activity_extractor.extract_activity_info(article_content)
        print(article_content)
        if not activity_info:
            return jsonify({
                'code': 500,
                'message': '活动信息提取失败',
                'data': None
            }), 500
        # 返回成功响应
        return jsonify({
            'code': 200,
            'message': '提取成功',
            'data': {
                'activity_info': activity_info
            }
        }), 200

    except Exception as e:
        # 异常处理
        return jsonify({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': None
        }), 500