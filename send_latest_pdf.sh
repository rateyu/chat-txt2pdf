#!/bin/bash

# 脚本功能：生成最新的PDF文件并通过邮件发送
# 作者：Claude Code
# 日期：2025-12-17

set -e  # 遇到错误立即退出

echo "================================================"
echo "步骤 1: 运行 export-txt2pdf2.py 生成PDF文件..."
echo "================================================"

# 运行PDF生成脚本
python export-txt2pdf2.py

# 检查是否成功生成PDF
if [ $? -ne 0 ]; then
    echo "❌ PDF生成失败，退出脚本"
    exit 1
fi

echo ""
echo "================================================"
echo "步骤 2: 查找最新生成的PDF文件..."
echo "================================================"

# 查找最新的 chat_ebook_*.pdf 文件（按修改时间排序）
LATEST_PDF=$(ls -t chat_ebook_*.pdf 2>/dev/null | head -n 1)

# 检查是否找到PDF文件
if [ -z "$LATEST_PDF" ]; then
    echo "❌ 未找到任何 chat_ebook_*.pdf 文件"
    exit 1
fi

echo "✓ 找到最新PDF文件: $LATEST_PDF"
echo "  文件大小: $(ls -lh "$LATEST_PDF" | awk '{print $5}')"
echo "  修改时间: $(ls -l "$LATEST_PDF" | awk '{print $6, $7, $8}')"

echo ""
echo "================================================"
echo "步骤 3: 发送邮件到 y81212@icloud.com ..."
echo "================================================"

# 使用 mymail.py 发送邮件
~/mymail.py -f "$LATEST_PDF" \
    -t y81212@icloud.com \
    -s "Chat对话PDF导出" \
    -c "您好，这是最新生成的对话记录PDF文件：$LATEST_PDF，请查收！"

# 检查邮件发送结果
if [ $? -eq 0 ]; then
    echo ""
    echo "================================================"
    echo "✓ 全部完成！PDF已成功发送到邮箱"
    echo "================================================"
else
    echo ""
    echo "================================================"
    echo "❌ 邮件发送失败"
    echo "================================================"
    exit 1
fi
