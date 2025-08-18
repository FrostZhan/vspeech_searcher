from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
from video_searcher import VideoSpeechContentSearcher
import threading
from database import db, Index, File, IndexStatus

try:
    # load environment variables from .env file (requires `python-dotenv`)
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print("load env error")

app = Flask(__name__)
CORS(app)  # 允许跨域请求

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
        if not request.is_json:
            return jsonify({'error': '请求必须为JSON格式'}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的JSON数据'}), 400
            
        # 获取索引名称
        index_name = data.get('name')
        
        if not index_name:
            return jsonify({'error': '索引名称不能为空'}), 400
        
        # 获取文件路径列表
        file_paths = data.get('filePaths', []) if isinstance(data, dict) else []
        
        if not file_paths:
            return jsonify({'error': '视频文件列表不能为空'}), 400
        
        # 获取文件路径列表
        video_file_paths = []
        for path in file_paths:
            if not os.path.exists(path):
                return jsonify({'error': f'文件不存在: {path}'}), 400
            if not os.path.isfile(path):
                return jsonify({'error': f'路径不是文件: {path}'}), 400
            video_file_paths.append(path)
        
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

@app.route('/api/indexes/<index_id>', methods=['DELETE'])
def delete_index(index_id):
    """删除索引"""
    try:
        # 检查索引是否存在
        index_obj = db.get_index_by_id(index_id)
        if not index_obj:
            return jsonify({'error': '索引不存在'}), 404
        
        # 删除索引
        if db.delete_index(index_id):
            return jsonify({'message': '索引删除成功'}), 200
        else:
            return jsonify({'error': '索引删除失败'}), 500
    except Exception as e:
        return jsonify({'error': f'索引删除失败: {str(e)}'}), 500

@app.route('/api/indexes/<index_id>/files', methods=['POST'])
def add_files_to_index(index_id):
    """向索引中添加文件"""
    try:
        # 检查索引是否存在
        index_obj = db.get_index_by_id(index_id)
        if not index_obj:
            return jsonify({'error': '索引不存在'}), 404
        
        if not request.is_json:
            return jsonify({'error': '请求必须为JSON格式'}), 400
            
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({'error': '无效的JSON数据'}), 400
            
        # 获取文件路径列表
        file_paths = data.get('filePaths', [])
        
        if not file_paths:
            return jsonify({'error': '文件列表不能为空'}), 400
        
        # 检查文件是否存在
        for path in file_paths:
            if not os.path.exists(path):
                return jsonify({'error': f'文件不存在: {path}'}), 400
            if not os.path.isfile(path):
                return jsonify({'error': f'路径不是文件: {path}'}), 400
        
        # 添加文件到数据库
        new_files = []
        for path in file_paths:
            # 检查文件是否已存在于索引中
            existing_file = next((f for f in index_obj.files if f.path == path), None)
            if existing_file:
                # 如果文件已存在，跳过
                print(f"文件已存在于索引中: {path}")
                continue
            
            # 添加新文件到数据库
            file_obj = db.add_file_to_index(index_id, path)
            new_files.append({
                'path': file_obj.path,
                'status': file_obj.status
            })
        
        # 如果有新文件添加，启动后台处理线程
        if new_files:
            thread = threading.Thread(target=process_videos, args=(index_id, index_obj.name, file_paths))
            thread.start()
        
        return jsonify({'message': '文件添加成功', 'newFiles': new_files}), 200
    except Exception as e:
        return jsonify({'error': f'添加文件失败: {str(e)}'}), 500

@app.route('/api/indexes/<index_id>/files/<path:file_path>', methods=['DELETE'])
def remove_file_from_index(index_id, file_path):
    """从索引中删除文件"""
    try:
        # 检查索引是否存在
        index_obj = db.get_index_by_id(index_id)
        if not index_obj:
            return jsonify({'error': '索引不存在'}), 404
        
        # 删除文件
        db.remove_file_from_index(index_id, file_path)
        vs.delete_video(index_id, file_path)
        return jsonify({'message': '文件删除成功'})
    except Exception as e:
        return jsonify({'error': f'删除文件失败: {str(e)}'}), 500

@app.route('/api/indexes/<index_id>/search', methods=['POST'])
def search_in_index(index_id):
    """在指定索引中搜索"""
    try:
        # 检查索引是否存在
        index_obj = db.get_index_by_id(index_id)
        if not index_obj:
            return jsonify({'error': '索引不存在'}), 404
        
        if not request.is_json:
            return jsonify({'error': '请求必须为JSON格式'}), 400
            
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({'error': '无效的JSON数据'}), 400
            
        query = data.get('query')
        n_results = data.get('nResults', 10)
        video_paths = data.get('videoPaths', None)
        keyword = data.get('keyword', None)
        print(f"index: {index_id}, query: {query}, n_results: {n_results}, video_paths: {video_paths}, keyword: {keyword}")

        documents, metadatas = vs.search_content(index_id, n_results=n_results, query=query, video_paths=video_paths, keyword=keyword)
        
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
        # 添加视频到索引
        vs.add_videos(video_files, index_id)

    except Exception as e:
        print(f"处理索引{index_name} 视频时出错: {str(e)}")
    # 更新索引状态
    db.update_index_status(index_id, IndexStatus.COMPLETED)


def format_time(seconds):
    """将秒数格式化为时间字符串"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

if __name__ == '__main__':
    app.run(debug=True, port=5001)
