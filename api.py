from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
from video_searcher import VideoSpeechContentSearcher
import threading
from database import db, Index, File, IndexStatus

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 存储搜索器实例
searchers = {}

# 初始化搜索器
vs = VideoSpeechContentSearcher()

@app.route('/api/indexes', methods=['GET'])
def get_indexes():
    """获取所有索引列表"""
    try:
        indexes = db.get_all_indexes()
        # 转换为字典格式以供JSON序列化
        indexes_dict = []
        for index in indexes:
            files_dict = [{'path': f.path, 'status': f.status} for f in index.files]
            indexes_dict.append({
                'id': index.id,
                'name': index.name,
                'createDate': index.create_date,
                'status': index.status,
                'files': files_dict
            })
        return jsonify(indexes_dict)
    except Exception as e:
        return jsonify({'error': f'获取索引列表失败: {str(e)}'}), 500

@app.route('/api/indexes', methods=['POST'])
def create_index():
    """创建新索引"""
    try:
        # 获取索引名称
        index_name = request.form.get('name')
        
        if not index_name:
            return jsonify({'error': '索引名称不能为空'}), 400
        
        # 获取上传的文件
        uploaded_files = request.files.getlist('files')
        
        if not uploaded_files:
            return jsonify({'error': '视频文件列表不能为空'}), 400
        
        # 创建临时文件夹
        temp_folder = os.path.join('tmp', str(uuid.uuid4()))
        os.makedirs(temp_folder, exist_ok=True)
        
        # 保存上传的文件到临时文件夹
        video_file_paths = []
        for file in uploaded_files:
            if file.filename != '':
                # 生成文件路径
                file_path = os.path.join(temp_folder, file.filename)
                # 保存文件
                file.save(file_path)
                # 添加到文件路径列表
                video_file_paths.append(file_path)
        
        # 创建索引记录
        index_obj = db.create_index(index_name, video_file_paths)
        index_id = index_obj.id
        
        # 启动后台处理线程
        thread = threading.Thread(target=process_videos, args=(index_id, index_name, video_file_paths))
        thread.start()
        
        # 转换为字典格式以供JSON序列化
        files_dict = [{'path': f.path, 'status': f.status} for f in index_obj.files]
        index_record = {
            'id': index_obj.id,
            'name': index_obj.name,
            'createDate': index_obj.create_date,
            'status': index_obj.status,
            'files': files_dict
        }
        
        return jsonify(index_record), 201
    except Exception as e:
        return jsonify({'error': f'创建索引失败: {str(e)}'}), 500

@app.route('/api/indexes/<index_id>', methods=['GET'])
def get_index_detail(index_id):
    """获取索引详情"""
    try:
        index_obj = db.get_index_by_id(index_id)
        
        if not index_obj:
            return jsonify({'error': '索引不存在'}), 404
        
        # 转换为字典格式以供JSON序列化
        files_dict = [{'path': f.path, 'status': f.status} for f in index_obj.files]
        index_detail = {
            'id': index_obj.id,
            'name': index_obj.name,
            'createDate': index_obj.create_date,
            'status': index_obj.status,
            'files': files_dict
        }
        
        return jsonify(index_detail)
    except Exception as e:
        return jsonify({'error': f'获取索引详情失败: {str(e)}'}), 500

@app.route('/api/indexes/<index_id>/search', methods=['POST'])
def search_in_index(index_id):
    """在指定索引中搜索"""
    try:
        # 检查索引是否存在
        index_obj = db.get_index_by_id(index_id)
        if not index_obj:
            return jsonify({'error': '索引不存在'}), 404
        
        data = request.json
        query = data.get('query')
        
        if not query:
            return jsonify({'error': '搜索关键词不能为空'}), 400
        
        # 使用搜索器执行搜索
        if index_id not in searchers:
            return jsonify({'error': '索引尚未准备好'}), 400
        
        searcher = searchers[index_id]
        documents, metadatas = searcher.search_content(query)
        
        # 格式化搜索结果
        results = []
        for doc, meta in zip(documents, metadatas):
            doc = doc.replace("search_document: ", "")
            results.append({
                'videoPath': meta.get('src_file', ''),
                'startTime': format_time(meta.get('start', 0)),
                'text': doc
            })
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': f'搜索失败: {str(e)}'}), 500

def process_videos(index_id, index_name, video_files):
    """后台处理视频文件"""
    try:
        # 创建或使用数据库
        vs.use_database(index_name)
        searchers[index_id] = vs
        
        # 添加视频到索引
        vs.add_videos(video_files, index_id)
        
        # 更新索引状态
        db.update_index_status(index_id, IndexStatus.COMPLETED)
            
    except Exception as e:
        # 更新索引状态为错误
        db.update_index_status(index_id, IndexStatus.ERROR)
        print(f"处理视频时出错: {str(e)}")

def format_time(seconds):
    """将秒数格式化为时间字符串"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

if __name__ == '__main__':
    app.run(debug=True, port=5000)
