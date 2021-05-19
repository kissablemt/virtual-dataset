import bpy
import os
import cv2
import numpy as np
import importlib
from configs import base
from utils import blender as B
from utils import matrix as M

from addons import range_scanner
from addons import bpycv

# modules_to_reload = [
#     range_scanner, 
#     range_scanner.scanners, range_scanner.export,
#     range_scanner.scanners.generic, range_scanner.scanners.lidar,
#     range_scanner.export.exporter, range_scanner.export.export_csv, range_scanner.export.export_ycb,
#     bpycv,
#     bpycv.render_utils, bpycv.material_utils, 
# ]
# for m in modules_to_reload:
#     try:
#         importlib.reload(m)
#     except:
#         print(m)
#         pass

def kinect_v1(output_dir, filename):
    try:
        range_scanner.ui.user_interface.register()
    except Exception as e:
        pass
    
    try:
        range_scanner.ui.user_interface.scan_static(
            bpy.context, 

            scannerObject=bpy.context.scene.objects["Camera"],

            resolutionX=320, fovX=57, resolutionY=240, fovY=43, resolutionPercentage=100,

            reflectivityLower=0.0, distanceLower=0.8, reflectivityUpper=0.0, distanceUpper=4, maxReflectionDepth=4,
            
            enableAnimation=False, frameStart=1, frameEnd=1, frameStep=1, frameRate=1,

            addNoise=False, noiseType='gaussian', mu=0.0, sigma=0.01, noiseAbsoluteOffset=0.0, noiseRelativeOffset=0.0,

            simulateRain=False, rainfallRate=0.0, 

            addMesh=False,

            exportLAS=False, exportHDF=False, exportCSV=False, exportYCB=True, exportSingleFrames=False,
            exportRenderedImage=False, exportSegmentedImage=False, exportPascalVoc=False, exportDepthmap=True, depthMinDistance=0.0, depthMaxDistance=5.0, 
            dataFilePath=output_dir, dataFileName=filename,
            
            debugLines=False, debugOutput=False, outputProgress=False, measureTime=False, singleRay=False, destinationObject=None, targetObject=None
        )
    except Exception as e:
        print(e)
        
    try:
        range_scanner.ui.user_interface.unregister()
    except Exception as e:
        pass
    

def generate_dataset(name):
    kinect_v1(base.output_dir, "{}".format(name))

    for obj in bpy.data.objects:
        if "Target" in obj.name:
            obj["inst_id"] = obj["object_id"]
            obj["sem_id"] = obj["cls_index"]
    result = bpycv.render_data()

    rgb_filepath = os.path.join(base.output_dir, "rgb-{}.jpg".format(name))
    cv2.imwrite(rgb_filepath, result["image"][..., ::-1], [cv2.IMWRITE_PNG_COMPRESSION, 0])  # transfer RGB image to opencv's BGR
    print("save to " + rgb_filepath)

    # save instance map as 16 bit png
    inst_filepath = os.path.join(base.output_dir, "inst-{}.png".format(name))
    cv2.imwrite(inst_filepath, result["inst"], [cv2.IMWRITE_PNG_COMPRESSION, 0])
    print("save to " + inst_filepath)

    sem_filepath = os.path.join(base.output_dir, "sem-{}.png".format(name))
    cv2.imwrite(sem_filepath, result["sem"], [cv2.IMWRITE_PNG_COMPRESSION, 0])
    print("save to " + sem_filepath)
    