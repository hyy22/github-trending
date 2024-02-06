import time
import schedule
from requests_html import HTMLSession, HTML
from datetime import datetime
import json
import os

# 执行时间
EXEC_TIME = os.getenv("EXEC_TIME", "08:00")
# 重试次数
MAX_RETRY = int(os.getenv("MAX_RETRY", 10))


def task():
    trending_url = "https://github.com/trending"
    session = HTMLSession()
    r = session.get(trending_url)
    html = HTML(html=r.content)
    projects = []
    for row in html.find(".Box-row"):
        title = row.find(".Box-row>h2", first=True).text
        link = row.find(".Box-row>h2>a", first=True).attrs["href"]
        desc_element = row.find(".Box-row>p", first=True)
        desc = '' if desc_element is None else desc_element.text
        wrapper = row.find(".Box-row>div:last-child>a")
        star = wrapper[0].text
        fork = wrapper[1].text
        projects.append({
            "title": title,
            "link": link,
            "desc": desc,
            "star": star,
            "fork": fork,
        })
    # 写入文件
    path = f"./trending/{datetime.now().strftime(format='%Y-%m-%d')}.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(projects, ensure_ascii=False))
    print(f"写入成功：{path}")


# 重试
def retry(func, n=10):
    for i in range(n):
        try:
            func()
            return
        except Exception as e:
            print(f"第{i + 1}次重试：{e}")
    print("重试次数已用完，任务失败")


# 任务调度
if __name__ == "__main__":
    # 每天执行一次
    schedule.every().day.at(EXEC_TIME).do(retry, n=MAX_RETRY, func=task)
    while True:
        schedule.run_pending()
        time.sleep(60)
