import chromadb
from vstore import MyEmbeddingFunction
from video_edit import convert_video_to_audio
from utils import create_temp_folder, delete_temp_folder
from wishper import slow_asr, ASR
from preprocess import preprocess
import os

class VideoSpeechContentSearcher():
    chroma_client = None
    current_database = None
    current_database_name = None
    asr_model = None

    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(path="chroma.db")

    
    def use_database(self, name):
        self.current_database = self.chroma_client.get_or_create_collection(name=name, embedding_function=MyEmbeddingFunction())
        self.current_database_name = name


    def delete_database(self, name):
        self.chroma_client.delete_collection(name=name)


    def add_videos(self, video_paths):
        """
        Add videos to the database.
        """
        if self.asr_model is None:
            self.asr_model = ASR()
        for video_path in video_paths:
            self._add_video(video_path)
            print("-" * 50)
        if self.asr_model is not None:
            del self.asr_model
    
    def _add_video(self, video_path):
        """
        Add a single video to the database.
        """

        if self.asr_model is None:
            self.asr_model = ASR()

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
        print(f"Adding text to database {self.current_database_name}")
        self._add_emebedding(text_path, src_file=video_path)
        print(f"Video {video_path} added to database {self.current_database_name}")

        delete_temp_folder(temp_dir)


    def _add_emebedding(self, text_file, src_file=""):
        ids, documents, metadatas = preprocess(text_file, src_file) 
        self.current_database.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    def search_content(self, query):
        results = self.current_database.query(
            query_texts=["search_query: " + query],
            n_results=5
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