"""
Robstride Python SDK - Quick Start Guide
========================================

这是一个完整的Robstride电机Python SDK，基于官方CAN协议规范开发。
SDK提供了简单易用的API来控制Robstride电机的所有功能。

## 安装和设置

1. 安装依赖:
   ```bash
   cd robstride-sdk
   pip install -r requirements.txt
   ```

2. 安装SDK (可选):
   ```bash
   pip install -e .
   ```

## 基础使用

### 1. 连接电机
```python
import robstride

# 使用SocketCAN (Linux)
motor = robstride.create_motor_from_can_interface(
    motor_id=1, 
    interface='socketcan', 
    channel='can0'
)

# 或使用PCAN (Windows/Linux)
motor = robstride.create_motor_from_can_interface(
    motor_id=1, 
    interface='pcan', 
    channel='PCAN_USBBUS1'
)
```

### 2. 基本控制
```python
# 使能电机
motor.enable()

# 运控模式 - 最灵活的控制方式
motor.set_motion_control(
    pos=1.0,      # 目标位置 (弧度)
    vel=0.0,      # 目标速度 (弧度/秒)
    kp=50.0,      # 位置增益
    kd=1.0,       # 阻尼增益
    torque=0.0    # 前馈力矩 (牛米)
)

# 获取状态
status = motor.get_status()
print(f"位置: {status['position']:.3f} rad")
print(f"速度: {status['velocity']:.3f} rad/s")
print(f"力矩: {status['torque']:.3f} Nm")

# 停止电机
motor.disable()
motor.close()
```

## 控制模式

### 1. 运控模式 (默认, 最推荐)
```python
# 位置控制 - 弹簧效果
motor.set_motion_control(pos=1.0, vel=0.0, kp=50.0, kd=1.0, torque=0.0)

# 速度控制
motor.set_motion_control(pos=0.0, vel=2.0, kp=0.0, kd=1.0, torque=0.0)

# 阻尼控制 - 抵抗运动
motor.set_motion_control(pos=0.0, vel=0.0, kp=0.0, kd=2.0, torque=0.0)

# 力矩控制
motor.set_motion_control(pos=0.0, vel=0.0, kp=0.0, kd=0.0, torque=1.0)
```

### 2. 其他控制模式
```python
# 电流模式
motor.set_run_mode(robstride.RUN_MODE_CURRENT)
motor.enable()
motor.set_current_reference(2.0)  # 2安培

# 速度模式
motor.set_run_mode(robstride.RUN_MODE_VELOCITY)
motor.set_current_limit(5.0)
motor.enable()
motor.set_velocity_reference(3.0)  # 3弧度/秒

# 位置模式 (CSP)
motor.set_run_mode(robstride.RUN_MODE_POSITION_CSP)
motor.set_velocity_limit(10.0)
motor.set_current_limit(3.0)
motor.enable()
motor.set_position_reference(1.5)  # 1.5弧度
```

## 示例程序

SDK包含三个完整的示例程序：

1. `examples/01_enable_and_disable.py` - 基础连接和状态读取
2. `examples/02_motion_control.py` - 运控模式的详细演示
3. `examples/03_read_write_params.py` - 参数管理和模式切换

运行示例：
```bash
cd examples
python 01_enable_and_disable.py
```

## CAN接口配置

### Linux SocketCAN
```bash
sudo ip link set can0 type can bitrate 1000000
sudo ip link set up can0
```

### Windows PCAN
安装PCAN驱动，然后直接使用通道名如 'PCAN_USBBUS1'

## 常用功能

### 参数读写
```python
# 读取参数
kp_value = motor.read_parameter(robstride.PARAM_LOC_KP)

# 写入参数
motor.set_position_kp(30.0)

# 保存到Flash (断电后保持)
motor.save_configuration()
```

### 错误处理
```python
try:
    motor.enable()
    motor.set_motion_control(1.0, 0.0, 50.0, 1.0, 0.0)
except robstride.ConnectionError:
    print("CAN通信失败")
except robstride.TimeoutException:
    print("电机无响应")
except robstride.MotorFaultException as e:
    print(f"电机故障: 0x{e.fault_code:08X}")
```

### 状态监控
```python
def status_callback(status):
    print(f"电机位置: {status['position']:.3f} rad")

motor.set_status_callback(status_callback)
motor.set_active_reporting(True)  # 启用10ms状态上报
```

## 协议支持

SDK完整实现了Robstride CAN协议规范：
- 支持所有通信类型 (0-25)
- 扩展CAN帧 (29位ID) 1Mbps波特率
- 自动数据转换和错误处理
- 线程安全的异步通信

## 故障排除

1. **连接失败**:
   - 检查CAN接口是否正确配置
   - 确认电机已上电
   - 验证CAN总线连接

2. **无状态反馈**:
   - 检查电机ID是否正确
   - 确认电机已使能
   - 增加超时时间

3. **命令无效果**:
   - 检查电机是否在正确模式
   - 确认参数范围正确
   - 查看错误码

## 技术规格

- Python 3.7+
- python-can >= 4.0.0
- 支持所有python-can兼容的CAN接口
- 线程安全，支持多电机控制
- 完整的类型注解和文档

## 开发和测试

运行测试：
```bash
python -m pytest tests/ -v
```

检查协议实现：
```bash
python tests/test_protocol.py
```

---

这个SDK提供了Robstride电机控制的完整解决方案，从底层CAN协议到高层应用接口，
让您可以专注于机器人应用逻辑而不是通信细节。
"""
