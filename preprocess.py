from retrieve import embed, dot
from utils import generate_random_id
import time

def preprocess(result_file, src_file=""):
    with open(result_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    ids, segments, metadatas = [], [], []
    texts = []
    start10 = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        text, start, end = line.rsplit(",", 2)
        if start10 == 0:
            start10 = float(start)
        start = float(start)
        end = float(end)
        texts.append(text)
        # 将每10s的文本分割成一个段落
        if end - start10 > 10:
            ids.append(generate_random_id())
            segments.append("search_document: " + ",".join(texts))
            metadatas.append({"start": start10, "end": end, "src_file": src_file})
            start10 = 0
            texts = []
            # print(f"分割段落: {segments[-1]}, 开始时间: {metadatas[-1]['start']}, 结束时间: {metadatas[-1]['end']}")
            
        
    
    return ids, segments, metadatas


def query_search(query, docs_embed, top_k=5, filter_threshold=0.2):
    query_embed = embed(['search_query: ' + query])[0]
    print(f'query: {query!r}')
    similarities = []
    for e in docs_embed:
        similarities.append(dot(query_embed, e))
        # print(f'similarity {dot(query_embed, e):.2f}: {d!r}')

    # 查询similarity前top_k的段落，且过滤掉相似度低于filter_threshold的段落
    top_indices = [i for i, sim in enumerate(similarities) if sim >= filter_threshold]
    top_indices = sorted(top_indices, key=lambda i: similarities[i], reverse=True)[:top_k]



    # top_indices = sorted(range(len(similarities)), key=lambda i: similarities[i], reverse=True)[:top_k]
    
    return top_indices, similarities




# segments, starts, ends = preprocess("result.txt")

def test_asr_embed(segments):

    start_time = time.time()
    segments_embed = embed(['search_document: ' + s for s in segments])
    end_time = time.time()
    print(f"预处理总用时: {int(end_time - start_time)} 秒")
    return segments_embed

# start_time = time.time()
# query_indices, similarities = query_search("北京上学", segments_embed, top_k=5)
# end_time = time.time()
# print(f"查询总用时: {int(end_time - start_time)} 秒")



def test_query_search():

    # 持续接受用户输入，并返回查询结果
    while True:
        query = input("请输入查询内容: ")
        if query.lower() in ["exit", "quit"]:
            break
        print(f"查询内容: {query!r} ")
        if not query.strip():
            print("查询内容不能为空，请重新输入。")
            continue
        start_time = time.time()
        query_indices, similarities = query_search(query, segments_embed, top_k=5)
        
        for i in query_indices:
            print(f"段落: {segments[i]}, 开始时间: {starts[i]}, 结束时间: {ends[i]}, 相似度: {similarities[i]:.2f}")
        end_time = time.time()
        print(f"查询总用时: {int(end_time - start_time)} 秒")
        print("-" * 50)
# print(f"总段落数: {len(segments)}")

