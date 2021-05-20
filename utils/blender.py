import sys
import os
import time
import numpy as np
import math

import bpy
import bmesh

from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

from . import matrix as M

# ***********************************************************************************************************************
# **********************************************          Base          ***********************************************
# ***********************************************************************************************************************
def import_stl(filepath: str, name=None) -> bpy.types.Object:
    fname, ftype = os.path.splitext(filepath)
    fname = fname.replace('\\', '/').split('/')[-1]
    ftype = '*' + ftype  
    bpy.ops.import_mesh.stl(filepath=filepath)
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
    current_object = bpy.context.object
    if not name:
        name = fname
    current_object.name = name
    return current_object

def import_obj(filepath: str, location, scale, name=None) -> bpy.types.Object:
    fname, ftype = os.path.splitext(filepath)
    fname = fname.replace('\\', '/').split('/')[-1]
    ftype = '*' + ftype  
    bpy.ops.import_scene.obj(filepath=filepath)
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
    bpy.ops.transform.resize(value=scale, constraint_axis=(True, True, True))

    current_object = bpy.context.object
    if not name:
        name = fname
    current_object.name = name
    current_object.location = location
    return current_object

def activate(object) -> None:
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.select_all(action='DESELECT')
    object.select_set(True)
    bpy.context.view_layer.objects.active = object
    
def remove(target) -> None:
    if isinstance(target, bpy.types.Object):
        if isinstance(target.data, bpy.types.Mesh):
            bpy.data.meshes.remove(target.data, do_unlink=True)
        elif isinstance(target.data, bpy.types.Camera):
            bpy.data.cameras.remove(target.data, do_unlink=True)
        elif isinstance(target.data, bpy.types.PointLight):
            bpy.data.lights.remove(target.data, do_unlink=True)
        else:
            pass
    elif isinstance(target, bpy.types.ParticleSettings):
        bpy.data.particles.remove(target, do_unlink=True)
    elif isinstance(target, bpy.types.Collection):
        bpy.data.collections.remove(target, do_unlink=True)
    elif isinstance(target, bpy.types.Material):
        bpy.data.materials.remove(target, do_unlink=True)
    elif isinstance(target, bpy.types.Mesh):
        bpy.data.meshes.remove(target, do_unlink=True)
    else:
        pass
    
def copy(object):
    new_obj = object.copy()
    new_obj.data = object.data.copy()
    new_obj.animation_data_clear()
    bpy.context.collection.objects.link(new_obj)
    return new_obj

def update():
    bpy.context.view_layer.update()
    
def clean() -> None:
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.context.scene.frame_set(0)
    for data_attr in ["meshes", "objects", "cameras", "particles", "collections", "materials", ]:
        for data in getattr(bpy.data, data_attr):
            try:
                remove(data)
            except Exception as e:
                print("clean->remove(): ", e)
            
def get_object(context, obj):
    depsgraph = context.evaluated_depsgraph_get()
    return obj.evaluated_get(depsgraph)

def build_bvhtree(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    tree = BVHTree.FromBMesh(bm, epsilon=0.0)
    bm.free()
    return tree

# ***********************************************************************************************************************
# **********************************************          Camera          ***********************************************
# ***********************************************************************************************************************

def rotate_on_xy_plane(camera, degree): # +:anticlockwise, -:clockwise
    x, y = camera.location[0:2]
    r = math.sqrt(x**2 + y**2)
    rad = np.radians(degree)
    sin_d = math.sin(rad)
    cos_d = math.cos(rad)
    camera.location = (r * cos_d, r * sin_d, camera.location[2])

# 动画demo
def camera_surround(cam, point, degree_step=1, keyframe_insert=False):
    cam.animation_data_clear()
    i = 0
    cam_mws = []
    cam_RTs = []
    for d in range(0, 360, degree_step):
        rotate_on_xy_plane(cam, d)
        look_at(cam, point)
        update()
        if keyframe_insert:
            cam.keyframe_insert(data_path="location", frame=i)
            cam.keyframe_insert(data_path="rotation_euler", frame=i)
            i += 1
        cam_mws.append(cam.matrix_world)
        cam_RTs.append(M.get_RT(cam))
    return cam_mws, cam_RTs

# 镜头朝向，对准point
def look_at(camera, point):
    if not isinstance(point, Vector):
        point = Vector(point)
    direction = point - camera.location
    # point the cameras '-Z' and use its 'Y' as up
    rot_quat = direction.to_track_quat('-Z', 'Y')

    # assume we're using euler rotation
    camera.rotation_euler = rot_quat.to_euler()
    camera.rotation_euler[1] = 0
# ***********************************************************************************************************************
# ***********************************************************************************************************************