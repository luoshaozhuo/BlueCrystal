"""跨模块通用工具集。

承载与具体业务域（whale / seahorse / starfish 等）无关的横切工具。当前
包含跨项目数据库连接工具（``tools.sqlalchemy_session``）；新增横切工具
时按职责归入此处，避免下沉到具体业务子包造成位置语义错位。
"""