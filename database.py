import sqlite3
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional

# 数据类定义
@dataclass
class File:
    id: int
    index_id: str
    path: str
    status: str

@dataclass
class Index:
    id: str
    name: str
    create_date: str
    status: str
    files: List[File] = field(default_factory=list)

class IndexStatus:
    WAITING = "waiting"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class Database:
    def __init__(self, db_file: str = 'indexes.db'):
        self.db_file = db_file
        self.init_db()
    
    # 初始化数据库
    def init_db(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # 创建索引表
        c.execute('''
            CREATE TABLE IF NOT EXISTS indexes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                create_date TEXT NOT NULL,
                status TEXT NOT NULL
            )
        ''')
        
        # 创建文件表
        c.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                index_id TEXT NOT NULL,
                path TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL,
                FOREIGN KEY (index_id) REFERENCES indexes (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # 创建索引
    def create_index(self, name: str, video_files: List[str]) -> Index:
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # 生成索引ID
        index_id = str(uuid.uuid4())
        
        # 获取当前日期和时间
        create_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 插入索引记录
        c.execute('''
            INSERT INTO indexes (id, name, create_date, status)
            VALUES (?, ?, ?, ?)
        ''', (index_id, name, create_date, IndexStatus.PROCESSING))
        
        # 插入文件记录
        files = []
        for file_path in video_files:
            c.execute('''
                INSERT INTO files (index_id, path, status)
                VALUES (?, ?, ?)
            ''', (index_id, file_path, IndexStatus.WAITING))
            
            # 获取插入的文件ID
            file_id = c.lastrowid
            if file_id is None:
                file_id = 0
            files.append(File(file_id, index_id, file_path, IndexStatus.WAITING))
        
        conn.commit()
        conn.close()
        
        # 返回创建的索引对象
        return Index(index_id, name, create_date, IndexStatus.PROCESSING, files)
    
    # 获取所有索引
    def get_all_indexes(self) -> List[Index]:
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # 获取所有索引
        c.execute('SELECT * FROM indexes')
        index_rows = c.fetchall()
        
        indexes = []
        for row in index_rows:
            index_id, name, create_date, status = row
            
            # 获取该索引的文件
            c.execute('SELECT id, index_id, path, status FROM files WHERE index_id = ?', (index_id,))
            file_rows = c.fetchall()
            
            files = [File(id, idx_id, path, status) for id, idx_id, path, status in file_rows]
            
            indexes.append(Index(index_id, name, create_date, status, files))
        
        conn.close()
        return indexes
    
    # 根据ID获取索引
    def get_index_by_id(self, index_id: str) -> Optional[Index]:
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # 获取索引信息
        c.execute('SELECT * FROM indexes WHERE id = ?', (index_id,))
        row = c.fetchone()
        
        if not row:
            conn.close()
            return None
        
        index_id, name, create_date, status = row
        
        # 获取该索引的文件
        c.execute('SELECT id, index_id, path, status FROM files WHERE index_id = ?', (index_id,))
        file_rows = c.fetchall()
        
        files = [File(id, idx_id, path, status) for id, idx_id, path, status in file_rows]
        
        conn.close()
        
        return Index(index_id, name, create_date, status, files)
    
    # 更新索引状态
    def update_index_status(self, index_id: str, status: str) -> bool:
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # 更新索引状态
        c.execute('''
            UPDATE indexes SET status = ? WHERE id = ?
        ''', (status, index_id))
        
        # 如果索引完成，也更新所有文件的状态
        if status == IndexStatus.COMPLETED:
            c.execute('''
                UPDATE files SET status = ? WHERE index_id = ?
            ''', (IndexStatus.COMPLETED, index_id))
        
        conn.commit()
        rows_affected = c.rowcount
        conn.close()
        
        return rows_affected > 0
    
    # 更新文件状态
    def update_file_status(self, index_id: str, file_path: str, status: str) -> bool:
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # 更新文件状态
        c.execute('''
            UPDATE files SET status = ? WHERE index_id = ? AND path = ?
        ''', (status, index_id, file_path))
        
        conn.commit()
        rows_affected = c.rowcount
        conn.close()
        
        return rows_affected > 0
    
    # 更新索引信息
    def update_index(self, index: Index) -> bool:
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        # 更新索引信息
        c.execute('''
            UPDATE indexes SET name = ?, status = ? WHERE id = ?
        ''', (index.name, index.status, index.id))
        
        conn.commit()
        rows_affected = c.rowcount
        conn.close()
        
        return rows_affected > 0
    
    # 删除索引
    def delete_index(self, index_id: str) -> bool:
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # 先删除相关文件记录
        c.execute('DELETE FROM files WHERE index_id = ?', (index_id,))
        
        # 再删除索引记录
        c.execute('DELETE FROM indexes WHERE id = ?', (index_id,))
        
        conn.commit()
        rows_affected = c.rowcount
        conn.close()
        
        return rows_affected > 0
    
    # 添加文件到索引
    def add_file_to_index(self, index_id: str, file_path: str) -> File:
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # 更新索引状态
        c.execute('''
            UPDATE indexes SET status = ? WHERE id = ?
        ''', (IndexStatus.PROCESSING, index_id))

        # 插入文件记录
        c.execute('''
            INSERT INTO files (index_id, path, status)
            VALUES (?, ?, ?)
        ''', (index_id, file_path, IndexStatus.WAITING))
        
        # 获取插入的文件ID
        file_id = c.lastrowid
        if file_id is None:
            file_id = 0
        
        conn.commit()
        conn.close()
        
        return File(file_id, index_id, file_path, IndexStatus.WAITING)
    
    # 从索引中删除文件
    def remove_file_from_index(self, index_id: str, file_path: str) -> bool:
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # 删除文件记录
        c.execute('''
            DELETE FROM files WHERE index_id = ? AND path = ?
        ''', (index_id, file_path))
        
        conn.commit()
        rows_affected = c.rowcount
        conn.close()
        
        return rows_affected > 0

# 全局数据库实例
db = Database()
