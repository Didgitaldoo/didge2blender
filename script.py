
# export a didge-lab geometry to blender

import bpy
import bmesh
import math
import numpy as np
import sys
import json

#infile="/home/jan/workspaces/didge-sound/production/arusha_2/didgelab/0_geo.txt"
#f=open(infile, "r")
#geo=json.load(f)
#f.close()

geo = [[0.0, 31.0],
 [82.3, 31.37],
 [172.6, 31.74],
 [289.0, 32.01],
 [349.5, 33.99],
 [425.0, 35.87],
 [511.0, 38.129999999999995],
 [581.0, 39.800000000000004],
 [651.0, 41.47],
 [740.0, 43.73],
 [807.0, 46.870000000000005],
 [868.0, 50.0],
 [1012.9999999999999, 50.67],
 [1162.0, 59.67],
 [1230.5, 64.0],
 [1319.0, 68.33],
 [1421.0, 74.67],
 [1478.5, 79.5],
 [1520.0, 84.0],
 [1642.5, 84.6],
 [1789.0, 85.0]]

split_it = True  # flat to switch splitting on and off

SPLIT_WIDENING = "split_widening"
SPLIT_NARROWING = "split_narrowing"

splits = [
    {#0
        "z": 0,
        "type": SPLIT_NARROWING
    },
    {#0
        "z": 100,
        "type": SPLIT_WIDENING
    },
    {#1
        "z": 200.0,
        "type": SPLIT_WIDENING
    },
    {#1
        "z": 300.0,
        "type": SPLIT_WIDENING
    },
    {#2
        "z": 400.0,
        "type": SPLIT_WIDENING
    },
    {#3
        "z": 550.0,
        "type": SPLIT_WIDENING
    },
    {#4
        "z": 720.0,
        "type": SPLIT_NARROWING
    },
    {#5
        "z": 850.0,
        "type": SPLIT_NARROWING
    },
    {#6
        "z": 950.0,
        "type": SPLIT_NARROWING
    },
    {#6
        "z": 1100.0,
        "type": SPLIT_NARROWING
    },
    {#6
        "z": 1210.0,
        "type": SPLIT_NARROWING
    },
    {#8
        "z": 1320.0,
        "type": SPLIT_WIDENING
    },
    {
        "z": 1480.0,
        "type": SPLIT_WIDENING
    },
    {
        "z": 1590.0,
        "type": SPLIT_WIDENING
    },
    {
        "z": 1700.0,
        "type": SPLIT_WIDENING
    },
]

    

# print("geo", geo)
# print("split positions", split_positions)

joint_length = 15   # how long are the joints?
n_circle_segments = 64  # how many segments make a circle
z_resolution = 4  # create a segment every z_resolution mm
wall_thickness = 4 # wall thickness


# these indizes define on which parts of the circle should be a nose and the cut for the nose
nose_size = 0.2 # the size of the nose. 0.1 means that 10% of the ring is the nose
nose_neg_leave_indizes = np.arange(1, np.ceil(nose_size*n_circle_segments)+1, 1)
nose_neg_leave_indizes = [int(x) for x in nose_neg_leave_indizes]
nose_pos_leave_indizes = list(filter(lambda x : x not in nose_neg_leave_indizes, range(n_circle_segments)))


# mouthpiece parameters
mouthpiece_length=10 # how long is the mouthpiece part in mm
mouthpiece_widening=7  # how many mm does in widen
mouthpiece_r=1  # the size of the rounding at the inner mouth end of the mouthpiece
mouthpiece_resolution=0.4  # the mouthpiece has a finer resolution

scene = bpy.context.scene

# debug function -> create only some of the parts

create_partly = False
#create_partly = True
#create_ids = [0,1,2,3,4]

curve = None
numbers = [str(i) for i in range(10)]

for obj in bpy.data.objects:
    if len(obj.name)>1 and obj.name[0] in numbers and obj.name[1] in numbers:
        bpy.data.objects[obj.name].select_set(True)
        bpy.ops.object.delete()     
    #else:
    #    print("do not delete", obj.name)

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
    
    # recalculate normals to fix bad contingent edges
    # somehow it works from blender ui but not from python
    #bpy.ops.mesh.select_all(action='SELECT')
    #bpy.ops.mesh.normals_make_consistent(inside=False)

    # remove interior faces
    bpy.ops.mesh.select_interior_faces()
    bpy.ops.mesh.select_less()
    if clean_mesh:
        bpy.ops.mesh.delete() 
    
    # rotate mesh
    bpy.context.active_object.rotation_euler[0] = math.radians(90)
    
    mesh.validate(verbose=True)

    return obj


# create one ring of vertizes
def make_vertex_ring(data, z, diameter, leave_out=[]):
    start_vertex=len(data["verts"])
    
    z = z/1000
    diameter = diameter/1000
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


# connect two rings with edges and faces
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

# create all z positions of rings of the geometry
zs = set([float(z) for z in np.arange(0, geo[-1][0], z_resolution)])

for g in geo:
    zs.add(g[0])

if split_it:
    for split in splits:
        z = split["z"]
        zs.add(z)
        zs.add(z+joint_length/2)
        zs.add(z-joint_length/2)
zs.add(mouthpiece_length)

zs = sorted(list(zs))

# define inner diameters
diameter_innen = [diameter_at_z(geo, z) for z in zs]
diameter_aussen = [d + 2*wall_thickness for d in diameter_innen]
fine_geo = [(zs[i], diameter_innen[i], diameter_aussen[i]) for i in range(len(zs))]

# get a part of the geometry
get_subgeo = lambda geo, z1, z2 : list(filter(lambda segment: segment[0]>=z1 and segment[0]<=z2, geo))

# divide geo by parts
parts = []

pos=0

if not split_it:
    splits = [
    {#0
        "z": geo[0][0],
        "type": SPLIT_WIDENING
    }    
    ]


for split in splits:

    if len(parts)==0:
        parts.append({
            "type": "mouthpiece",
            "name": "%02d" % len(parts) + "_mouthpiece",
            "geo": get_subgeo(fine_geo, pos, mouthpiece_length)
        })
        pos = mouthpiece_length
    else:
        parts.append({
            "type": "normal",
            "name": "%02d" % len(parts) + "_normal",
            "geo": get_subgeo(fine_geo, pos, split["z"]-joint_length/2)
        })
        parts.append({
            "type": "joint1",
            "name": "%02d" % len(parts) + "_joint1",
            "geo": get_subgeo(fine_geo, split["z"]-joint_length/2, split["z"]+joint_length/2),
            "meta": {
                "type": split["type"]
            }
        })
        parts.append({
            "type": "joint2",
            "name": "%02d" % len(parts) + "_joint2",
            "geo": get_subgeo(fine_geo, split["z"]-joint_length/2, split["z"]+joint_length/2),
            "meta": {
                "type": split["type"]
            }
        })
        parts.append({
            "type": "nose"
        })
        
        pos = split["z"]+joint_length/2
        
parts.append({
    "type": "normal",
    "name": "%02d" % len(parts) + "_normal",
    "geo": get_subgeo(fine_geo, split["z"]+joint_length/2, zs[-1])
})

# create an empty mesh structure
make_data = lambda : {"verts": [], "edges": [], "faces": []}

def make_mouthpiece(part):
    data = make_data()
    zs = set(np.arange(0,mouthpiece_length, mouthpiece_resolution))
    zs.add(mouthpiece_length)
    zs = sorted(list(zs))
    
    inner_diameters = [diameter_at_z(geo, z) for z in zs]
    outer_diameters = np.array(inner_diameters).copy() + 2*wall_thickness
    
    # round the mouthpiece on the inside
    n_segments = int(mouthpiece_r / mouthpiece_resolution)
    mouthpiece_y = [mouthpiece_r-np.sin(0.5*i*np.pi/n_segments)*mouthpiece_r for i in range(n_segments)]
    for i in range(len(mouthpiece_y)):
        inner_diameters[i] += mouthpiece_y[i]
        
    # widen on the outside
    sigmoid = lambda x,d: d*(1-1 / (1 + math.exp(-x)))
    smin=-5
    smax=10
    
    x=np.arange(smin, smax, (0.000001+smax-smin)/len(zs))
    y=[sigmoid(a, mouthpiece_widening) for a in x]
    
    outer_diameters += y
    
    # create mesh
    segments = []
    for i in range(len(zs)):
        r1=make_vertex_ring(data, zs[i], inner_diameters[i])
        r2=make_vertex_ring(data, zs[i], outer_diameters[i])
        segments.append((r1, r2))

        if len(segments)>1:
            # vertical edges and faces
            connect_rings(data, r1, segments[-2][0])
            connect_rings(data, r2, segments[-2][1]) 
               
    # horizontal edges and faces
    if len(segments)>1:
        connect_rings(data, segments[0][0], segments[0][1])
        connect_rings(data, segments[-1][0], segments[-1][1])
        
    return object_from_data(data, part["name"], scene)
    
# make a normal part
def make_normal_part(part):
    segments = []
    data = make_data()
    for z, inner_diameter, outer_diameter in part["geo"]:
        r1=make_vertex_ring(data, z, inner_diameter)
        r2=make_vertex_ring(data, z, outer_diameter)
        segments.append((r1, r2))
        
        if len(segments)>1:
            # vertical edges and faces
            connect_rings(data, r1, segments[-2][0])
            connect_rings(data, r2, segments[-2][1])
            
    # horizontal edges and faces
    if len(segments)>1:
        connect_rings(data, segments[0][0], segments[0][1])
        connect_rings(data, segments[-1][0], segments[-1][1])
        
    return object_from_data(data, part["name"], scene)
        
# make the outer part of a joint
def make_joint1(part):
    
    data = make_data()
    segments=[]
    
    # change geometry to add a profile in the first 2 mm
    i_profile=0
    
    while part["geo"][i_profile][0] < part["geo"][0][0]+wall_thickness:
        i_profile+=1
        
    part_geo = []
    z0 = part["geo"][0][0]
    z1 = z0+wall_thickness
    
    if part["meta"]["type"] == SPLIT_WIDENING:        
        inner_diameter = diameter_at_z(geo, z0)
        outer_diameter = inner_diameter + 2*wall_thickness
        part_geo.append((z0, inner_diameter, outer_diameter))

        inner_diameter = diameter_at_z(geo, z1) + wall_thickness
        outer_diameter = inner_diameter + wall_thickness
        part_geo.append((z1, inner_diameter, outer_diameter))
    else:
        inner_diameter = diameter_at_z(geo, z0)
        outer_diameter = inner_diameter + 2*wall_thickness
        part_geo.append((z0, outer_diameter, outer_diameter))

        inner_diameter = diameter_at_z(geo, z1) + wall_thickness
        outer_diameter = inner_diameter + wall_thickness
        part_geo.append((z1, inner_diameter, outer_diameter))

    i_profile_end=len(part["geo"])-1
    while part["geo"][i_profile_end][0] < part["geo"][-1][0]-wall_thickness:
        i_profile_end-=1
        
    for z, inner_diameter, outer_diameter in part["geo"][i_profile:i_profile_end]:
        part_geo.append([z, inner_diameter + 0.5*(outer_diameter-inner_diameter), outer_diameter])
        
    for z, inner_diameter, outer_diameter in part_geo[0:-1]:
        
        r1=make_vertex_ring(data, z, inner_diameter) 
        r2=make_vertex_ring(data, z, outer_diameter)  
        segments.append((r1, r2))
        
        if len(segments)>1:
            # vertical edges and faces
            connect_rings(data, r1, segments[-2][0])
            connect_rings(data, r2, segments[-2][1])
    
    # make end profile - segment one
    z = part["geo"][-1][0]-wall_thickness
    inner_diameter = diameter_at_z(geo, z) + wall_thickness
    outer_diameter = inner_diameter + wall_thickness
    r1=make_vertex_ring(data, z, inner_diameter) 
    r2=make_vertex_ring(data, z, outer_diameter)  
    segments.append((r1, r2))
    connect_rings(data, r1, segments[-2][0])
    connect_rings(data, r2, segments[-2][1])
    
    # make end profile - segment two

    if part["meta"]["type"] == SPLIT_WIDENING:
        z, inner_diameter, outer_diameter = part["geo"][-1]
        r2=make_vertex_ring(data, z, outer_diameter)  
        segments.append((r2, r2))
        connect_rings(data, r2, segments[-2][0])
        connect_rings(data, r2, segments[-2][1])
    else:
        z, inner_diameter, outer_diameter = part["geo"][-1]
        r1=make_vertex_ring(data, z, inner_diameter)  
        r2=make_vertex_ring(data, z, outer_diameter)  
        segments.append((r1, r2))
        connect_rings(data, r1, segments[-2][0])
        connect_rings(data, r2, segments[-2][1])
        
        connect_rings(data, segments[-1][0], segments[-1][1])
        
    # horizontal edges and faces
    connect_rings(data, segments[0][0], segments[0][1])
    # connect_rings(data, segments[-1][0], segments[-1][1])
    
    return object_from_data(data, part["name"], scene)
        
# make the inner part of the joint
def make_joint2(part):
    
    # create first 2 mm with profile
    i_profile=0
    
    while part["geo"][i_profile][0] < part["geo"][0][0]+wall_thickness:
        i_profile+=1
        
    part_geo = []
    
    data = make_data()
    segments = []
    
    z0 = part["geo"][0][0]
    z1 = z0+wall_thickness
    
    if part["meta"]["type"] == SPLIT_WIDENING:
        inner_diameter = diameter_at_z(geo, z0)
        r0=make_vertex_ring(data, z0, inner_diameter)
        
        inner_diameter = diameter_at_z(geo, z1)
        r1=make_vertex_ring(data, z1, inner_diameter)
        r2=make_vertex_ring(data, z1, inner_diameter + wall_thickness)
        
        segments.append((r1, r2))

        connect_rings(data, r1, r0)
        connect_rings(data, r2, r0)
    else:
        inner_diameter = diameter_at_z(geo, z0)
        r1=make_vertex_ring(data, z0, inner_diameter)
        r2=make_vertex_ring(data, z0, inner_diameter + 2*wall_thickness)
        segments.append((r1, r2))

        inner_diameter = diameter_at_z(geo, z1)
        r1=make_vertex_ring(data, z1, inner_diameter)
        r2=make_vertex_ring(data, z1, inner_diameter + wall_thickness)
        segments.append((r1, r2))
        
        connect_rings(data, r1, segments[-2][0])
        connect_rings(data, r2, segments[-2][1])
        
    
    i_profile_end=len(part["geo"])-1
    while part["geo"][i_profile_end][0] < part["geo"][-1][0]-wall_thickness:
        i_profile_end-=1

    for z, inner_diameter, outer_diameter in part["geo"][i_profile:i_profile_end-1]:
        diameter = diameter_at_z(geo, z)
        r1=make_vertex_ring(data, z, inner_diameter)
        r2=make_vertex_ring(data, z, inner_diameter + 0.5*(outer_diameter-inner_diameter))
        # r3 = make_vertex_ring(data, z, outer_diameter)
        segments.append((r1, r2))
        
        if len(segments)>1:
            # joint vertical edges and faces
            connect_rings(data, r1, segments[-2][0])
            connect_rings(data, r2, segments[-2][1])
            

    # make end profile - segment one
    z = part["geo"][-1][0]-wall_thickness
    inner_diameter = diameter_at_z(geo, z)
    outer_diameter = inner_diameter + wall_thickness
    r1=make_vertex_ring(data, z, inner_diameter) 
    r2=make_vertex_ring(data, z, outer_diameter)  
    segments.append((r1, r2))
    
    connect_rings(data, r1, segments[-2][0])
    connect_rings(data, r2, segments[-2][1])
        
    # make end profile - segment two
    
    if part["meta"]["type"] == SPLIT_WIDENING:
        z, inner_diameter, outer_diameter = part["geo"][-1]
        r1=make_vertex_ring(data, z, inner_diameter)  
        r2=make_vertex_ring(data, z, outer_diameter)  
        segments.append((r1, r2))
        connect_rings(data, r1, segments[-2][0])
        connect_rings(data, r2, segments[-2][1])
        # close mesh horizontal with faces and edges
        connect_rings(data, segments[-1][1], segments[-1][0])
    else:
        z, inner_diameter, outer_diameter = part["geo"][-1]
        r1=make_vertex_ring(data, z, inner_diameter)  
        #r2=make_vertex_ring(data, z, outer_diameter)  
        segments.append((r1, r1))
        connect_rings(data, r1, segments[-2][0])
        connect_rings(data, r1, segments[-2][1])
        
        # close mesh horizontal with faces and edges
        connect_rings(data, segments[0][1], segments[0][0])
    
    return object_from_data(data, part["name"], scene)
    
def make_nose(joint1_part, joint2_part):
    
    # create triangle for cutout
    diameter = nose_size*joint1_part["geo"][-1][1] / 1000
    
    assert joint1_part["meta"]["type"] == joint2_part["meta"]["type"]
    
    x0 = 0
    x1 = 2*joint1_part["geo"][-1][1] / 1000
    y0 = -1*diameter
    y1 = diameter
        
    #z0 = 0.001 + 0.5*wall_thickness/1000 + joint1_part["geo"][0][0] / 1000
    #z1 = 0.01 + (5+joint1_part["geo"][-1][0]) / 1000
    
    z0=0.00005+joint1_part["geo"][0][0]/1000
    z1=0.01+joint1_part["geo"][-1][0]/1000
        
    if joint1_part["meta"]["type"] == SPLIT_NARROWING:
        z1=0.00005+joint1_part["geo"][0][0]/1000
        z0=0.00005+joint1_part["geo"][-1][0]/1000
        
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
    
    joint1 = bpy.data.objects[joint1_part["name"]]
    joint2 = bpy.data.objects[joint2_part["name"]]

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
    bpy.data.objects[joint2.name].select_set(True)
    bpy.data.objects["nose2"].select_set(True)
    bpy.context.view_layer.objects.active = joint2
    bpy.ops.object.join()

# create all parts
for i in range(len(parts)):
    
    if create_partly and i not in create_ids:
        continue
    
    part = parts[i]
    print(i, part["type"])
    if part["type"]=="mouthpiece":
        make_mouthpiece(part)
    if part["type"]=="normal":
        make_normal_part(part)
    elif part["type"]=="joint1":
        make_joint1(part)
    elif part["type"]=="joint2":
        make_joint2(part)
    elif part["type"]=="nose":
        make_nose(parts[i-2], parts[i-1])

# go to object mode - the script does not work in edit mode

# join them

def join_segments():
    bpy.ops.object.mode_set(mode = 'OBJECT') 

    joins = []
    join = []

    for i in range(len(parts)):
        if parts[i]["type"] == "nose":
            continue
        join.append(parts[i])
        
        if len(join) == 3:
            joins.append(join)
            join = []

    joins.append(join)

    for i in range(len(joins)):
        print([j["name"] for j in joins[i]])
        if joins[i][-1]["type"] == "joint1" and joins[i][-1]["meta"]["type"] == SPLIT_NARROWING:
            # swap joints
            joint = joins[i+1][0]
            joins[i+1][0] = joins[i][-1]
            joins[i][-1] = joint


    for i_join in range(len(joins)):
        join = joins[i_join]
        bpy.ops.object.select_all(action='DESELECT')
        
        for j in join:
            bpy.data.objects[j["name"]].select_set(True)
        
        bpy.context.view_layer.objects.active = bpy.data.objects[join[0]["name"]]
        bpy.data.objects[join[0]["name"]].name = str(i_join)
        
        bpy.ops.object.join()
        
if not create_partly:
    join_segments()

# add curves 
if "Curve" in bpy.data.objects:
    for obj in bpy.data.objects:
        if obj.name != "Curve":
            mod = obj.modifiers.new("Curve", 'CURVE')
            mod.deform_axis = "NEG_Y"
            mod.object = bpy.data.objects["Curve"]




            
