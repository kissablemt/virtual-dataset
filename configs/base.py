import os
import sys

root_dir = "D:/virtual-dataset"
object_dir = os.path.join(root_dir, "objects")
output_dir = os.path.join(root_dir, "outputs")
coco_dir = os.path.join(root_dir, "COCO")
log_filepath = os.path.join(output_dir, "log.txt")

sys_path_to_append = [
    root_dir,
    "D:/Anaconda3/lib",
]

def init():
    global sys_path_to_append
    for p in sys_path_to_append:
        if p not in sys.path:
            sys.path.append(p)

def debug():
    print(root_dir, object_dir, output_dir, log_filepath)
    