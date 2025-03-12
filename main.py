import cv2
import numpy as np
import speech_recognition as sr
import pyttsx3
import requests
from PIL import Image
import io
import time
import json
import os
from aip import AipSpeech

class VisualDialogSystem:
    def __init__(self):
        # 百度语音识别配置
        self.APP_ID = '117953438'
        self.API_KEY = 'bo6eeRyNlCAZOVDMGKLnJmli'
        self.SECRET_KEY = '7s1bcKj4LCnkYUNhVUrXufWKoQd56ATC'
        self.client = AipSpeech(self.APP_ID, self.API_KEY, self.SECRET_KEY)
        
        # 添加请求控制
        self.last_request_time = 0
        self.min_request_interval = 5  # 增加到5秒
        self.max_retries = 3
        self.base_wait_time = 2  # 基础等待时间（秒）
        
        # 初始化音频设备
        self.init_audio_device()
        
        # 尝试不同的摄像头设备
        for i in range(10, 19):  # 尝试video10到video18
            self.camera = cv2.VideoCapture(i)
            if self.camera.isOpened():
                print(f"成功打开摄像头 /dev/video{i}")
                break
        
        if not self.camera.isOpened():
            raise Exception("无法打开摄像头")
        
        # 设置摄像头分辨率
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # 设置服务器API地址
        self.api_url = "http://47.122.125.254:5000/api/chat"  # 使用公网IP地址
        
        # 创建临时文件夹用于存储图片
        self.temp_dir = "temp_images"
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
    
    def init_audio_device(self):
        """初始化音频设备"""
        try:
            # 获取可用的音频设备列表
            import pyaudio
            p = pyaudio.PyAudio()
            device_count = p.get_device_count()
            
            print("可用的音频设备:")
            for i in range(device_count):
                device_info = p.get_device_info_by_index(i)
                print(f"设备 {i}: {device_info['name']}")
            
            # 初始化语音识别
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 4000
            self.recognizer.dynamic_energy_threshold = True
            
            # 初始化语音合成
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)
            self.engine.setProperty('volume', 0.9)
            
            p.terminate()
            
        except Exception as e:
            print(f"初始化音频设备时出错: {e}")
            raise
    
    def verify_api_credentials(self):
        """验证百度API凭据"""
        try:
            # 尝试一个简单的API调用来验证凭据
            result = self.client.asr(b'', 'wav', 16000, {
                'dev_pid': 1537,
            })
            # 如果返回 3301 或 3302，说明凭据有问题
            if result.get('err_no') in [3301, 3302]:
                print("百度API凭据无效，请检查APP_ID、API_KEY和SECRET_KEY")
                return False
            return True
        except Exception as e:
            print(f"验证API凭据时出错: {e}")
            return False
    
    def capture_image(self):
        """捕获摄像头画面并保存为临时文件"""
        ret, frame = self.camera.read()
        if not ret:
            raise Exception("无法捕获图像")
        
        # 保存图片到临时文件
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(self.temp_dir, f"capture_{timestamp}.jpg")
        cv2.imwrite(image_path, frame)
        
        return frame, image_path
    
    def listen_for_command(self):
        """监听语音命令"""
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                with sr.Microphone() as source:
                    print("正在调整噪音阈值...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    print("正在听...")
                    try:
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                        print("接收到音频，正在识别...")
                        
                        # 保存音频文件用于调试
                        with open("test_audio.wav", "wb") as f:
                            f.write(audio.get_wav_data())
                        print("已保存测试音频文件: test_audio.wav")
                        
                        # 检查API请求间隔
                        current_time = time.time()
                        if current_time - self.last_request_time < self.min_request_interval:
                            wait_time = self.min_request_interval - (current_time - self.last_request_time)
                            print(f"等待 {wait_time:.1f} 秒以遵守API调用间隔...")
                            time.sleep(wait_time)
                        
                        # 使用指数退避策略计算等待时间
                        if retry_count > 0:
                            wait_time = self.base_wait_time * (2 ** (retry_count - 1))
                            print(f"第 {retry_count + 1} 次重试，等待 {wait_time} 秒...")
                            time.sleep(wait_time)
                        
                        # 更新最后请求时间
                        self.last_request_time = time.time()
                        
                        try:
                            # 调用百度语音识别
                            result = self.client.asr(audio.get_wav_data(), 'wav', 16000, {
                                'dev_pid': 1537,
                                'format': 'wav',
                                'rate': 16000,
                                'channel': 1,
                                'cuid': f'raspberry_pi_{time.time()}',  # 添加时间戳使每个请求唯一
                            })
                            
                            print(f"识别服务返回结果: {result}")
                            
                            if result.get('err_no') == 0:
                                text = result['result'][0]
                                print(f"识别到的文字: {text}")
                                return text
                            elif result.get('err_no') == 3305:  # QPS超限错误
                                print(f"API调用频率超限，使用指数退避重试... (第 {retry_count + 1} 次重试)")
                                retry_count += 1
                                continue
                            else:
                                error_msg = result.get('err_msg', '未知错误')
                                print(f"识别失败: {error_msg}")
                                return None
                                
                        except Exception as e:
                            print(f"调用百度API时出错: {str(e)}")
                            retry_count += 1
                            continue
                            
                    except sr.WaitTimeoutError:
                        print("没有检测到语音输入")
                        return None
                    except Exception as e:
                        print(f"识别错误: {e}")
                        return None
            except Exception as e:
                print(f"麦克风初始化错误: {e}")
                retry_count += 1
                time.sleep(1)
                
        print("达到最大重试次数，无法完成语音识别")
        return None
    
    def speak(self, text):
        """通过扬声器播放语音"""
        if not text:
            return
        print(f"正在说: {text}")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"语音输出错误: {e}")
    
    def send_to_server(self, image_path, text):
        """发送图片和文字到服务器"""
        try:
            # 准备请求数据
            files = {
                'image': ('image.jpg', open(image_path, 'rb'), 'image/jpeg')
            }
            data = {
                'text': text
            }
            
            # 发送请求
            response = requests.post(self.api_url, files=files, data=data, timeout=10)
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            return result.get('text', '抱歉，服务器返回的数据格式不正确')
            
        except requests.exceptions.RequestException as e:
            print(f"发送请求到服务器时出错: {e}")
            return "抱歉，无法连接到服务器"
        except json.JSONDecodeError:
            print("服务器返回的数据格式不正确")
            return "抱歉，服务器返回的数据格式不正确"
        finally:
            # 清理临时文件
            try:
                os.remove(image_path)
            except:
                pass
    
    def cleanup(self):
        """清理资源"""
        self.camera.release()
        cv2.destroyAllWindows()
        # 清理临时文件夹
        try:
            for file in os.listdir(self.temp_dir):
                os.remove(os.path.join(self.temp_dir, file))
            os.rmdir(self.temp_dir)
        except:
            pass
    
    def run(self):
        """运行主循环"""
        print("系统启动中...")
        
        # 验证API凭据
        if not self.verify_api_credentials():
            print("API凭据验证失败，请检查配置")
            return
            
        self.speak("系统已启动，请说出您的命令")
        
        try:
            while True:
                # 监听语音命令
                command = self.listen_for_command()
                if command:
                    try:
                        # 捕获图像
                        frame, image_path = self.capture_image()
                        
                        # 发送到服务器
                        response_text = self.send_to_server(image_path, command)
                        
                        # 播放服务器返回的响应
                        self.speak(response_text)
                    except Exception as e:
                        print(f"处理命令时出错: {e}")
                        self.speak("抱歉，处理您的命令时出现错误")
                
                time.sleep(0.1)  # 短暂休眠以避免CPU过载
                
        except KeyboardInterrupt:
            print("\n程序正在退出...")
        finally:
            self.cleanup()

if __name__ == "__main__":
    try:
        system = VisualDialogSystem()
        system.run()
    except Exception as e:
        print(f"发生错误: {e}")
        input("按回车键退出...") 