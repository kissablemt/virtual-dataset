import bpy
import bmesh
import sys
import os
import time
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
import numpy as np

import importlib

sys.path.append("D:/virtual-dataset")
from configs import base
from utils import blender as B
from utils import matrix as M

modules_to_reload = [
    base, B, M, 
]

for m in modules_to_reload:
    importlib.reload(m)

    
def create_target():
    B.import_stl(filepath=os.path.join(base.object_dir, "30D_831_673____PCA_TM__003_____VERST_TUERFESTSTEL________EDAG_20180824.STL"))
    bpy.context.object.name = "Target" 
    bpy.context.object.scale=(1, 1, 1)
    bpy.context.object.location=(0, 0, 0)
    return bpy.context.object


# 碰撞检测
def intersection_check(obj_list):
    #check every object for intersection with every other object
    start_time = time.time()
    bpy.context.view_layer.update()
    bvh_trees = []
    for obj in obj_list:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.transform(obj.matrix_world)
        bvh_trees.append(BVHTree.FromBMesh(bm, epsilon=0.0))
        bm.free()
        
    sz = len(obj_list)
    for i in range(sz):
        for j in range(i + 1, sz):
            inter = bvh_trees[i].overlap(bvh_trees[j])
            if inter != []:
                return True
#    print("time: ", time.time() - start_time)
    return False

def get_distance(vertex1_co, vertex2_co) -> float:
    return (vertex1_co - vertex2_co).length


# 获得物体对应点的距离
def get_objects_distance(obj1, obj2) -> float:
    B.update()
    return get_distance(obj1.matrix_world @ obj1.data.vertices[0].co, obj2.matrix_world @ obj2.data.vertices[0].co)


# 在`axis`轴上靠近， 0->x, 1->y, 2->z
def bsearch_axis(obj1, obj2, axis, flag=1):
    obj1 = B.copy(obj1)
    obj2 = B.copy(obj2)
    
    touch_dis = 0
    untouch_dis = flag * 200 ## 注意！ 这个距离应设置为3D Bounding Box的长，这里没有计算写了200作为测试
    
    while abs(untouch_dis - touch_dis) > 0.0001:
        test_dis = (touch_dis + untouch_dis) / 2
        obj2.location[axis] = test_dis
        is_inter = intersection_check([obj1, obj2])
        if is_inter:
            touch_dis = test_dis
        else:
            untouch_dis = test_dis
    
    B.remove(obj1)
    B.remove(obj2)    
    return untouch_dis


def bsearch_location(obj1_, obj2_):
    obj1 = B.copy(obj1_)
    obj2 = B.copy(obj2_)
    
    # 先在y轴上靠近
    obj2.location[1] = bsearch_axis(obj1, obj2, 1, -1)
    
    ## 注意！ [10, -5, 1]是人为设置的，实际上第一个值应设置为3D Bounding Box的某边长度，然后依次除以-2
    for step in [10, -5, 1]:
        pre_dis = float("inf")
        while True:
            dis = get_objects_distance(obj1, obj2)
            if dis > pre_dis:
                break
            obj2.location[0] += step
            obj2.location[1] = bsearch_axis(obj1, obj2, 1, -1)
            pre_dis = dis
    location = obj2.location
    
    B.remove(obj1)
    B.remove(obj2)
    return location


def seq_test():
    obj1 = create_target()
#    obj1.rotation_euler = (0.15, 0.35, 0)
        
    obj_list = [obj1]
    for i in range(1, 2):
        obj_old = obj_list[i - 1]
        obj_new = B.copy(obj_old)
        
#        obj_new.rotation_euler = (np.random.randint(5, 10) / 100, np.random.randint(35, 55) / 100, 0)
        obj_new.location = bsearch_location(obj_old, obj_new)
#        print("obj_{} location: ".format(i), obj_new.location, "\n")
        obj_list.append(obj_new)
        B.update()
    return 0


def main():
    B.clean()
    seq_test()
    return 0

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print("Error: ", e)