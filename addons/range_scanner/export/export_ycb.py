import csv
import numpy as np
import os
import bpy

import scipy.io as sio 

from . import matrix as M

def apply_transform_on_blender(matrix, vertices_co):
    """Get vert coords in world space"""
    m = np.array(matrix)    
    mat = m[:3, :3].T  # Forward of Blender camera is -Z !!!!
    loc = m[:3, 3]
    return vertices_co @ mat + loc


def export(filePath, fileName, data, exportNoiseData, scannerObject, width, height):
    """
    hit.categoryID, hit.partID,                                             # 0, 1   
    hit.location.x, hit.location.y, hit.location.z,                         # 2, 3, 4
    hit.distance,                                                           # 5
    hit.intensity,                                                          # 6
    hit.color[0], hit.color[1], hit.color[2],                               # 7, 8, 9
    """

    cam_K = M.get_K(scannerObject)
    cam_RT = M.get_RT(scannerObject)
    factor_depth = np.array([[10000]])

    poses = None
    center = []
    vertmap = np.zeros((height, width, 3), dtype=np.float)
    objs_set = {}
    for hit in data:
        obj = hit.target
        if not obj.get("object_id", None) and not obj.get("cls_index", None):
            continue
        if objs_set.get(obj, None) == None: # if this object is not visited.
            objs_set[obj] = True # set visited

            # 3D orgin to 2D project center: cam_K @ cam_RT @ matrix_world
            projected_center = apply_transform_on_blender(cam_K @ cam_RT, np.array(obj.location)) 
            projected_center /= projected_center[2]
            center.append(projected_center)

            # to camera coordinate: cam_RT @ matrix_world
            if len(center) == 1:
                poses = np.array(cam_RT @ obj.matrix_world)
            else:
                poses = np.dstack((poses, np.array(cam_RT @ obj.matrix_world)))

             # 3D world coordinate to 2D project coordinate: cam_K @ cam_RT @ matrix_world
            projected_co = apply_transform_on_blender(cam_K @ cam_RT, np.array([hit.location.x, hit.location.y, hit.location.z]))
            projected_co /= projected_co[2]
            x = int(projected_co[0])
            y = int(projected_co[1])
            if 0 <= x < width and 0 <= y < height:
                vertmap[y][x] = obj['object_id']

    center = np.array(center)
    cls_indexes = np.array([[obj['cls_index']] for obj in objs_set.keys()])

    meta_data = {}
    meta_data["cls_indexes"] = cls_indexes
    meta_data["factor_depth"] = factor_depth
    meta_data["intrinsic_matrix"] = cam_K
    meta_data["rotation_translation_matrix"] = cam_RT
    meta_data["vertmap"] = vertmap
    meta_data["poses"] = poses
    meta_data["center"] = center

    if exportNoiseData:
        pass
    else:
        sio.savemat(os.path.join(filePath, "%s.mat" % fileName), meta_data)
        # sio.savemat(os.path.join("D:/vdset/YCB/data/0001", "%s.mat" % "000001-meta"), meta_data)
        pass