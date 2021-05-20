import sys
import os
import time
import numpy as np
import cv2
np.set_printoptions(suppress=True)

import bpy
import bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

import importlib

sys.path.append("D:/virtual-dataset")
from configs import base
from utils import blender as B
from utils import matrix as M
from scripts import generate_dataset as gen_dset

def create_light(location) -> bpy.types.Object:
    light_data = bpy.data.lights.new(name='Light', type="POINT")
    light_object = bpy.data.objects.new('Light', light_data)
    bpy.context.scene.collection.objects.link(light_object)
    light_object.location = location
    return light_object

def create_camera() -> bpy.types.Object:
    camera_data = bpy.data.cameras.new(name='Camera')
    camera_object = bpy.data.objects.new('Camera', camera_data)
    bpy.context.scene.collection.objects.link(camera_object)
    bpy.context.scene.camera = camera_object
    camera_object.location = (0, -3.0, 3)
    camera_object.rotation_euler = (0.785, 0, 0)
    B.look_at(camera_object, (0, 0, 0))
    return camera_object

def create_monkey() -> bpy.types.Object:
    bpy.ops.mesh.primitive_monkey_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0))
    target = bpy.context.object
    mat = bpy.data.materials.get("Monkey Material")
    if mat is None:
        # create material
        mat = bpy.data.materials.new(name="Monkey Material")

    # Assign it to object
    if target.data.materials:
        # assign to 1st material slot
        target.data.materials[0] = mat
    else:
        # no slots
        target.data.materials.append(mat)
    target["cls_index"] = 1
    target["object_id"] = 1
    return target


def build_scene():
    B.clean()
    light1 = create_light((0.5, 0.5, 1))
    light2 = create_light((-0.5, -0.5, 1))
    create_camera()
    create_monkey()
    
    
def surround_scan():
    cam = bpy.data.objects["Camera"]
    cam.animation_data_clear()
    loc_bak, rot_bak = cam.location.copy(), cam.rotation_euler.copy()
    print(cam.location, cam.rotation_euler)
    for d in range(0, 360, 90):
        B.rotate_on_xy_plane(cam, d)
        B.look_at(cam, Vector((0, 0, 0)))
        B.update()
        
        gen_dset.generate_dataset("degree-%d" % d)
        
    cam.location, cam.rotation_euler = loc_bak, rot_bak
    print(cam.location, cam.rotation_euler)
        
def main(): 
    build_scene()
    surround_scan()
#    B.camera_surround(bpy.data.objects['Camera'], Vector((0, 0, 0)), degree_step=1, keyframe_insert=True)
    return 0    

if __name__ == '__main__':

    try:
        main()
    except Exception as e:
        print("Error: ", e)
        
