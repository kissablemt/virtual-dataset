import sys
import os
import time
import numpy as np
from transforms3d.quaternions import quat2mat, mat2quat

import bpy
import bpy_extras
from mathutils import Matrix
from mathutils import Vector
np.set_printoptions(suppress=True)

filepath = os.path.abspath(__file__) # vdset/utils/matrix.py
current_path = os.path.abspath(os.path.dirname(filepath) + os.path.sep + ".") # vdset/utils/
father_path = os.path.abspath(os.path.dirname(current_path) + os.path.sep + ".") # vdset/

if father_path not in sys.path:
    sys.path.append(father_path)


def get_sensor_size(camera):
    if camera.data.sensor_fit == 'VERTICAL':
        return camera.data.sensor_height
    return camera.data.sensor_width

def get_sensor_fit(sensor_fit, size_x, size_y):
    if sensor_fit == 'AUTO':
        if size_x >= size_y:
            return 'HORIZONTAL'
        else:
            return 'VERTICAL'
    return sensor_fit

def get_K(camera):
    return get_intrinsic_matrix(camera)

# https://blender.stackexchange.com/questions/38009/3x4-camera-matrix-from-blender-camera
def get_intrinsic_matrix(camera):
    scene = bpy.context.scene
    cam_data = camera.data
    if cam_data.type != 'PERSP':
        raise ValueError('Non-perspective cameras not supported')
    
    # Render Settings
    scale = scene.render.resolution_percentage / 100
    resolution_x_in_px = scale * scene.render.resolution_x
    resolution_y_in_px = scale * scene.render.resolution_y
    pixel_aspect_ratio = scene.render.pixel_aspect_y / scene.render.pixel_aspect_x
    
    # Camera Settings
    focal_length_in_mm = cam_data.lens
    sensor_size_in_mm = get_sensor_size(camera)
    sensor_fit = get_sensor_fit(
        cam_data.sensor_fit,
        scene.render.pixel_aspect_x * resolution_x_in_px,
        scene.render.pixel_aspect_y * resolution_y_in_px
    )
    
    if sensor_fit == 'HORIZONTAL':
        view_fac_in_px = resolution_x_in_px
    else:
        view_fac_in_px = pixel_aspect_ratio * resolution_y_in_px
    pixel_size_mm_per_px = sensor_size_in_mm / focal_length_in_mm / view_fac_in_px
    f_u = 1 / pixel_size_mm_per_px
    f_v = 1 / pixel_size_mm_per_px / pixel_aspect_ratio

    # Parameters of intrinsic calibration matrix K
    u_0 = resolution_x_in_px / 2 - cam_data.shift_x * view_fac_in_px
    v_0 = resolution_y_in_px / 2 + cam_data.shift_y * view_fac_in_px / pixel_aspect_ratio
    skew = 0 # only use rectangular pixels

    K = Matrix(
        ((f_u, skew, u_0),
        (   0,  f_v, v_0),
        (   0,    0,   1)))
    K = np.array(K)
    return K    


## Returns camera rotation and translation matrices from Blender.
## 
## There are 3 coordinate systems involved:
##    1. The World coordinates: "world"
##       - right-handed
##    2. The Blender camera coordinates: "bcam"
##       - x is horizontal
##       - y is up
##       - right-handed: negative z look-at direction
##    3. The desired computer vision camera coordinates: "cv"
##       - x is horizontal
##       - y is down (to align to the actual pixel coordinates 
##         used in digital images)
##       - right-handed: positive z look-at direction
def get_RT(camera):
    return get_RT_matrix(camera)

def get_RT_matrix(camera):
    # bcam stands for blender camera
    R_bcam2cv = Matrix(
        ((1, 0,  0),
        (0, -1, 0),
        (0, 0, -1)))

    location, rotation = camera.matrix_world.decompose()[0:2]
    R_world2bcam = rotation.to_matrix().transposed()
    T_world2bcam = -1 * R_world2bcam @ location

    # Build the coordinate transform matrix from world to computer vision camera
    R_world2cv = R_bcam2cv @ R_world2bcam
    T_world2cv = R_bcam2cv @ T_world2bcam

    # put into 3x4 matrix
    RT = Matrix((
        R_world2cv[0][:] + (T_world2cv[0],),
        R_world2cv[1][:] + (T_world2cv[1],),
        R_world2cv[2][:] + (T_world2cv[2],)
    ))
    RT = np.array(RT)
    return RT
    

def get_P(camera):
    return get_projection_matrix(camera)

def get_projection_matrix(camera):
    K = get_intrinsic_matrix(camera)
    RT = get_RT_matrix(camera)
    return K @ RT

def get_co(obj):
    """Returns vertex coords as N x 3"""
    n = len(obj.data.vertices)    
    arr = np.zeros(n * 3, dtype=np.float32)
    obj.data.vertices.foreach_get('co', arr.ravel())
    arr.shape = (n, 3)
    return arr

def apply_transform_on_blender(matrix, vertices_co):
    """Get vert coords in world space"""
    m = np.array(matrix)    
    mat = m[:3, :3].T  # Forward of Blender camera is -Z !!!!
    loc = m[:3, 3]
    return vertices_co @ mat + loc


def revert_transform_on_blender(matrix, co):
    """Set world coords on object. 
    Run before setting coords to deal with object transforms
    if using apply_transforms()"""
    m = np.linalg.inv(matrix)    
    mat = m[:3, :3].T # rotates backwards without T
    loc = m[:3, 3]
    return co @ mat + loc

def world_to_RT(matrix_world):
    m = np.array(matrix_world)
    return m[:3, :4]

def main():
    scene = bpy.context.scene
    camera = bpy.data.objects['Camera']
    K = get_K(camera)
    P = get_P(camera)
    
    obj = bpy.data.objects['textured.001']
    with open("/Users/wzt/Documents/BlenderProjects/outputs/2d.txt", "w") as f:
        for obj in bpy.data.objects:
            if getattr(obj.data, "vertices", None) == None:
                continue
            obj_P = P @ obj.matrix_world
            projected_co = apply_transform_on_blender(obj_P, get_co(obj))
            projected_co /= projected_co[:, 2:]
            for co in projected_co:
                f.write("{} {}\n".format(co[0], co[1]))
    return 0
    
    
if __name__ == '__main__':
    start_time = time.time()
    try:
        main()
#        test()
    except Exception as e:
        print(e)
    print("RUN: {:.2f}s".format(time.time() - start_time))