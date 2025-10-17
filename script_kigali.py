

# export a didge-lab geometry to blender

import bpy
import bmesh
import math
import numpy as np
import sys
import json

geo=[[0.0, 32.0], [54.9, 34.7], [137.0, 31.6], [168.0, 38.3], [257.2, 35.1], [337.3, 36.0], [409.5, 38.6], [471.6, 36.3], [549.5, 37.1], [609.9, 35.0], [669.9, 32.5], [716.0, 33.6], [775.8, 29.5], [883.5, 29.4], [950.5, 31.8], [1021.2, 28.8], [1099.5, 33.0], [1145.8, 37.3], [1198.3, 33.3], [1275.8, 37.8], [1349.6, 36.4], [1425.8, 36.7], [1466.3, 36.7], [1539.6, 44.0], [1638.8, 47.7], [1694.9, 48.5], [1704.3, 47.9], [1734.2, 58.2], [1764.1, 69.1], [1794.1, 79.3], [1824.0, 86.0], [1854.0, 86.8], [1883.9, 83.7], [1913.9, 78.2], [1943.8, 76.3], [1973.8, 65.0], [2019.0, 52.4], [2113.8, 49.1], [2170.3, 47.8], [2228.8, 51.5], [2313.6, 48.9], [2355.3, 45.0], [2420.2, 49.8], [2513.2, 53.5], [2578.6, 51.3], [2652.2, 52.6], [2712.6, 58.2], [2781.4, 56.1], [2836.5, 61.1]]

# geo = [[0, 32], [2000, 32]]
splits = [
 200,
 400,
 500,
 600,
 800,
 1000,
 1170,
 1280,
 1450,
 1550,
 1650,
 1800,
 2000,
 2100,
 2200,
 2400,
 2600]

# debug configuration to creaty only a subset of the meshes
create_partly = False
# create_partly = True
# create_partly_ids = [14]

split_it = True  # flat to switch splitting on and off

n_circle_segments = 64  # how many segments make a circle
z_resolution = 4  # create a segment every z_resolution mm
wall_thickness = 4 # wall thickness

# mouthpiece parameters
mouthpiece_length=10 # how long is the mouthpiece part in mm
mouthpiece_widening=7  # how many mm does in widen
mouthpiece_r=1  # the size of the rounding at the inner mouth end of the mouthpiece
mouthpiece_resolution=0.4  # the mouthpiece has a finer resolution

#joint parameters
joint_length = 3   # how long are the joints in multiples of the resolution
joint_sharp_edge_thickness = 0.5  # thickness of the walls at the joints

scene = bpy.context.scene

if not split_it:
    splits = [geo[-1][0]]

# create a mesh object and insert into scene
def object_from_data(data, name, scene, select=True):
    
    clean_mesh = True # remove loose vertices

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(data['verts'], data['edges'], data['faces'])
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)

    bpy.context.view_layer.objects.active = obj
    
    # remove all vertices that are not connected to a face
    obj.select_set(True)
    bpy.ops.object.mode_set(mode = 'EDIT') 
    bpy.ops.mesh.select_mode(type="FACE")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.ops.mesh.select_mode(type="FACE")
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.ops.mesh.select_all(action="INVERT")

    if clean_mesh:
        bpy.ops.mesh.delete() 

    # remove interior faces
    bpy.ops.mesh.select_interior_faces()
    bpy.ops.mesh.select_less()
    if clean_mesh:
        bpy.ops.mesh.delete() 
    
    # rotate mesh
    bpy.context.active_object.rotation_euler[0] = math.radians(90)
    
    mesh.validate(verbose=True)

    recalculate_normals(bpy.context.active_object)

    return obj


# create one ring of vertizes
def make_vertex_ring(data, z, diameter, leave_out=[]):
    start_vertex=len(data["verts"])
    
    # z = z/1000
    # diameter = diameter/1000
    this_circle_n_segments = n_circle_segments - len(leave_out)
    for i in range(n_circle_segments):
        
        if i in leave_out:
            continue
        a = 2*np.pi*i/n_circle_segments
        x = 0.5*diameter*np.sin(a)
        y = 0.5*diameter*np.cos(a)
        data["verts"].append((x,y,z))

    start_edge = len(data["edges"])
    for i in range(start_vertex, start_vertex + n_circle_segments):        
        if i in leave_out:
            continue
        j=i-1 if i>start_vertex else start_vertex+this_circle_n_segments-1
        data["edges"].append((i,j))
    
    return start_vertex, start_edge


# recalculate normals because otherwise the mesh will have 'bad contiguous edges'
def recalculate_normals(obj):
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False) # Recalculate to face outwards
    bpy.ops.object.mode_set(mode='OBJECT')


# get the diameter of the geometry at position x
def diameter_at_z(geo, x):

    assert x<=geo[-1][0]

    if x==0:
        return geo[0][1]

    for i in range(len(geo)):
        if x<geo[i][0]:
            break

    x1=geo[i-1][0]
    y1=geo[i-1][1]
    x2=geo[i][0]
    y2=geo[i][1]

    ydiff=(y2-y1)/2
    xdiff=(x2-x1)

    winkel=math.atan(ydiff/xdiff)
    y=math.tan(winkel)*(x-x1)*2+y1
    return y

"""
connect two rings with edges and faces
"""
def connect_rings(data, index1, index2, leave_out = []):
    start_edge = len(data["edges"])
    for i in range(n_circle_segments):
        if i not in leave_out:
            data["edges"].append((index1[0]+i, index2[0]+i))
    
    for i in range(n_circle_segments):
        if i in leave_out:
            continue
        j = i-1 if i>0 else n_circle_segments-1
        face = (
            index1[0]+i,
            index1[0]+j,
            index2[0]+j,
            index2[0]+i,
        )
        data["faces"].append(face)

make_data = lambda : {"verts": [], "edges": [], "faces": []}

"""
Create the meshes of all the individual didgeridoo segments
"""
def create_mesh():

    print('create mesh')
    for i_split in range(len(splits)):

        print(f'split {i_split}')
        if create_partly and i_split not in create_partly_ids:
            continue

        # print(f"split {i_split}")

        last_split_z = mouthpiece_length
        if i_split > 0:
            last_split_z = splits[i_split-1] - joint_length * z_resolution

        end_z = min(splits[i_split], geo[-1][0])

        zs = []
        if i_split == 0:
            # add mouthpiece with finer resolution
            zs.extend(list(np.arange(0, mouthpiece_length, mouthpiece_resolution)))

        zs.extend(list(np.arange(last_split_z, end_z, z_resolution)))

        if end_z not in zs:
            zs.append(end_z)
        
        inner_diameters = []
        outer_diameters = []
        # print(f"coordinates {min(zs)}, {max(zs)}")

        # determine if we need a mouthpiece joint and where it will start
        joint_z_mouthpiece_pos = None
        if i_split > 0:
            joint_z_mouthpiece_pos = zs[0] + z_resolution * joint_length
            if joint_z_mouthpiece_pos not in zs:
                zs.append(joint_z_mouthpiece_pos)

        # determine if we need a bellend joint and where it will start
        joint_z_bellend_pos = None
        if i_split < len(splits)-1:
            joint_z_bellend_pos = zs[-1] - z_resolution * joint_length
            if joint_z_bellend_pos not in zs:
                zs.append(joint_z_bellend_pos)

        zs = sorted(zs)
        # print(f"dimensions {min(zs)}, {max(zs)}, end_z {end_z}")

        # geometry
        data = make_data()

        last_outer_ring = None
        last_inner_ring = None
        for z in zs:

            d = diameter_at_z(geo, z)

            outer_diameter = d+2*wall_thickness
            inner_diameter = d

            if i_split == 0 and z < mouthpiece_length:\
                # create mouthpiece
                i = np.power(1-z/mouthpiece_length, 2)
                outer_diameter += i*mouthpiece_widening

                if z<=mouthpiece_r:
                    i = 1-z/mouthpiece_r
                    inner_diameter += i*mouthpiece_r

                inner_ring = make_vertex_ring(data, z, inner_diameter)
                outer_ring = make_vertex_ring(data, z, outer_diameter)
                if last_outer_ring is not None and last_inner_ring is not None:
                    connect_rings(data, inner_ring, last_inner_ring)
                    connect_rings(data, outer_ring, last_outer_ring)
                last_inner_ring = inner_ring
                last_outer_ring = outer_ring

            elif joint_z_mouthpiece_pos and z <= joint_z_mouthpiece_pos:
                # joint directed towards mouthpiece
                l = joint_length * wall_thickness # length of the joint
                a = -((outer_diameter-2*joint_sharp_edge_thickness)-(inner_diameter+2*joint_sharp_edge_thickness))/l # slope of the joint
                _z = l-(z-last_split_z)
                outer_diameter = (outer_diameter - 2*joint_sharp_edge_thickness) + a*_z

                inner_ring = make_vertex_ring(data, z, inner_diameter)
                if z == joint_z_mouthpiece_pos:
                    middle_ring = make_vertex_ring(data, z, outer_diameter)
                    outer_ring = make_vertex_ring(data, z, outer_diameter +2*joint_sharp_edge_thickness)
                    connect_rings(data, middle_ring, outer_ring)
                    connect_rings(data, inner_ring, last_inner_ring)
                    connect_rings(data, middle_ring, last_outer_ring)
                else:
                    outer_ring = make_vertex_ring(data, z, outer_diameter)

                    if last_outer_ring is not None and last_inner_ring is not None:
                        connect_rings(data, inner_ring, last_inner_ring)
                        connect_rings(data, outer_ring, last_outer_ring)

                last_inner_ring = inner_ring

                if z == joint_z_mouthpiece_pos:
                    last_outer_ring = outer_ring
                else:
                    last_outer_ring = outer_ring

            elif joint_z_bellend_pos and z >= joint_z_bellend_pos:
                # bellend facing joint

                l = joint_length * wall_thickness # length of the joint
                a = ((outer_diameter-2*joint_sharp_edge_thickness)-(inner_diameter+2*joint_sharp_edge_thickness))/l # slope of the joint
                _z = z-joint_z_bellend_pos
                inner_diameter += 2*joint_sharp_edge_thickness + _z*a                

                outer_ring = make_vertex_ring(data, z, outer_diameter)
                if z == joint_z_bellend_pos:
                    inner_ring = make_vertex_ring(data, z, d)
                    extra_ring = make_vertex_ring(data, z, d+2*joint_sharp_edge_thickness)
                    connect_rings(data, inner_ring, extra_ring)
                else:
                    inner_ring = make_vertex_ring(data, z, inner_diameter)

                connect_rings(data, inner_ring, last_inner_ring)
                connect_rings(data, outer_ring, last_outer_ring)

                last_outer_ring = outer_ring
                if z == joint_z_bellend_pos:
                    last_inner_ring = extra_ring
                else:
                    last_inner_ring = inner_ring
            else:
                # normal part
                inner_ring = make_vertex_ring(data, z, inner_diameter)
                outer_ring = make_vertex_ring(data, z, outer_diameter)
                if last_outer_ring is not None and last_inner_ring is not None:
                    connect_rings(data, inner_ring, last_inner_ring)
                    connect_rings(data, outer_ring, last_outer_ring)
                last_inner_ring = inner_ring
                last_outer_ring = outer_ring

            # add the vertical faces at beginning and end
            if z == zs[0] or z == zs[-1]:
                connect_rings(data, inner_ring, outer_ring)

        object_from_data(data, f"{i_split}", scene)

def make_nose(mesh1_name, mesh2_name, z, diameter):
    
    joint1 = bpy.data.objects[mesh1_name]
    joint2 = bpy.data.objects[mesh2_name]

    z1 = z+0.005
    z0 = z1 - joint_length * z_resolution

    x0 = 0
    x1 = diameter
    y0 = -0.17*diameter
    y1 = 0.17*diameter

    verts = []
    verts.append((x0, y1, z1))
    verts.append((x1, y1, z1))
    verts.append((x1, y0, z1))
    verts.append((x0, y0, z1))
    verts.append((x0, 0, z0))
    verts.append((x1, 0, z0))
    
    data = make_data()
    data["verts"] = verts
    
    data["edges"].append((0,1)) # basis
    data["edges"].append((1,2))
    data["edges"].append((2,3))
    data["edges"].append((3,0))
    
    data["edges"].append((4,5)) # oben
    
    data["edges"].append((5,1)) # eine seite
    data["edges"].append((0,4))

    data["edges"].append((5,2)) # eine seite
    data["edges"].append((3,4))
    
    data["faces"].append((0,1,2,3)) # unterseite
    data["faces"].append((4,5,1,0))
    data["faces"].append((4,5,2,3))
    
    data["faces"].append((0,3,4))
    data["faces"].append((1,2,5))
    
    nose1 = object_from_data(data, "nose1", scene)
    nose2 = object_from_data(data, "nose2", scene)

    bpy.ops.object.mode_set(mode = 'OBJECT') 
    mod_bool =  nose2.modifiers.new('my_bool_mod_2', 'BOOLEAN')
    mod_bool.operation = 'INTERSECT'
    mod_bool.object = joint1
    mod_bool.solver = "FAST"
    mod_bool.double_threshold /= 10
    res = bpy.ops.object.modifier_apply(modifier = 'my_bool_mod_2')

    bpy.ops.object.mode_set(mode = 'OBJECT') 
    mod_bool =  joint1.modifiers.new('my_bool_mod', 'BOOLEAN')
    mod_bool.operation = 'DIFFERENCE'
    mod_bool.solver = "FAST"    
    mod_bool.object = nose1
    bpy.context.view_layer.objects.active = joint1
    mod_bool.double_threshold /= 10
    res = bpy.ops.object.modifier_apply(modifier = 'my_bool_mod')

    # delete nose 1
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects["nose1"].select_set(True)
    bpy.ops.object.delete()   

    bpy.ops.object.mode_set(mode = 'OBJECT') 
    bpy.ops.object.select_all(action='DESELECT')
    joint2.select_set(True)
    bpy.data.objects["nose2"].select_set(True)
    bpy.context.view_layer.objects.active = joint2
    bpy.ops.object.join()

def add_curve_modifier():
    # add curves 
    if "Curve" in bpy.data.objects:
        for obj in bpy.data.objects:
            if obj.name != "Curve":
                mod = obj.modifiers.new("Curve", 'CURVE')
                mod.deform_axis = "NEG_Y"
                mod.object = bpy.data.objects["Curve"]

def make_noses():
    for i in range(1, len(splits)):
        if create_partly and (i-1 not in create_partly_ids or i not in create_partly_ids):
            continue
        make_nose(str(i-1), str(i), splits[i-1], diameter_at_z(geo, splits[i-1]))


def delete_all_objects():
    for obj in bpy.data.objects:
        if obj.name.lower() != "curve":
            bpy.data.objects.remove(obj, do_unlink=True)

def run():

    print('#####')
    print('Execute didge script')
    print('#####')
    delete_all_objects()
    create_mesh()
    make_noses()
    add_curve_modifier()

run()            