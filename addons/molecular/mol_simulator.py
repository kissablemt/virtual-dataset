from time import perf_counter as clock, sleep, strftime, gmtime, time

import bpy
from mathutils import Vector
from mathutils.geometry import barycentric_transform as barycentric

from . import properties, simulate, core
from .utils import get_object, destroy_caches


class MolSimulator:
    def __init__(self, context):
        self.context = context
        properties.define_props()

        ## clean
        for ob in bpy.data.objects:
            destroy_caches(ob)

    def _modal(self):
        context = self.context
        scene = context.scene
        frame_end = scene.frame_end
        frame_current = scene.frame_current

        if frame_current == frame_end:
            if scene.mol_bake:
                fake_context = context.copy()
                for ob in bpy.data.objects:
                    obj = get_object(context, ob)
                    for psys in obj.particle_systems:
                        if psys.settings.mol_active and len(psys.particles):
                            fake_context["point_cache"] = psys.point_cache
                            bpy.ops.ptcache.bake_from_cache(fake_context)
            scene.render.frame_map_new = 1
            scene.frame_end = scene.mol_old_endframe
            context.view_layer.update()

            if frame_current == frame_end and scene.mol_render:
                bpy.ops.render.render(animation=True)

            scene.frame_set(frame=scene.frame_start)

            core.memfree()
            scene.mol_simrun = False
            mol_exportdata = scene.mol_exportdata
            mol_exportdata.clear()
            # print('-' * 50 + 'Molecular Sim end')
            
            return False            
        else:
            if frame_current == scene.frame_start:            
                scene.mol_stime = clock()
            mol_exportdata = context.scene.mol_exportdata
            mol_exportdata.clear()
            simulate.pack_data(context, False)
            mol_importdata = core.simulate(mol_exportdata)

            i = 0
            for ob in bpy.data.objects:
                obj = get_object(context, ob)

                for psys in obj.particle_systems:
                    if psys.settings.mol_active and len(psys.particles):
                        psys.particles.foreach_set('velocity', mol_importdata[1][i])
                        i += 1

            mol_substep = scene.mol_substep
            framesubstep = frame_current / (mol_substep + 1)        
            if framesubstep == int(framesubstep):
                etime = clock()
                # print("    frame " + str(framesubstep + 1) + ":")
                # print("      links created:", scene.mol_newlink)
                if scene.mol_totallink:
                    # print("      links broked :", scene.mol_deadlink)
                    # print("      total links:", scene.mol_totallink - scene.mol_totaldeadlink ,"/", scene.mol_totallink," (",round((((scene.mol_totallink - scene.mol_totaldeadlink) / scene.mol_totallink) * 100), 2), "%)")
                # print("      Molecular Script: " + str(round(etime - scene.mol_stime, 3)) + " sec")
                    pass
                remain = (((etime - scene.mol_stime) * (scene.mol_old_endframe - framesubstep - 1)))
                days = int(strftime('%d', gmtime(remain))) - 1
                scene.mol_timeremain = strftime(str(days) + ' days %H hours %M mins %S secs', gmtime(remain))
                # print("      Remaining estimated:", scene.mol_timeremain)
                scene.mol_newlink = 0
                scene.mol_deadlink = 0
                scene.mol_stime = clock()
                stime2 = clock()
            scene.mol_newlink += mol_importdata[2]
            scene.mol_deadlink += mol_importdata[3]
            scene.mol_totallink = mol_importdata[4]
            scene.mol_totaldeadlink = mol_importdata[5]
            
            scene.frame_set(frame=frame_current + 1)
            
            if framesubstep == int(framesubstep):
                etime2 = clock()
                # print("      Blender: " + str(round(etime2 - stime2, 3)) + " sec")
                stime2 = clock()
        return True
    

    def start(self):
        context = self.context
        print('Molecular Simulate Start' + '-' * 50)
        mol_stime = clock()
        scene = context.scene
        scene.mol_simrun = True
        scene.mol_minsize = 1000000000.0
        scene.mol_newlink = 0
        scene.mol_deadlink = 0
        scene.mol_totallink = 0
        scene.mol_totaldeadlink = 0
        scene.mol_timeremain = "...Simulating..."
        scene.frame_set(frame=scene.frame_start)
        scene.mol_old_endframe = scene.frame_end
        mol_substep = scene.mol_substep
        scene.render.frame_map_old = 1
        scene.render.frame_map_new = mol_substep + 1
        scene.frame_end *= mol_substep + 1

        if scene.mol_timescale_active == True:
            fps = scene.render.fps * scene.timescale
        else:
            fps = scene.render.fps

        cpu = scene.mol_cpu
        mol_exportdata = context.scene.mol_exportdata
        mol_exportdata.clear()
        mol_exportdata.append([fps, mol_substep, 0, 0, cpu])
        mol_stime = clock()
        simulate.pack_data(context, True)
        etime = clock()
        # print("  PackData take " + str(round(etime - mol_stime, 3)) + "sec")
        mol_stime = clock()
        mol_report = core.init(mol_exportdata)
        etime = clock()
        # print("  Export time take " + str(round(etime - mol_stime, 3)) + "sec")
        # print("  total numbers of particles: " + str(mol_report))
        # print("  start processing:")
        while self._modal():
            continue
        scene.frame_set(frame=scene.frame_end)
        print("Molecular Simulate Finished")
