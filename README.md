# github热榜归档

## 运行

```shell
# 打包镜像
docker build -t . github-trending
# 运行镜像
docker run -d \
  --name github-trending \
  -v $HOME/dockerdata/trending:/app/trending \
  -v /etc/timezone:/etc/timezone:ro \
  -v /etc/localtime:/etc/localtime:ro \
  -e EXEC_TIME="08:00" \
  -e MAX_RETRY=10 \
  github-trending
```