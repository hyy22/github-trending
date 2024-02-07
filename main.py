import time
import schedule
from requests_html import HTMLSession, HTML
from datetime import datetime
import json
import os
from string import Template
import http.server
import socketserver
import threading

# 同步间隔小时
EXEC_PER_HOUR = int(os.getenv("EXEC_PER_HOUR", 1))
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
    path = f"./dist/trending/{datetime.now().strftime(format='%Y-%m-%d')}.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(projects, ensure_ascii=False))
    print(f"写入成功：{path}")
    # 生成网页
    render()


# 重试
def retry(func, n=10):
    for i in range(n):
        try:
            func()
            return
        except Exception as e:
            print(f"第{i + 1}次重试：{e}")
    print("重试次数已用完，任务失败")


# 渲染页面
def render():
    with open("./template.html", "r", encoding="utf-8") as f:
        data = f.read()
        with open("./dist/index.html", "w", encoding="utf-8") as fw:
            # 日期渲染列表
            date_list = sorted([date.split('.')[0] for date in os.listdir("./dist/trending")], key=lambda x: datetime.strptime(x, '%Y-%m-%d'), reverse=True)
            date_div_list = [f'<div class="item">{date}</div>' for date in date_list]
            fw.write(Template(data).safe_substitute(date_div_list=''.join(date_div_list)))


# 开启静态服务
class StaticServer(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="./dist", **kwargs)


def start_server():
    handler = http.server.SimpleHTTPRequestHandler
    handler.directory = './dist'
    with socketserver.TCPServer(("", 80), StaticServer) as httpd:
        print("静态服务已开启")
        httpd.serve_forever()


# 任务调度
if __name__ == "__main__":
    # 启动静态服务
    thread = threading.Thread(target=start_server)
    thread.start()
    # 每两小时执行一次
    schedule.every(EXEC_PER_HOUR).hours.do(retry, n=MAX_RETRY, func=task)
    while True:
        schedule.run_pending()
        time.sleep(1)
