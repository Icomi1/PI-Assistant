# 树莓派视觉对话系统

这是一个基于树莓派的视觉对话系统，可以通过摄像头捕获画面，通过麦克风进行语音输入，并通过扬声器进行语音输出。

## 硬件要求

- 树莓派（任何型号）
- USB摄像头
- USB麦克风
- USB扬声器
- SD卡

## 软件依赖

- Python 3.7+
- 见 requirements.txt 文件

## 安装步骤

1. 将SD卡插入电脑，使用树莓派镜像烧录工具（如Raspberry Pi Imager）烧录最新的Raspberry Pi OS
2. 将SD卡插入树莓派，连接电源启动
3. 连接USB摄像头、麦克风和扬声器
4. 克隆此仓库到树莓派
5. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

运行主程序：
```bash
python main.py
```

## 注意事项

- 确保树莓派已连接到网络
- 确保所有USB设备正确连接并被系统识别
- 首次运行时可能需要配置音频设备 