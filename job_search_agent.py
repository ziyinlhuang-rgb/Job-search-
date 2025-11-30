import os
import json
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import anthropic
import schedule
import time

# 配置

CONFIG = {
“job_titles”: [“Contract Manager”, “Category Manager”, “Buyer”, “Procurement Manager”],
“locations”: [“Singapore”, “Dubai”],
“your_email”: “Ziyi.nl.huang@gmail.com”,
“smtp_server”: “smtp.gmail.com”,
“smtp_port”: 587,
“gmail_password”: “iopjklbnm”,
“max_experience”: 8,  # 最多经验年数
“languages”: [“English”, “Chinese”],
“sponsorship_required”: True,  # 需要公司 sponsor 签证
}

def search_jobs_with_claude(location, job_title):
“”“使用 Claude 搜索职位”””
client = anthropic.Anthropic(api_key=os.environ.get(“ANTHROPIC_API_KEY”))

```
search_queries = [
    f"{job_title} jobs in {location} visa sponsorship",
    f"{job_title} {location} hiring relocation",
    f"{job_title} vacancy {location} English",
]

all_jobs = []

for query in search_queries:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        tools=[
            {
                "type": "web_search",
                "name": "web_search"
            }
        ],
        messages=[
            {
                "role": "user",
                "content": f"""搜索职位: {query}
```

请找出所有列出的职位，包括:

1. 职位名称
1. 公司名称
1. 地点
1. 职位描述 (工作内容和要求)
1. 经验要求 (年数)
1. 签证支持信息 (visa sponsorship, relocation等)
1. 语言要求
1. 申请链接

返回尽可能完整的职位信息。”””
}
]
)

```
    for block in response.content:
        if hasattr(block, 'text'):
            all_jobs.append(block.text)

return all_jobs
```

def filter_jobs(jobs_data):
“”“筛选符合条件的职位”””
client = anthropic.Anthropic(api_key=os.environ.get(“ANTHROPIC_API_KEY”))

```
jobs_text = "\n".join(jobs_data) if isinstance(jobs_data, list) else jobs_data

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=3000,
    messages=[
        {
            "role": "user",
            "content": f"""分析这些职位信息，严格筛选符合条件的职位:
```

职位信息:
{jobs_text}

筛选标准 (MUST MATCH ALL):

1. 职位类型: Contract Manager, Category Manager, Buyer, Procurement Manager
1. 地点: Singapore 或 Dubai
1. 经验要求: 不超过 8 年 (如果说 “8+ years” 或更高就排除)
1. 语言: 包括 English (中文加分但非必需)
1. 签证支持: MUST 明确提到公司 sponsor 签证、visa sponsorship、work permit support 或 relocation 支持
- 排除标准: “自己准备签证”、“only candidates with visa”、“self-sponsored”、“no sponsorship”
1. 只返回完整信息的职位 (公司名、职位名、链接、明确的经验和签证信息)

IMPORTANT: 只返回明确说明公司会 sponsor 签证的职位。如果签证信息不明确，排除掉。

返回 JSON 格式:
{{
“jobs”: [
{{
“title”: “职位名称”,
“company”: “公司名”,
“location”: “地点”,
“experience_required”: “经验年数”,
“description”: “职位描述 (100字以内)”,
“visa_sponsorship”: “签证支持情况”,
“languages”: “语言要求”,
“link”: “申请链接”
}}
]
}}

如果没有符合所有条件的职位，返回空数组。”””
}
]
)

```
try:
    result_text = response.content[0].text
    # 提取 JSON
    start_idx = result_text.find('{')
    end_idx = result_text.rfind('}') + 1
    if start_idx != -1 and end_idx > start_idx:
        json_str = result_text[start_idx:end_idx]
        return json.loads(json_str)
except (json.JSONDecodeError, IndexError) as e:
    print(f"JSON 解析错误: {e}")

return {"jobs": []}
```

def send_email(filtered_jobs):
“”“发送邮件”””
if not filtered_jobs.get(“jobs”):
print(“❌ 没有找到符合条件的职位”)
return False

```
# 构建邮件内容
email_body = f"""<html><body style="font-family: Arial, sans-serif;">
```

<h2>📋 职位搜索结果 - {datetime.now().strftime('%Y年%m月%d日')}</h2>
<p>找到 <strong>{len(filtered_jobs['jobs'])} 个</strong> 符合条件的职位（新加坡 + 迪拜）</p>
<hr>
<table border="1" cellpadding="12" style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #2c3e50; color: white;">
<th>职位</th>
<th>公司</th>
<th>地点</th>
<th>经验</th>
<th>签证支持</th>
<th>语言</th>
<th>申请</th>
</tr>
"""

```
for job in filtered_jobs['jobs']:
    email_body += f"""<tr>
```

<td><strong>{job.get('title', 'N/A')}</strong></td>
<td>{job.get('company', 'N/A')}</td>
<td>{job.get('location', 'N/A')}</td>
<td>{job.get('experience_required', 'N/A')}</td>
<td style="color: green;"><strong>{job.get('visa_sponsorship', 'N/A')}</strong></td>
<td>{job.get('languages', 'N/A')}</td>
<td><a href="{job.get('link', '#')}" style="background-color: #3498db; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">申请</a></td>
</tr>
<tr style="background-color: #ecf0f1;">
<td colspan="7">{job.get('description', 'N/A')}</td>
</tr>
"""

```
email_body += """</table>
```

<hr>
<p style="color: #7f8c8d; font-size: 12px;">这是自动发送的每周职位搜索结果。祝你好运！</p>
</body></html>"""

```
# 发送邮件
try:
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🔍 职位搜索结果 - {datetime.now().strftime('%Y年%m月%d日')} ({len(filtered_jobs['jobs'])} 个职位)"
    msg['From'] = CONFIG['your_email']
    msg['To'] = CONFIG['your_email']
    
    msg.attach(MIMEText(email_body, 'html'))
    
    with smtplib.SMTP(CONFIG['smtp_server'], CONFIG['smtp_port']) as server:
        server.starttls()
        server.login(CONFIG['your_email'], CONFIG['gmail_password'])
        server.send_message(msg)
    
    print(f"✅ 邮件已发送，包含 {len(filtered_jobs['jobs'])} 个职位")
    return True
except Exception as e:
    print(f"❌ 邮件发送失败: {e}")
    return False
```

def run_job_search_agent():
“”“主搜索程序”””
print(f”\n🔍 开始搜索职位 ({datetime.now().strftime(’%Y-%m-%d %H:%M:%S’)})”)
print(f”搜索条件: 经验≤{CONFIG[‘max_experience’]}年, 需要签证赞助, 地点: {’, ’.join(CONFIG[‘locations’])}”)

```
all_jobs = []
for location in CONFIG['locations']:
    for job_title in CONFIG['job_titles']:
        print(f"  搜索: {job_title} in {location}")
        jobs = search_jobs_with_claude(location, job_title)
        all_jobs.extend(jobs)

print("\n📊 筛选职位...")
filtered_jobs = filter_jobs(all_jobs)

print(f"✓ 找到 {len(filtered_jobs['jobs'])} 个符合条件的职位")

if filtered_jobs['jobs']:
    print("\n📧 发送邮件...")
    send_email(filtered_jobs)

return filtered_jobs
```

def schedule_weekly_search():
“”“每周一早上 8 点运行搜索”””
schedule.every().monday.at(“08:00”).do(run_job_search_agent)

```
print("⏰ 定时任务已设置：每周一早上 8 点")
print("按 Ctrl+C 停止运行\n")

while True:
    schedule.run_pending()
    time.sleep(60)
```

if **name** == “**main**”:
import sys

```
if len(sys.argv) > 1 and sys.argv[1] == "once":
    # 运行一次搜索
    results = run_job_search_agent()
else:
    # 定时运行
    schedule_weekly_search()
```
