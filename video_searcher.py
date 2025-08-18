import chromadb
from vstore import MyEmbeddingFunction
from video_edit import convert_video_to_audio
from utils import create_temp_folder, delete_temp_folder
from wishper import slow_asr, ASR
from preprocess import preprocess
import os
from database import db, IndexStatus

class VideoSpeechContentSearcher():
    chroma_client = None
    database = None
    asr_model = None
    
    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(path="chroma.db")
        self.database = db

    def delete_database(self, name):
        self.chroma_client.delete_collection(name=name)


    def add_videos(self, video_paths, index_id):
        """
        Add videos to the database.
        """
        if index_id == "":
            raise ValueError("Index ID cannot be empty.")

        if self.asr_model is None:
            print("Initializing ASR model...")
            self.asr_model = ASR()
            print("ASR model initialized.")
        for video_path in video_paths:
            self._add_video(video_path, index_id)
            print("-" * 50)
        if self.asr_model is not None:
            del self.asr_model
    
    def _add_video(self, video_path, index_id):
        """
        Add a single video to the database.
        """
        try:
            self.database.update_file_status(index_id, video_path, IndexStatus.PROCESSING)
            print(f"Adding video: {video_path}")
            # Placeholder for video processing logic
            # Here you would extract audio and process it as needed
            temp_dir = create_temp_folder()

            # Extract audio from video
            print(f"Extracting audio from video: {video_path}")
            audio_path = os.path.join(temp_dir, "output_audio.wav")
            convert_video_to_audio(video_path, audio_path)
            print(f"Audio extracted to: {audio_path}")

            # Perform ASR on the audio file
            print("Performing ASR on the audio file...")
            text_path = os.path.join(temp_dir, "text.txt")
            self.asr_model.asr(audio_path, result_path=text_path)
            print(f"ASR result saved to: {text_path}")

            # Add the processed audio text to the database
            print(f"Adding text to database {index_id}")
            self._add_emebedding(text_path, src_file=video_path, index_id=index_id)
            print(f"Video {video_path} added to database {index_id}")

            # 更新文件状态为已完成
            db.update_file_status(index_id, video_path, IndexStatus.COMPLETED)

            delete_temp_folder(temp_dir)
        except Exception as e:
            # 更新文件状态为错误
            db.update_file_status(index_id, video_path, IndexStatus.ERROR)
            print(f"处理视频 {video_path} 时出错: {str(e)}")
            raise


    def _add_emebedding(self, text_file, src_file, index_id):
        collection = self.chroma_client.get_or_create_collection(name=index_id, embedding_function=MyEmbeddingFunction())
        ids, documents, metadatas = preprocess(text_file, src_file) 
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    def search_content(self, index_id, n_results=10, query=None, video_paths=None, keyword=None):
        collection = self.chroma_client.get_collection(name=index_id, embedding_function=MyEmbeddingFunction())
        query_texts, where, where_document = None, None, None
        if query is not None:
            query_texts = ["search_query: " + query]
        if keyword is not None:
            keywords = keyword.split(",")
            where_document = {
                "$and": [
                    {"$contains": keyword} for keyword in keywords
                ]
            }
            # where_document = {"$contains": keyword}
        if video_paths is not None:
            where = {"src_file": {"$in": video_paths}}
        results = collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where,
            where_document=where_document
        )
        documents, metadatas = results['documents'][0], results['metadatas'][0]
        return documents, metadatas


    def user_query(self):
        """
        User query interface.
        """
        while True:
            query = input("请输入查询内容: ")
            if query.lower() in ["exit", "quit"]:
                break
            print(f"查询内容: {query!r} ")
            if not query.strip():
                print("查询内容不能为空，请重新输入。")
                continue
            documents, metadatas = self.search_content(query)
            for document, metadata in zip(documents, metadatas):
                document = document.replace("search_document: ", "")
                print(f"文档: {document}, 元数据: {metadata}")
            print("-" * 50)
