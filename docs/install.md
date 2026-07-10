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

### 初始化ORM
alembic -c alembic.ini revision --autogenerate -m "init whale schema"
alembic -c alembic.ini upgrade head
### 初始化view
//注意这里不要用 --autogenerate。
//--autogenerate 主要比较 Base.metadata 里的表结构，默认不会可靠管理 view。
alembic -c alembic.ini revision -m "add whale views"
//修改新增的xxx_add_whale_views.py代码文件再执行下面的指令
alembic -c alembic.ini upgrade head

# 推荐的职责划分
Navicat
└── 人工查询、调试、检查数据库

完整 DDL
└── 创建全新数据库的当前完整结构

主数据 DML
└── 初始化系统必需的参考代码、协议、标准语义

Sample DML
└── 初始化示例场站和测试数据

Alembic
└── 已有数据库从旧版本升级到新版本

ORM
└── 根据正式数据库结构反向生成，供程序访问