# 运行db容器
docker run -d \
  --name bluecrystal\
  -e POSTGRES_USER=${BLUECRYSTAL_USERNAME} \
  -e POSTGRES_PASSWORD=${BLUECRYSTAL_PASSWORD} \
  -p 5432:5432 \
  -e POSTGRES_DB=whale \
  --restart always \
  postgres:latest

# 初始化数据库
alembic -c alembic.ini revision --autogenerate -m "init whale schema"
alembic -c alembic.ini upgrade head