import chromadb
import time
from chromadb import Documents, EmbeddingFunction, Embeddings
from retrieve import embed
from preprocess import preprocess

class MyEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        # embed the documents somehow
        return embed(input)


def add_document_example():
    collection = chroma_client.create_collection(name="my_collection")
    collection.add(
        ids=["id1", "id2"],
        documents=[
            "This is a document about pineapple",
            "This is a document about oranges"
        ]
    )

    results = collection.query(
        query_texts=["This is a query document about hawaii"], # Chroma will embed this for you
        n_results=2 # how many results to return
    )
    print(results)




def add_embedding(text_file, collection_name="asr_collection"):
    collection = chroma_client.get_or_create_collection(name=collection_name, embedding_function=MyEmbeddingFunction())
    ids, documents, metadatas = preprocess(text_file) 
    
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )

    print(f"已添加 {len(ids)} 个文档到集合 'asr_collection'")






def test_query():
    collection = chroma_client.get_collection(name="asr_collection", embedding_function=MyEmbeddingFunction())
    while True:
        query = input("请输入查询内容: ")
        if query.lower() in ["exit", "quit"]:
            break
        print(f"查询内容: {query!r} ")
        if not query.strip():
            print("查询内容不能为空，请重新输入。")
            continue
        start_time = time.time()
        results = collection.query(
            query_texts=["search_query: " + query],
            n_results=5
        )
        end_time = time.time()
        for document, metadata, distance in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
            document = document.replace("search_document: ", "")
            print(f"文档: {document}, 元数据: {metadata}, 距离: {distance}")
        print(f"查询总用时: {int(end_time - start_time)} 秒")
        print("-" * 50)


if __name__ == "__main__":
    # 创建或连接到数据库
    chroma_client = chromadb.PersistentClient(path="chroma.db")
    # 测试添加嵌入
    # add_embedding("result.txt")
    # 测试查询
    test_query()
