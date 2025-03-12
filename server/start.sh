#!/bin/bash

# 激活虚拟环境（如果使用虚拟环境）
# source venv/bin/activate

# 使用gunicorn启动服务
gunicorn -w 4 -b 0.0.0.0:5000 app:app 