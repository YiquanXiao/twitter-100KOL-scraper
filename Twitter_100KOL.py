import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options  # for change chrome setting 
from selenium.webdriver.chrome.service import Service  # for manage chromedriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import json
import urllib.parse


def random_sleep(min_sec=1.0, max_sec=3.0):
    """
    在 min_sec 到 max_sec 之间随机 sleep 一段时间。
    用于模拟人类行为，避免被检测为自动脚本。
    """
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def get_chromedriver(webdriver_path="chromedriver.exe", disable_logging=True, headless=False):
    """
    启动 Chrome 浏览器的 WebDriver。

    Args:
        webdriver_path (str, optional): 需要指定 chromedriver.exe 的路径。
            Defaults to "chromedriver.exe"
        disable_logging (bool, optional): 是否禁用 Chrome 的日志输出。
            Defaults to True.
        headless (bool, optional): 是否以无头模式运行 Chrome。（即不显示浏览器界面）
            Defaults to False.

    Returns:
        _type_: _description_
    """
    options = Options()
    if disable_logging:
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # options.add_argument('--log-level=3')  # Suppress all logs
    if headless:
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920x1080')
    wd = webdriver.Chrome(service=Service(webdriver_path), options=options)
    return wd


def get_top_handles(cookie_path: str,
                    hashtag_query: str,
                    min_faves: int,
                    max_scrolls: int, 
                    headless: bool = False) -> list:
    """
    使用 Selenium 在 Twitter 上按 hashtag + 最低点赞数检索推文，并滚动加载直到收集到 100 个不同作者 @handle。

    参数:
      - cookie_path: Chrome Cookie Editor 导出的 JSON 文件路径
      - hashtag_query: 例如 "#drone OR #DJI OR #quadcopter"
      - min_faves: 最低点赞数，如 200
      - max_scrolls: 最多滚动次数
      - headless: 是否以无头模式运行

    返回:
      - handles: 最多 100 个作者 @handle 的列表
    """
    # 1. 启动浏览器
    driver = get_chromedriver(
        webdriver_path="chromedriver.exe",
        disable_logging=True,
        headless=headless
    )
    
    try:
        # 2. 加载 Twitter，注入 Cookie 以保持登录态
        driver.get("https://twitter.com/")
        random_sleep()  # 等待页面初始化
        
        with open(cookie_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        
        # 清洗 Cookie 数据
        # Twitter 的 Cookie 中有些值为 None 或 "no_restriction"，需要转换为合法值
        for c in cookies:
            # 将 "no_restriction" 或 None 转换为合法值
            if c.get("sameSite") not in ["Strict", "Lax", "None"]:
                c["sameSite"] = "None"
            # Selenium 不接受 null，需要删除这些键
            for key in list(c.keys()):
                if c[key] is None:
                    del c[key]
            
        for ck in cookies:
            driver.add_cookie(ck)
        
        # 3. 构造搜索 URL 并打开
        query = f"({hashtag_query}) min_faves:{min_faves}"
        url = "https://twitter.com/search?q=" + urllib.parse.quote(query)
        driver.get(url)
        random_sleep()
        
        # 4. 循环滚动加载，提取作者
        handles = set()
        scrolls = 0
        last_count = 0
        
        while len(handles) < 100 and scrolls < max_scrolls:
            # 滚动次数
            if scrolls % 10 == 0 and scrolls > 0:
                print(f"已滚动 {scrolls} 次，当前收集到 {len(handles)} 个作者 @handle")
                random_sleep(200,300)
            
            # 滚动到底部
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            random_sleep(3, 5)
            
            # 等待至少一个推文出现（可根据实际页面调整 selector）
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//article[@data-testid='tweet']"))
            )
            
            tweets = driver.find_elements(By.XPATH, "//article[@data-testid='tweet']")
            for tweet in tweets:
                try:
                    # 定位作者 @handle
                    handle_elem = tweet.find_element(
                        By.XPATH,
                        ".//div[@data-testid='User-Name']//span[contains(text(), '@')]"
                    )
                    handle = handle_elem.text.lstrip('@')
                    handles.add(handle)
                except:
                    continue
        
            # 若本轮无新增，则提前退出
            if len(handles) == last_count:
                break
            
            last_count = len(handles)
            scrolls += 1
        
        # 5. 返回前 100 个
        random_sleep(1.5, 3.5)
        return list(handles)[:100]
    
    finally:
        driver.quit()


def get_kol_details(handles: list,
                    category: str,
                    cookie_path: str,
                    webdriver_path: str = "chromedriver.exe",
                    headless: bool = False,
                    max_wait: int = 10) -> pd.DataFrame:
    """
    通过 Selenium RPA 方式，打开每个 KOL 主页并提取粉丝量，
    最后返回包含 id, profile_url, followers, category 的 DataFrame。

    参数:
      - handles: KOL @handle 列表（如 ['drone_master', 'tech_guru', ...]）
      - category: 该批 KOL 对应的品类名称（string）
      - cookie_path: 导出 cookie 的 JSON 文件路径
      - webdriver_path: ChromeDriver 可执行文件路径
      - headless: 是否以无头模式运行
      - max_wait: 单个页面等待元素加载的最长秒数

    返回:
      - df: Pandas DataFrame，列名 ['id', 'profile_url', 'followers', 'category']
    """
    # 1. 启动浏览器
    driver = get_chromedriver(webdriver_path=webdriver_path,
                              disable_logging=True,
                              headless=headless)

    # 注入 cookies 保持登录态
    driver.get("https://twitter.com/")
    random_sleep()  # 等待页面初始化
    
    with open(cookie_path, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    
    # 清洗 Cookie 数据
    # Twitter 的 Cookie 中有些值为 None 或 "no_restriction"，需要转换为合法值
    for c in cookies:
        # 将 "no_restriction" 或 None 转换为合法值
        if c.get("sameSite") not in ["Strict", "Lax", "None"]:
            c["sameSite"] = "None"
        # Selenium 不接受 null，需要删除这些键
        for key in list(c.keys()):
            if c[key] is None:
                del c[key]
        
    for ck in cookies:
        driver.add_cookie(ck)
    
    
    records = []
    try:
        for index, handle in enumerate(handles):
            # 每几个 KOL 休眠一段时间，避免过快请求
            if index % 10 == 0 and index > 0:
                print(f"已处理 {index} 个 KOL @handle")
                random_sleep(200, 300)
            
            profile_url = f"https://twitter.com/{handle}"
            driver.get(profile_url)
            # 等待“粉丝”数字加载
            try:
                followers_elem = WebDriverWait(driver, max_wait).until(
                    EC.presence_of_element_located(
                        (By.XPATH,
                         "//a[contains(@href, '/verified_followers')]/span[1]/span")
                    )
                )
                raw = followers_elem.text  # 例如 '12.3K' 或 '987'
            except Exception:
                # 若提取失败，设置为 None
                raw = None

            # 转换为整数
            if raw:
                if raw.endswith('K'):
                    followers = int(float(raw[:-1]) * 1_000)
                elif raw.endswith('M'):
                    followers = int(float(raw[:-1]) * 1_000_000)
                else:
                    followers = int(raw.replace(',', ''))
            else:
                followers = None

            records.append({
                "id": handle,
                "profile_url": profile_url,
                "followers": followers,
                "category": category
            })
            
            random_sleep()

    finally:
        driver.quit()

    # 构建 DataFrame 并返回
    df = pd.DataFrame(records, columns=["id", "profile_url", "followers", "category"])
    return df


def fetch_category_kol(cookie_path: str,
                       hashtag_query: str,
                       min_faves: int,
                       max_scrolls: int,
                       category: str,
                       webdriver_path: str = "chromedriver.exe",
                       headless: bool = True) -> pd.DataFrame:
    """
    一步完成：先抓取符合 hashtag + 最低点赞数的前 100 位 KOL handle，
    再依次打开主页提取粉丝数，返回包含 id, profile_url, followers, category 的 DataFrame。

    参数:
      - cookie_path: Chrome Cookie Editor 导出的 JSON 文件路径
      - hashtag_query: 标签组合字符串，如 "#drone OR #DJI OR #quadcopter"
      - min_faves: 最低点赞数
      - max_scrolls: 搜索时最大滚动次数
      - category: 该批 KOL 对应的品类名称
      - webdriver_path: ChromeDriver 可执行文件路径
      - headless: 是否无头模式运行

    返回:
      - DataFrame, 列名 ["id","profile_url","followers","category"]
    """
    # 1. 获取前 100 个 KOL handle
    handles = get_top_handles(
        cookie_path=cookie_path,
        hashtag_query=hashtag_query,
        min_faves=min_faves,
        max_scrolls=max_scrolls
    )
    print(f"收集到 {len(handles)} 位 KOL @handle")

    # 2. 通过主页解析补齐粉丝数
    df = get_kol_details(
        handles=handles,
        category=category,
        cookie_path=cookie_path,
        webdriver_path=webdriver_path,
        headless=headless
    )
    # 输出前几行数据
    print("获取 KOL 主页信息完成，前几行数据如下：")
    print(df.head())
    
    # 3. 保存结果到 CSV 文件
    if not df.empty:
        print(f"保存到 {category}.csv")  
        df.to_csv(f"{category}.csv", index=False, encoding='utf-8-sig')

    return df


if __name__ == "__main__":
    # 示例：抓取智能无人机领域的 KOL
    df_drone = fetch_category_kol(
        cookie_path="twitter_cache.json",
        hashtag_query="#drone OR #DJI OR #quadcopter",
        min_faves=500,
        max_scrolls=20,
        category="智能无人机",
        webdriver_path="chromedriver.exe",
        headless=False
    )




