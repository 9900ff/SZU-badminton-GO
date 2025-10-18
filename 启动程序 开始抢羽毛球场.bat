@echo off
REM 切换控制台编码为 UTF-8 (65001)，以正确显示中文
chcp 65001

title 深圳大学场馆预约脚本
echo 正在启动Python环境，请稍候...


REM 使用相对路径调用我们打包的Python环境
REM 来执行同目录下的 main.py 脚本
cd src
.\python-env\python.exe .\main.py

echo 本项目github发布地址：https://github.com/9900ff/SZU-badminton-GO

REM 运行完毕后暂停，防止窗口闪退，方便查看日志
echo.
echo 脚本已执行完毕。


pause
exit