# github热榜归档

> 将每日的github热榜归档到本地，并使用docker部署。

## 运行 BUILD & RUN

```shell
# 打包镜像
docker build -t github-trending .
# 运行镜像
docker run -d \
  --name github-trending \
  --restart unless-stopped \
  -p 8080:80 \
  -v $HOME/dockerdata/trending/data:/app/dist \
  -v /etc/timezone:/etc/timezone:ro \
  -v /etc/localtime:/etc/localtime:ro \
  -e EXEC_TIME="08:00" \
  -e MAX_RETRY=10 \
  github-trending
```

## 环境变量

```bash
# 每天几点执行，默认8点
EXEC_TIME="08:00"
# 重试次数，默认10次
MAX_RETRY=10
```

## 截图 Snapshot

![1.png](./screenshot/1.png)