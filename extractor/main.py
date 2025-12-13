import json
from openai import OpenAI
from extractor.ActivityInfoExtractor import ActivityInfoExtractor
from extractor.WeChatArticleExtractor import WeChatArticleExtractor


def main():
    # 配置信息
    ACCESS_KEY_ID = "your_access_key_id"

    # 初始化客户端
    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
        api_key="sk-ed733795179440cc9a7e705b0e375df2",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    # 文章URL
    article_url = "https://mp.weixin.qq.com/s/PtEUwhj6RglHvpmS1Nbysg"

    # 提取文章内容
    extractor = WeChatArticleExtractor()
    article_content = extractor.extract_article_content(article_url)

    if article_content:
        print(article_content)
        print("文章内容提取成功")

        # 提取活动信息
        activity_extractor = ActivityInfoExtractor(client)
        activity_info = activity_extractor.extract_activity_info(article_content)

        if activity_info:
            print("活动信息提取成功:")
            print(json.dumps(activity_info, ensure_ascii=False, indent=2))

        else:
            print("活动信息提取失败")
    else:
        print("文章内容提取失败")


if __name__ == "__main__":
    main()