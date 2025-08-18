from huggingface_hub import hf_hub_download


from llama_cpp import Llama
import time


from langchain_community.embeddings import LlamaCppEmbeddings


if __name__ == "__main__":
    
    # hf_hub_download(
    #     repo_id="nomic-ai/nomic-embed-text-v2-moe-GGUF", filename="nomic-embed-text-v2-moe.f16.gguf", local_dir="models"
    # )

    llm = Llama(
        model_path="./models/nomic-embed-text-v2-moe.f16.gguf",
        n_batch=1,
        embedding=True,
        # n_gpu_layers=-1, # Uncomment to use GPU acceleration
        # seed=1337, # Uncomment to set a specific seed
        # n_ctx=2048, # Uncomment to increase the context window
    )
    # output = llm.embed(["csdsdcsdcsc", "xxxx","A: xxx jijdisnj", "xxxxx", "xxx", "xxx"]) 
    # print(len(output))
    # print(output[0][0])
    # time.sleep(50)


    llama = LlamaCppEmbeddings(model_path="./models/nomic-embed-text-v2-moe.f16.gguf", n_batch=1)
    output = llama.embed_documents(["chrthtrtnrt g ertgerg", "xxxx","A: xxx jijdisnj", "xxxxx", "xxx", "xxx"])
    print(output[0][0])


