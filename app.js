const express = require('express');
const axios = require('axios');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// 开启跨域访问支持
app.use(cors());
app.use(express.json());

// 上游接码平台根地址
const BASE_UPSTREAM_URL = 'https://www.jm111.cc';

/**
 * 核心请求安全中转器
 * 自动透传客户端参数，并优雅处理上游的文本或 JSON 返回
 */
async function forwardToUpstream(req, res, path) {
    const params = req.query;
    try {
        const response = await axios.get(`${BASE_UPSTREAM_URL}${path}`, { 
            params, 
            timeout: 12000 // 12秒超时保护
        });
        
        // 直接透传上游返回的结果（无论是 JSON 对象还是像 SUCCESS|phone|taskid 的字符串）
        return res.send(response.data);
    } catch (error) {
        console.error(`[C&M Backend] 中转 ${path} 发生通讯错误:`, error.message);
        return res.status(500).json({ 
            status: "error", 
            message: `服务器代理中转失败: ${error.message}` 
        });
    }
}

// 1. 网站首页欢迎提示
app.get('/', (req, res) => {
    res.send(`
        <div style="font-family: 'Segoe UI', Arial, sans-serif; text-align: center; margin-top: 10%;">
            <h1 style="color: #2c3e50; font-size: 2.5em;">Cartier & Miller API 服务端</h1>
            <p style="color: #27ae60; font-size: 1.2em; font-weight: bold;">✓ 已成功在 Render 容器中运行！</p>
            <p style="color: #7f8c8d;">您的专属域名 cartiermiller.ccwu.cc 已成功跑通中转代理网关。</p>
        </div>
    `);
});

// 2. 核心 API 中转路由组（无缝对应你 Python 客户端里 JmSMSClient 的各个底层接口）
app.get('/api/getnumber', (req, res) => forwardToUpstream(req, res, '/api/getnumber'));
app.get('/api/getcode', (req, res) => forwardToUpstream(req, res, '/api/getcode'));
app.get('/api/releasenumber', (req, res) => forwardToUpstream(req, res, '/api/releasenumber'));
app.get('/api/pendingorders', (req, res) => forwardToUpstream(req, res, '/api/pendingorders'));
app.get('/api/successfulorders', (req, res) => forwardToUpstream(req, res, '/api/successfulorders'));

// 3. 监听端口启动服务
app.listen(PORT, () => {
    console.log(`[Cartier & Miller] 服务已成功在端口 ${PORT} 上启动...`);
});
