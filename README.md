# 深圳大学体育场馆自动预约脚本，无需配置环境，无需账号密码

**github项目发布地址**：https://github.com/9900ff/SZU-badminton-GO

下载请点击网页右侧Releases，下载最新SZU-badminton-GO.zip后缀压缩包

## 说明

本项目是基于 [Cooduck/Ticket_grabbing_system](https://github.com/Cooduck/Ticket_grabbing_system) 修改的深圳大学自动抢羽毛球场脚本。

**本项目最大的特点是：已将Python环境、Chrome浏览器及对应驱动打包，并通过网页界面进行配置，实现了真正的“开箱即用”，无需在电脑上额外安装或配置任何环境。**

脚本包含自动登录、准时刷新、同时抢多个场地、随机优先抢场、添加同行人、体育经费支付等功能。支付是通过体育经费进行，运行前请确保体育经费充足。该脚本仅用于抢第二天的场地。

## 文件结构
```
SZU-badminton-GO/
│
├── 运行程序.bat                 <-- (【唯一运行入口】一键启动脚本)
│
└── src/
    │
    ├── main.py               <-- (脚本主程序)
    ├── web_server.py         <-- (网页配置服务)
    ├── information.txt       <-- (自动生成的配置文件)
    │
    ├── python-env/           <-- (已打包的Python环境)
    ├── chrome-win64/         <-- (已打包的Chrome浏览器)
    ├── chromedriver-win64/   <-- (已打包的Chromedriver)
    └── templates/            <-- (网页配置设置模板)
        └── index.html
```

## 更新说明

### v1.0

打包python依赖、浏览器驱动等全部依赖。无需手动配置，开箱即用

添加随机抢场功能

### v1.1

更加人性化的网页端抢票信息管理

支持手动登录，无需账号密码，确保用户隐私

### v1.2

添加了多时间段选择功能

优先同场地机制
