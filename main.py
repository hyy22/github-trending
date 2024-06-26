import time
import schedule
from requests_html import HTMLSession, HTML
from datetime import datetime
import json
import os
from string import Template
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse, Response
from pydantic import BaseModel
from typing import Union
import threading
from contextlib import asynccontextmanager

# 每天几点执行
EXEC_TIME = os.getenv("EXEC_TIME", "08:00")
# 重试次数
MAX_RETRY = int(os.getenv("MAX_RETRY", 10))
# 输出目录
DIST_DIR = "./dist"
TRENDING_DIR = "./dist/trending"


@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=run_schedule)
    thread.start()
    yield
    schedule.clear()


# app
app = FastAPI(lifespan=lifespan)
# 静态资源
app.mount("/trending", StaticFiles(directory=TRENDING_DIR), name="trending")


@app.get("/", response_class=HTMLResponse)
def root():
    return HTMLResponse(content=open(f"{DIST_DIR}/index.html").read(), status_code=200)


class TrendingItem(BaseModel):
    title: str
    link: str
    desc: str
    star: str
    fork: str
    lang: str
    today_star: str


def mapping_text(item: TrendingItem, keyword: str) -> Union[TrendingItem, None]:
    if item["title"] and keyword.lower() in item["title"].lower():
        return item
    if item["desc"] and keyword.lower() in item["desc"].lower():
        return item
    return None


def generate_result(keyword: str):
    if keyword == "" or keyword is None:
        yield "event:done\n\n"
    title_set: set[str] = set()
    files = os.listdir(TRENDING_DIR)
    for file in files:
        with open(f"{TRENDING_DIR}/{file}", "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                if item["title"] in title_set:
                    continue
                title_set.add(item["title"])
                if mapping_text(item, keyword):
                    yield f"event:data\n"
                    yield f"data:{json.dumps(item)}\n\n"
    yield "event:done\n"
    yield "data:\n\n"


@app.get("/search")
def search(keyword: str, response: Response):
    # 设置响应头
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    response.headers["Connection"] = "keep-alive"
    return StreamingResponse(generate_result(keyword), media_type="text/event-stream")


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
        desc = "" if desc_element is None else desc_element.text
        wrapper = row.find(".Box-row>div:last-child>a")
        star = wrapper[0].text
        fork = wrapper[1].text
        lang_wrapper = row.find(".Box-row>div .repo-language-color+span", first=True)
        lang = "" if lang_wrapper is None else lang_wrapper.text
        today_star = row.find(".Box-row>div:last-child>span:last-child", first=True).text
        projects.append({
            "title": title,
            "link": link,
            "desc": desc,
            "star": star,
            "fork": fork,
            "lang": lang,
            "today_star": today_star.split(" ")[0]
        })
    # 写入文件
    path = f"{TRENDING_DIR}/{datetime.now().strftime(format='%Y-%m-%d')}.json"
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
        with open(f"{DIST_DIR}/index.html", "w", encoding="utf-8") as fw:
            # 日期渲染列表
            date_list = sorted([date.split('.')[0] for date in os.listdir(TRENDING_DIR)],
                               key=lambda x: datetime.strptime(x, '%Y-%m-%d'), reverse=True)
            date_div_list = [f'<div class="item">{date}</div>' for date in date_list]
            fw.write(Template(data).safe_substitute(date_div_list=''.join(date_div_list)))


# 任务调度
def run_schedule():
    schedule.every().day.at(EXEC_TIME).do(retry, n=MAX_RETRY, func=task).run()
    while True:
        schedule.run_pending()
        time.sleep(1)
