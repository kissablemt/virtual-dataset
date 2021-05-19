import os
import bpy
import sys
import time
import importlib

# ********************** add path **********************
path_to_add = [
    "D:/virtual-dataset",
]
for path in path_to_add:
    if path not in sys.path:
        sys.path.append(path)
        
        
# ********************** add custom modules **********************
from configs import base
from utils import blender as B
from scripts import build_scene as scene
from scripts import generate_dataset as gen_dset

# ********************** reload modules **********************
modules_to_reload = [
    B,
    scene,
    gen_dset,
]
for m in modules_to_reload:
    importlib.reload(m)
    

def create_light() -> bpy.types.Object:
    light_data = bpy.data.lights.new(name='Light', type="POINT")
    light_object = bpy.data.objects.new('Light', light_data)
    bpy.context.scene.collection.objects.link(light_object)
    light_object.location = (0.5, 0.5, 1)
    return light_object
    
    
def main():   
    start_time = time.time()
    
    for i in range(0, 1):
        scene.build_scene(random_seed=i)
        gen_dset.generate_dataset(name=i)
        break
    
    print("RUN: {:.2f}s".format(time.time() - start_time))
    return 0    

if __name__ == '__main__':
    try:
        main() 
        print("hello")
    except Exception as e:
        print("main(): ", e)
