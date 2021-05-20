"""
在main.py中调用build_scene.py的话不需要修改环境变量；
否则需要加入utils的路径
"""
import numpy as np
import bpy
import os
import importlib
from configs import base
from utils import blender as B

from addons import molecular

# modules_to_reload = [
#     molecular, 
# ]
# for m in modules_to_reload:
#     importlib.reload(m)

"""
容器基本无需更改，可适当调整xy方向大小
"""
def create_container() -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0))
    container = bpy.data.objects[-1]
    B.activate(container)
    container.name = container.data.name = "Container"
    

    z = 0.15 # location[2] = scale[2] = z 可以保证底部高度为0
    container.scale = (0.5, 0.5, z)
    container.location = (0.0, 0.0, z)

    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode = 'OBJECT')
    container.data.polygons[5].select = True
    bpy.ops.object.mode_set(mode = 'EDIT')

    bpy.ops.mesh.inset(thickness=0.045, depth=0, release_confirm=True)
    bpy.ops.mesh.extrude_context_move(MESH_OT_extrude_context={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 0, -0.40), "orient_type":'NORMAL', "orient_matrix":((0, 1, 0), (-1, 0, 0), (0, 0, 1)), "orient_matrix_type":'NORMAL', "constraint_axis":(False, False, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":True, "use_accurate":False})
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    ## Collision
    bpy.ops.object.modifier_add(type='COLLISION')
    bpy.context.object.collision.damping_factor = 1
    bpy.context.object.collision.damping_random = 1
    bpy.context.object.collision.friction_factor = 1
    bpy.context.object.collision.friction_random = 1

    ## Rigid Body
    bpy.ops.rigidbody.object_add()
    bpy.context.object.rigid_body.type = 'PASSIVE'
    ## Rigid Body -> Collisions
    bpy.context.object.rigid_body.collision_shape = 'MESH' 
    ## Rigid Body -> Collisions -> Sensitivity
    bpy.context.object.rigid_body.collision_margin = 0

    # 材质
    mat = bpy.data.materials.get("Container Material")
    if mat is None:
        # create material
        mat = bpy.data.materials.new(name="Container Material")
    
    # 材质贴图
    mat.use_nodes = True
    img = bpy.data.images.get('UV.jpg')
    if img is None:
        img = bpy.data.images.load(filepath=os.path.join(base.object_dir, "UV.jpg"))
    
    nodes = mat.node_tree.nodes
    bsdf = nodes["Principled BSDF"]
    texImage = nodes.new(type='ShaderNodeTexImage')
    texImage.image = img

    mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])

    # Assign it to object
    if container.data.materials:
        # assign to 1st material slot
        container.data.materials[0] = mat
    else:
        # no slots
        container.data.materials.append(mat)


    container.scale = (1.0, 1.0, 0.30)
    return container


"""
相机location设置应根据实际进行调整
"""
def create_camera() -> bpy.types.Object:
    camera_data = bpy.data.cameras.new(name='Camera')
    camera_object = bpy.data.objects.new('Camera', camera_data)
    bpy.context.scene.collection.objects.link(camera_object)
    bpy.context.scene.camera = camera_object
    camera_object.location = (0.0, 0.0, 3)
    return camera_object


def create_light(location) -> bpy.types.Object:
    light_data = bpy.data.lights.new(name='Light', type="POINT")
    light_object = bpy.data.objects.new('Light', light_data)
    bpy.context.scene.collection.objects.link(light_object)
    light_object.location = location
    return light_object


"""
工件location设置应放置到不可见位置，该函数只用于工件模板创建
工件scale设置应根据实际进行调整
工件rotation_euler设置为(90°,70°,90°)时，工件基本平放
"""
def create_target() -> bpy.types.Object:
    B.import_stl(filepath=os.path.join(base.object_dir, "30D_831_673____PCA_TM__003_____VERST_TUERFESTSTEL________EDAG_20180824.STL"))
    # bpy.ops.mesh.primitive_monkey_add(enter_editmode=False, align='WORLD', location=(0, 0, 0))

    target = bpy.context.object
    print(target)
    B.activate(target)
    target.name = target.data.name = "Target" 
    target.scale = (0.015, 0.015, 0.015)
    target.location = (0, 0, -200)
    target.rotation_euler = (np.radians(90), np.radians(70), np.radians(90))
    
    mat = bpy.data.materials.get("Material")
    if mat is None:
        # create material
        mat = bpy.data.materials.new(name="Material")

    # Assign it to object
    if target.data.materials:
        # assign to 1st material slot
        target.data.materials[0] = mat
    else:
        # no slots
        target.data.materials.append(mat)
    return target


class Emitter:
    def __init__(self, target_object: bpy.types.Object, random_seed=0):
        self.object = target_object
        self.random_seed = random_seed
        self.activate()
        bpy.context.object.show_instancer_for_viewport = False
        bpy.ops.object.particle_system_add() 
        *_, self.settings = iter(bpy.data.particles)
    
    def set_particle_system(self, particle_settings: dict) -> None:
        for key, val in particle_settings.items():
            setattr(self.settings, key, val)
        self.object.particle_systems["ParticleSettings"].seed = self.random_seed

    
    def get_particle_system(self) -> bpy.types.ParticleSettings:
        return self.settings
    
    def set_object(self, target_object: bpy.types.Object) -> None:
        self.object = target_object
        
    def hide_object(self) -> None:
        self.activate()
        bpy.ops.object.hide_view_set(unselected=False)
    
    def show_object(self) -> None:
        self.activate()
        bpy.ops.object.hide_view_clear()
        
    def get_object(self: bpy.types.Object):
        return self.object
    
    def activate(self) -> None:
        bpy.context.view_layer.objects.active = self.object
        self.object.select_set(True)
        
    def __del__(self):
        self.activate()
        bpy.ops.object.particle_system_remove()
        B.remove(self.object)
    
def create_emitter(random_seed=0):
    bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 1))
    obj = bpy.context.object
    obj.name = "Emitter"
    obj.scale = (0.5, 0.5, 1.0)
    emitter = Emitter(obj, random_seed=random_seed)
    ## https://docs.blender.org/manual/en/latest/physics/particles/emitter/rotation.html
    par_sets = {
        ## Emission,
        "count": 30,
        "frame_end": 200,
        "lifetime": 500,

        ## Emission -> Source,
        "emit_from": 'VOLUME',
        # "distribution": 'GRID',
        # "grid_resolution": 2,
        # "grid_random": 1,

        "distribution": 'JIT',
        # "use_emit_random": True,

        ## Rotation,
        "use_rotations": True,
        "rotation_factor_random": 1,
        "phase_factor": 1,
        "phase_factor_random": 2,
        "use_dynamic_rotation": True,

        ## Physics -> Deflection,
        "use_size_deflect": True,

        ## Render,
        "render_type": 'OBJECT',
        "particle_size": 0.1,
        "instance_object": bpy.data.objects["Target"],

        ## Molecular(Add-on),
        "mol_active": True,

        ## Molecular(Add-on) -> Collision,
        "mol_selfcollision_active": True,
        "mol_othercollision_active": True,
        "mol_collision_group": 5,

        "mol_friction": 0.0,
        "mol_collision_damp": 0.9999,
    }
    emitter.set_particle_system(particle_settings=par_sets)
    return emitter

def make_real():
    bpy.ops.object.duplicates_make_real() 
    bpy.ops.rigidbody.objects_add(type='ACTIVE')
    bpy.ops.object.move_to_collection(collection_index=0, is_new=True, new_collection_name="Particles")
    
    particles = bpy.data.collections["Particles"].all_objects
    for obj in particles:
        B.activate(obj)
        bpy.context.object.rigid_body.collision_shape = 'MESH'
        # bpy.context.object.rigid_body.collision_shape = 'CONVEX_HULL'
        
        bpy.context.object.rigid_body.friction = 1
        bpy.context.object.rigid_body.restitution = 1
        bpy.context.object.rigid_body.collision_margin = 0.04
        
    for obj in particles:
        # print(obj.location, obj.matrix_world.translation)
        obj.location = obj.matrix_world.translation
    B.update()
    bpy.context.scene.frame_set(1)

def run_emitter(random_seed=0):
    try:
        molecular.register()
    except Exception as e:
        print("molecular.register(): ", e)
        
    try:
        emitter = create_emitter(random_seed)
        emitter.activate()
        mol_sim = molecular.mol_simulator.MolSimulator(bpy.context)
        bpy.ops.ptcache.free_bake_all()
        bpy.context.scene.frame_end = 200
        bpy.context.scene.mol_substep = 4

        mol_sim.start()
    except Exception as e:
        print("test_emitter->mol_sim.start(): ", e)
        
    try:
        make_real()
        del emitter
        pass
    except Exception as e:
        print("test_emitter->make_real(): ", e)
        
    try:
        molecular.unregister()
    except Exception as e:
        print("molecular.unregister(): ", e)
    return 0

def build_scene(random_seed=0):
    B.clean()
    container = create_container()
    cameara = create_camera() 
    light1 = create_light((0.5, 0.5, 1))
    light2 = create_light((-0.5, -0.5, 1))
    target = create_target()
    run_emitter(random_seed)

    objs = []
    for obj in bpy.data.objects:
        if (obj.matrix_world @ obj.location)[2] > 0 and id(obj.data) == id(target.data):
            objs.append(B.copy(obj))
    B.remove(target.data)
    B.remove(bpy.data.collections["Particles"])

    for i, obj in enumerate(objs):
        obj["cls_index"] = 1
        obj["object_id"] = i + 1