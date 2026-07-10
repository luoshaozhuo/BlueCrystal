# 安装whale
pip uninstall -y bluecrystal
pip install -e /home/luosh/BlueCrystal
pip show bluecrystal

# 运行db容器
docker run -d \
  --name bluecrystal\
  -e POSTGRES_USER=${BLUECRYSTAL_USERNAME} \
  -e POSTGRES_PASSWORD=${BLUECRYSTAL_PASSWORD} \
  -p 5432:5432 \
  -e POSTGRES_DB=whale \
  --restart always \
  postgres:latest

# 数据库管理
## navicat删除数据库
REVOKE CONNECT ON DATABASE whale FROM PUBLIC;

SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'whale';

DROP DATABASE whale;

## 初始化
mkdir -p src/whale/shared/persistence/orm
touch src/whale/shared/persistence/orm/__init__.py

python -m sqlacodegen \
  "$WHALE_DB_URL" \
  --schema whale \
  --outfile src/whale/shared/persistence/orm/models.py

### 初始化ORM
alembic -c alembic.ini revision --autogenerate -m "init whale schema"
alembic -c alembic.ini upgrade head
### 初始化view
//注意这里不要用 --autogenerate。
//--autogenerate 主要比较 Base.metadata 里的表结构，默认不会可靠管理 view。
alembic -c alembic.ini revision -m "add whale views"
//修改新增的xxx_add_whale_views.py代码文件再执行下面的指令
alembic -c alembic.ini upgrade head

# 职责划分

现有 DDL
→ 创建数据库
→ 生成一次 ORM
→ 建立 Alembic baseline
→ 从此以后 ORM + Alembic 为唯一演进入口