# Twitter 100KOL Scraper

**This README includes both English and 中文 versions.**  
**Click to jump to: [English Version](#english-version) | [中文说明](#中文说明)**

---

## English Version

### Overview

**Twitter 100KOL Scraper** is an automated script built with Python + Selenium to extract the top 100 KOL (Key Opinion Leader) handles based on hashtags and minimum likes, and retrieve their follower count by visiting their Twitter profiles.

### Features

- Log in with exported Twitter cookies
- Search tweets based on hashtags and min_faves condition
- Automatically scroll and collect top 100 unique @handles
- Visit each profile to extract followers count
- Output as structured Pandas DataFrame

### Requirements

- Python 3.x
- `selenium`
- `pandas`
- Google Chrome
- Compatible `chromedriver`

Install dependencies:

```bash
pip install selenium pandas
```

[Download ChromeDriver](https://googlechromelabs.github.io/chrome-for-testing/)

### How to Use

1. **Export Twitter login cookies** using browser extension like *Cookie Editor* and save them to a file named `twitter_cache.json`.

2. **Run the script** to fetch top KOLs in a hashtag category:

```python
from Twitter_100KOL import fetch_category_kol

df = fetch_category_kol(
    cookie_path="twitter_cache.json",
    hashtag_query="#drone OR #DJI OR #quadcopter",
    min_faves=500,
    max_scrolls=20,
    category="Smart Drones",
    webdriver_path="chromedriver.exe",
    headless=True
)
```

3. **Inspect the result**:

```python
print(df.head())
```

### Output

A DataFrame like:

| id           | profile_url                      | followers | category      |
|--------------|----------------------------------|-----------|----------------|
| example  | https://twitter.com/example  | 12345     | Sample Topic   |
| abc_user     | https://twitter.com/abc_user     | 67890     | Sample Topic   |

### Notes

- Random sleep is used to simulate human behavior.
- The script quits early if no new handles are found.
- Make sure cookies are valid and Twitter account is logged in.
- **For research or educational use only. Use responsibly.**

---

## 中文说明

### 简介

**Twitter 100KOL Scraper** 是一个基于 Python + Selenium 的自动化脚本，按关键词和最低点赞数爬取 Twitter 上最具影响力的 100 位 KOL，并访问其主页获取粉丝数。

### 功能

- 通过导入浏览器 Cookie 实现自动登录
- 根据 hashtag + 最低点赞数搜索推文
- 自动滚动页面，采集最多 100 个不重复的作者 @handle
- 访问作者主页提取粉丝数
- 以 Pandas DataFrame 形式返回结构化数据

### 环境依赖

- Python 3.x
- `selenium`
- `pandas`
- Chrome 浏览器
- 与 Chrome 版本匹配的 ChromeDriver

安装依赖：

```bash
pip install selenium pandas
```

[ChromeDriver 下载](https://googlechromelabs.github.io/chrome-for-testing/)

### 使用方法

1. **使用 Cookie 插件导出 Twitter 登录 Cookie**，保存为 `twitter_cache.json` 文件。

2. **运行脚本获取某一领域的 KOL**：

```python
from Twitter_100KOL import fetch_category_kol

df = fetch_category_kol(
    cookie_path="twitter_cache.json",
    hashtag_query="#drone OR #DJI OR #quadcopter",
    min_faves=500,
    max_scrolls=20,
    category="智能无人机",
    webdriver_path="chromedriver.exe",
    headless=True
)
```

3. **查看输出结果**：

```python
print(df.head())
```

### 输出格式示例
| id           | profile_url                      | followers | category      |
|--------------|----------------------------------|-----------|----------------|
| example  | https://twitter.com/example  | 12345     | Sample Topic   |
| abc_user     | https://twitter.com/abc_user     | 67890     | Sample Topic   |


### 注意事项

- 使用随机延迟模拟人类行为，降低被 Twitter 检测为脚本的风险；
- 若连续多轮未获取新 handle，将提前结束任务；
- 确保导入的 Cookie 有效，能维持登录状态；
- **本脚本仅供学习研究使用，请合理合规使用。**

---
