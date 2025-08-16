import torch
from torch.nn.attention import SDPBackend, sdpa_kernel
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from datasets import load_dataset
from tqdm import tqdm

import threading
import time


class ASR:
    """
    ASR class for handling Automatic Speech Recognition tasks.
    """
    
    generate_kwargs = None  # Placeholder for generation parameters
    pipe = None  # Placeholder for the ASR pipeline
    model = None # Placeholder for the ASR model

    # Define the generation parameters
    def __init__(self):
        self.generate_kwargs = {
            "max_new_tokens": 440,
            "num_beams": 1,
            "condition_on_prev_tokens": False,
            "compression_ratio_threshold": 1.35,  # zlib compression ratio threshold (in token space)
            "temperature": (0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
            "logprob_threshold": -1.0,
            "no_speech_threshold": 0.6,
            "return_timestamps": True,
            "language": "chinese"
        }
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        print("Using device: ", device)
        model_id = "openai/whisper-large-v3-turbo"

        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
        )
        self.model.to(device)
        print("Using model: ", model_id)
        processor = AutoProcessor.from_pretrained(model_id)
        print("Using pipeline: automatic-speech-recognition")
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=self.model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            torch_dtype=torch_dtype,
            device=device,
        )

    def asr(self, audio_path, result_path="result.txt"):
        """
        Perform ASR on the given audio file and save the result to a text file.
        """
        start_time = time.time()
        stop_event = threading.Event()
        t = threading.Thread(target=print_elapsed, args=(start_time, stop_event))
        t.start()

        result = self.pipe([audio_path], return_timestamps=True, generate_kwargs=self.generate_kwargs)

        stop_event.set()
        t.join()
        print(f"总用时: {int(time.time() - start_time)} 秒")
        write_result(result, result_path)

    def __del__(self):
        """
        Clean up resources when the ASR object is deleted.
        """


        if self.pipe is not None:
            del self.pipe
        if self.model is not None:
            del self.model
        torch.cuda.empty_cache()


generate_kwargs = {
    "max_new_tokens": 440,
    "num_beams": 1,
    "condition_on_prev_tokens": False,
    "compression_ratio_threshold": 1.35,  # zlib compression ratio threshold (in token space)
    "temperature": (0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
    "logprob_threshold": -1.0,
    "no_speech_threshold": 0.6,
    "return_timestamps": True,
    "language": "chinese"
}

def print_elapsed(start_time, stop_event):
    while not stop_event.is_set():
        elapsed = time.time() - start_time
        print(f"已用时: {int(elapsed)} 秒")
        stop_event.wait(10)  # 每10秒输出一次


def write_result(result, result_path):
    with open(result_path, "w", encoding="utf-8") as f:
        for item in result[0]['chunks']:
            f.write(item["text"] + ",")
            f.write(str(item['timestamp'][0])+",")
            f.write(str(item['timestamp'][1]) + "\n")

def slow_asr(audio_path, result_path="result.txt"):
    

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model_id = "openai/whisper-large-v3-turbo"

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
    )
    model.to(device)

    processor = AutoProcessor.from_pretrained(model_id)

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        torch_dtype=torch_dtype,
        device=device,
    )

    # dataset = load_dataset("distil-whisper/librispeech_long", "clean", split="validation")
    # sample = dataset[0]["audio"]



    start_time = time.time()
    stop_event = threading.Event()
    t = threading.Thread(target=print_elapsed, args=(start_time, stop_event))
    t.start()

    result = pipe([audio_path], return_timestamps=True, generate_kwargs=generate_kwargs)

    stop_event.set()
    t.join()
    print(f"总用时: {int(time.time() - start_time)} 秒")
    write_result(result, result_path)


def fast_asr(audio_path, result_path="result.txt"):
    torch.set_float32_matmul_precision("high")

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model_id = "openai/whisper-large-v3-turbo"

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True
    ).to(device)

    # Enable static cache and compile the forward pass
    model.generation_config.cache_implementation = "static"
    model.generation_config.max_new_tokens = 256
    model.forward = torch.compile(model.forward, mode="reduce-overhead", fullgraph=True)

    processor = AutoProcessor.from_pretrained(model_id)

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        torch_dtype=torch_dtype,
        device=device,
    )

    dataset = load_dataset("distil-whisper/librispeech_long", "clean", split="validation")
    sample = dataset[0]["audio"]

    # 2 warmup steps
    for _ in tqdm(range(2), desc="Warm-up step"):
        with sdpa_kernel(SDPBackend.MATH):
            result = pipe(sample.copy(), return_timestamps=True, generate_kwargs={"min_new_tokens": 256, "max_new_tokens": 256})


    start_time = time.time()
    stop_event = threading.Event()
    t = threading.Thread(target=print_elapsed, args=(start_time, stop_event))
    t.start()


    # fast run
    with sdpa_kernel(SDPBackend.MATH):
        result = pipe([audio_path], return_timestamps=True, generate_kwargs=generate_kwargs)

    stop_event.set()
    t.join()
    print(f"总用时: {int(time.time() - start_time)} 秒")
    write_result(result, result_path)

if __name__ == "__main__":
    # audio_path = "1753363872220364059-294138122944649.mp3"
    # audio_path = "0724.MP3"
    # audio_path = "C20250318_0001_1.mp3"
    # slow_asr(audio_path, "result.txt")
    # fast_asr(audio_path, "result.txt")
    model = ASR()
    model.pipe = None
    model.model = None
    torch.cuda.empty_cache()
    print("done")
