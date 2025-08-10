import uuid

def generate_random_id():
    return str(uuid.uuid4())

# 在当前目录下，创建一个临时文件夹
def create_temp_folder():
    import os
    temp_dir = "tmp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    return temp_dir 


# def create_temp_folder():
#     import tempfile
#     temp_dir = tempfile.mkdtemp(dir=".")
#     return temp_dir

# 删除临时文件夹
def delete_temp_folder(temp_dir):
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)