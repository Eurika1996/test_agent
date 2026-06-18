#!/bin/bash
# ============================================================
# 需求文档评审 Agent - 阿里云服务器一键部署脚本
# 使用方法（在服务器上执行）：
#   bash deploy.sh
# ============================================================

set -e

echo "=============================================="
echo "  需求文档评审 Agent - 部署到阿里云服务器"
echo "=============================================="

# --- 1. 更新系统并安装 Python3 & Git & Nginx ---
echo ""
echo "[1/7] 安装系统依赖 (python3, git, nginx, virtualenv)..."

# Ubuntu/Debian 系
if command -v apt-get &> /dev/null; then
    apt-get update -y
    apt-get install -y python3 python3-pip python3-venv git nginx curl
# CentOS/RHEL/Alibaba Cloud Linux 系
elif command -v yum &> /dev/null; then
    yum install -y python3 python3-pip git nginx curl
    pip3 install --upgrade pip
fi

python3 --version

# --- 2. 拉取代码 ---
echo ""
echo "[2/7] 从 GitHub 拉取代码..."
cd /root
if [ -d "test_agent" ]; then
    echo "  代码已存在，尝试更新..."
    cd test_agent
    git pull
else
    git clone https://github.com/Eurika1996/test_agent.git
    cd test_agent
fi

# --- 3. 创建虚拟环境并安装依赖 ---
echo ""
echo "[3/7] 创建 Python 虚拟环境并安装依赖..."
cd /root/test_agent
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install flask flask-cors markdown requests python-dotenv waitress
pip install python-docx
pip install PyMuPDF
deactivate

# --- 4. 创建必要的目录 ---
echo ""
echo "[4/7] 创建日志和上传目录..."
mkdir -p /root/test_agent/uploads
mkdir -p /root/test_agent/outputs
mkdir -p /root/test_agent/logs

# --- 5. 配置 .env ---
echo ""
echo "[5/7] 配置 API Key..."
if [ ! -f "/root/test_agent/.env" ]; then
    cat > /root/test_agent/.env << 'ENVEOF'
OPENAI_API_KEY=sk-59457476cc18447da793a7a2ebd98a37
OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen-plus
LLM_PROVIDER=DashScope
ENVEOF
    echo "  已自动写入 .env 配置（使用你之前验证过的 DashScope Key）"
else
    echo "  .env 已存在，跳过写入"
fi

# --- 6. 配置 systemd 服务（开机自启 + 崩溃自动重启）---
echo ""
echo "[6/7] 配置 systemd 服务..."
cp /root/test_agent/deploy/test_agent.service /etc/systemd/system/test_agent.service
systemctl daemon-reload
systemctl enable test_agent
systemctl restart test_agent
sleep 2

# 检查服务状态
if systemctl is-active --quiet test_agent; then
    echo "  ✅ 服务启动成功"
    systemctl status test_agent --no-pager | head -10
else
    echo "  ❌ 服务启动失败，查看日志："
    journalctl -u test_agent -n 30 --no-pager
    exit 1
fi

# --- 7. 配置 Nginx 反向代理 ---
echo ""
echo "[7/7] 配置 Nginx 反向代理..."

# 备份默认配置
if [ -f "/etc/nginx/sites-enabled/default" ]; then
    mv /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/default.bak 2>/dev/null || true
fi
if [ -f "/etc/nginx/conf.d/default.conf" ]; then
    mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.bak 2>/dev/null || true
fi

# 写入新配置
cp /root/test_agent/deploy/nginx.conf /etc/nginx/conf.d/test_agent.conf
# Ubuntu 系也在 sites-enabled 放一份
if [ -d "/etc/nginx/sites-enabled" ]; then
    cp /root/test_agent/deploy/nginx.conf /etc/nginx/sites-enabled/test_agent
fi

# 测试 Nginx 配置
nginx -t
systemctl reload nginx

# --- 8. 开放防火墙端口（阿里云安全组也要放行 80 端口）---
echo ""
echo "[附加] 开放防火墙端口..."
if command -v ufw &> /dev/null; then
    ufw allow 80/tcp 2>/dev/null || true
    ufw allow 443/tcp 2>/dev/null || true
fi
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=80/tcp 2>/dev/null || true
    firewall-cmd --permanent --add-port=443/tcp 2>/dev/null || true
    firewall-cmd --reload 2>/dev/null || true
fi

# --- 完成 ---
echo ""
echo "=============================================="
echo "  ✅ 部署完成！"
echo "=============================================="
echo ""
echo "  访问地址： http://你的服务器公网IP"
echo ""
echo "  常用命令："
echo "    systemctl status test_agent    查看服务状态"
echo "    systemctl restart test_agent   重启服务"
echo "    journalctl -u test_agent -f    实时查看日志"
echo "    tail -f /root/test_agent/logs/app.log"
echo ""
echo "  拉取最新代码："
echo "    cd /root/test_agent && git pull && systemctl restart test_agent"
echo ""
echo "  ⚠️  重要：请在阿里云控制台 → 安全组 → 入方向规则 放行 80 端口"
echo ""
