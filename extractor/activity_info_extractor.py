import json
import re
import requests
class ActivityInfoExtractor:
    def __init__(self, bailian_client):
        self.client = bailian_client

    def extract_activity_info(self, article_content):
        """使用百炼大模型提取活动信息"""

        prompt = f"""
        请从以下微信公众号文章内容中提取活动信息并生成三个标签（用,分隔），并以JSON格式返回：
        
        文章内容：
        {article_content}
        
        请提取以下信息：
        1. 活动名称
        2. 活动时间（开始时间和结束时间）
        3. 活动地点
        4. 活动描述
        5. 标签
        
        如果某些信息在文章中未提及，请用"未知"表示。
        
        请返回标准的JSON格式：
        {{
            "activity_name": "活动名称",
            "start_time": "开始时间",
            "end_time": "结束时间",
            "location": "活动地点",
            "description": "活动描述",
            "tags": "标签"
        }}
        """

        try:
            # 调用百炼API
            completion = self.client.chat.completions.create(
                model="qwen-plus",
                messages=[
                    {"role": "user", "content": prompt},
                ]
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"信息提取失败: {e}")
            return None

    def _parse_text_response(self, text):
        """备选方案：解析文本响应"""
        info = {}
        lines = text.split('\n')

        for line in lines:
            if '活动名称' in line:
                info['activity_name'] = line.split('：')[-1].strip()
            elif '活动时间' in line:
                info['start_time'] = line.split('：')[-1].strip()
            # 其他字段类似处理...

        return info