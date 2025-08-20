# TMDb 影视数据抓取
本项目用于抓取 [TMDb](https://www.themoviedb.org/) 的最新电影和电视剧信息，并保存为 JSON 文件。  
支持多语言信息抓取，并可每天定时运行，获取最近 3 天更新的影视内容。

## 功能
- 获取最近 3 天上映的电影及更新的电视剧
- 支持抓取中、英、日、韩、法多语言信息
- 清洗字段：标题、上映/更新日期、地区、类型、简介、海报链接、影视类型（电影/电视剧）
- 自动生成 JSON 文件保存抓取结果
- 可与 Glide App 结合，实时展示影视数据

## 文件说明
- `main.py` - 项目主文件，包含数据抓取、清洗、JSON 输出逻辑
- `api_key.txt` - TMDb API Key（**注意：不要上传到 GitHub**）
- `.gitignore` - 忽略本地生成文件、敏感信息和 IDE 配置
- `requirements.txt` - 项目依赖文件（requests 等）
- `output/` - 存放抓取结果的 JSON 文件（不上传）

## 使用方法
1.克隆仓库到本地：
```bash
git clone <仓库地址>
2.安装依赖：
pip install -r requirements.txt
3.在根目录创建 api_key.txt，填入你的 TMDb API Key。
4.运行脚本抓取数据：
python main.py
5.抓取完成后，JSON 文件会生成在 output/output.json。
6.定时运行
可使用 GitHub Actions 或其他定时任务，每天定时运行脚本获取最新影视数据。例如：
北京时间每天 10:00 和 22:00 自动抓取
输出结果覆盖 output/output.json
7.注意事项
请确保 API Key 有效
数据库和输出文件夹被 .gitignore 忽略，本地运行时会自动生成
当前只抓取最近 3 天的影视更新
