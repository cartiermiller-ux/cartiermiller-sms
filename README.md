Cartier & Miller 平台（cartierandmiller.ccwu.cc）部署与建站实操指南

本指南将以你的专属域名 cartiermiller.ccwu.cc 为核心，详细讲解从域名解析、服务器配置、安全防护到系统部署上线的一整套实操流程。

零、 前置步骤：GitHub 仓库创建与代码上传（基于你的截图）

在使用 Render 部署前，你需要将你的代码上传到 GitHub 仓库中。

1. 填写新建仓库表单（已完成 ✅）

你已成功创建了名为 cartiermiller-sms 的公共/私有仓库。

2. 网页端拖拽上传代码（已完成第一步 ✅）

你已经成功上传了客户端程序 cartier_and_miller_sms_platform.py。

⚠️ 如果你想把这里做成一个供用户通过浏览器访问的“发卡/接码网站”，你还需要往这个仓库里上传两个网站服务端文件：

package.json（网站配置文件，代码在右侧 upload_list.md 方案 B 中）

app.js（网站核心后端，代码在右侧 upload_list.md 方案 B 中）

上传方法：点击你当前 GitHub 页面绿色的 “添加文件 (Add file)” -> “上传文件 (Upload files)”，把这两个文件拖进去并提交保存（Commit changes）即可。

一、 第一步：在 Render 平台免费部署你的网站后端

当你的 GitHub 仓库中准备好了 package.json 和 app.js 之后，就可以开始部署了：

1. 登录 Render 并新建服务

打开并登录 Render 控制台（直接用你的 GitHub 账号授权登录）。

点击页面右上角红色的 "New +" 按钮，选择 "Web Service"。

2. 关联 GitHub 仓库

在 "Connect a repository" 列表中，找到你刚刚创建的 cartiermiller-sms 仓库。

点击右侧的 "Connect" 链接。

3. 配置部署参数

在打开的配置页面中，依次填写以下内容：

Name (服务名称)：写 cartiermiller-api。

Region (服务器地区)：选择 Singapore (新加坡) 或 Oregon (美国)（建议新加坡，国内访问稍微快一点）。

Branch (分支)：保持默认的 main。

Runtime (运行环境)：选择 Node（Render 会自动根据你上传的 package.json 识别）。

Build Command (打包命令)：输入 npm install。

Start Command (启动命令)：输入 node app.js。

Instance Type (实例类型)：拉到最下面选择 Free (免费版)。

点击最下方的 "Create Web Service"（创建服务）。等待 2~3 分钟，当你看到控制台日志输出 Your service is live! 时，说明你的网站后端已经成功发布到公网了！

4. 绑定你的专属域名 cartiermiller.ccwu.cc

在 Render 的当前服务页面，点击左侧菜单的 "Settings" (设置)。

往下拉找到 "Custom Domains" (自定义域名) 这一栏，点击 "Add Custom Domain"。

输入你的域名：cartiermiller.ccwu.cc，点击保存。

域名解析配置：
Render 会给你提供一个类似 cartiermiller-api.onrender.com 的目标地址。
你需要登录你购买域名的控制台（如腾讯云、阿里云或 Cloudflare），为你添加一条 CNAME 记录：

记录类型：CNAME

主机记录：cartiermiller

记录值：填写 Render 刚才提供给你的那个 xxxx.onrender.com 网址。

解析生效后，你就可以直接通过 https://cartiermiller.ccwu.cc 访问你的网站系统了！

二、 第二步：服务器选型与基础环境（若后续升级为独立服务器）

1. 服务器推荐

地域：选择中国香港、新加坡、日本或美国的云服务器。

配置：前期测试 1核2G 即可；正式上线推荐 2核4G、50M带宽以上。

系统：Ubuntu 22.04 LTS 或 Debian 12。

2. 简易环境搭建：宝塔面板 (BT Panel) 部署

在服务器终端运行以下命令安装宝塔：

wget -O install.sh https://download.bt.cn/install/install_lts.sh && sudo bash install.sh ed8484bec


三、 第三步：配置 Nginx 与 SSL 安全证书

在宝塔左侧菜单点击 网站 -> 添加站点，输入域名：cartiermiller.ccwu.cc。

站点创建成功后，点击站点设置 -> SSL -> 选择 Let's Encrypt 申请并开启 “强制HTTPS”。

四、 第四步：全自动 TRC20-USDT 充值网关对接

接入「易支付 + USDT 插件」：一旦检测到指定金额（比如 15.00 USDT）的账单入账，系统就会通过 Webhook 自动回调给你的网站，给对应的用户增加余额。
