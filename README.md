# 深圳大学体育场馆自动预约脚本 (绿色版)

github项目发布地址：https://github.com/9900ff/SZU-badminton-GO

## 说明

本项目是基于 [Cooduck/Ticket_grabbing_system](https://github.com/Cooduck/Ticket_grabbing_system) 修改的深圳大学自动抢羽毛球场/网球场脚本。

**本项目最大的特点是：已将Python环境、Chrome浏览器及对应驱动打包，实现了真正的“开箱即用”，无需在电脑上额外安装或配置Python/Chrome。**

脚本包含自动登录、准时刷新、随机优先抢场、添加同行人、体育经费支付等功能。支付是通过体育经费进行，运行前请确保体育经费充足。该脚本仅用于抢第二天的场地。

## 功能特性

* **开箱即用**：无需安装Python、Selenium或Chrome，下载解压后即可使用。
* **自动登录**：在抢票时间（12:30:00）前90秒（12:28:30）自动打开浏览器并登录。
* **准时刷新**：在 12:30:00 准时自动刷新页面，获取最新的场次信息。
* **随机优先**：自动按**随机顺序**抢场地，避免与其他使用脚本用户冲突。
* **完整流程**：全自动完成选择校区、球类、日期、时间、场馆、提交、支付等所有流程。

## 文件结构

```ini
Ticket\_grabbing\_system-master/
│
├── start.bat                 \<-- (【唯一运行入口】一键启动脚本)
├── 购票信息.txt           \<-- (【唯一配置入口】在此填写信息)
│
├── main.py                   \<-- (脚本python程序)
├── 启动程序 开始抢羽毛球场.bat            \<-- (脚本一键启动主程序)

├── python-env/               \<-- (已打包的Python环境)
├── chrome-win64/             \<-- (已打包的Chrome浏览器)
└── chromedriver-win64/       \<-- (已打包的Chromedriver)
```


## 运行（重要）

使用本脚本**极其简单**，仅需两步：

### 第一步：配置信息

1.  打开 `information.txt` 文件。
2.  将【快速配置区】的 **8个** 字段填写完整。
3.  **注意**：请严格按照文件下方“配置说明”中的格式和选项填写，尤其是 `venues` 和 `appointment` 字段，否则脚本会超时失败。

需要填写的字段如下：

```ini
username=
password=
campus=
ball=
appointment=
venues=
payment_password=
companions_id=
````

### 第二步：一键启动

1.  在抢票当天 12:30:00 之前（建议提前几分钟）。
2.  **双击 `start.bat`** 运行脚本。
3.  脚本会先加载配置，然后在 12:28:30 自动打开浏览器并登录。
4.  在 12:30:00 准时开始抢票。
5.  抢票成功会显示“预约并支付成功”。

## 致谢

  * 本项目修改自 [Cooduck/Ticket\_grabbing\_system](https://github.com/Cooduck/Ticket_grabbing_system)，在此基础上实现了环境打包和抢票逻辑优化。
