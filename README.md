# 视频语音内容搜索系统 (vspeech_searcher)

这是一个基于 Whisper 模型的视频语音内容搜索系统，可以对视频中的语音内容进行识别、索引和搜索。

## 功能特性

- 视频语音内容识别（使用 Whisper 模型）
- 视频内容索引管理
- 文本搜索功能
- Web 前端界面

## 项目结构

```
.
├── api.py              # 后端 API 服务
├── main.py             # 主程序入口
├── video_searcher.py   # 视频搜索核心逻辑
├── vstore.py           # 向量存储相关
├── retrieve.py         # 检索相关
├── preprocess.py       # 预处理相关
├── wishper.py          # Whisper 模型封装
├── video_edit.py       # 视频处理相关
├── utils.py            # 工具函数
├── requirements.txt    # 项目依赖
├── frontend/           # 前端代码
│   ├── index.html
│   ├── styles.css
│   ├── script.js
│   └── README.md
└── README.md           # 项目说明
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行后端服务

```bash
python api.py
```

后端服务将运行在 `http://localhost:5000`

## 运行前端界面

1. 进入 frontend 目录
2. 在浏览器中打开 `index.html` 文件，或者使用本地服务器运行

## 使用说明

1. 启动后端服务
2. 打开前端界面
3. 创建视频数据索引
4. 在索引中进行内容搜索

## API 接口

- `GET /api/indexes` - 获取所有索引列表
- `POST /api/indexes` - 创建新索引
- `GET /api/indexes/<index_id>` - 获取索引详情
- `POST /api/indexes/<index_id>/search` - 在指定索引中搜索
