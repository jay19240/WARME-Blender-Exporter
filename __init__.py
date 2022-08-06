bl_info = {
    "name": "JSM/JAM Exporter",
    "author": "matidfk#2272",
    "version": (0, 1, 5),
    "blender": (3, 1, 2),
    "location": "View3D > Properties > JSM/JAM Export",
    "description": "Export to a custom JSM/JAM format",
    "category": "Import-Export"
}

# Imports
import bpy
import json
import mathutils
from math import pi
from pathlib import Path

# JAM export operator
class JSMJAMEXPORT_OT_export_jam(bpy.types.Operator):
    """Export to a JAM format""" 
    bl_idname = "object.export_jam"
    bl_label = "Export to animated JAM format"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}

    def execute(self, context):
        data = export_jam()
        if data is not None:
            save_file(data, bpy.path.abspath(context.scene.render.filepath), context.object.name, "jam")
        else:
            self.report({'ERROR'}, "Object is not triangulated")
        return {"FINISHED"}

# MD2 process operator
class JSMJAMEXPORT_OT_process_md2(bpy.types.Operator):
    """Process md2 model""" 
    bl_idname = "object.process_md2"
    bl_label = "Process md2 model"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}

    def execute(self, context):
        bpy.context.scene.frame_start = 0
        obj = bpy.context.object
        bpy.context.scene.frame_end = len(obj.data.shape_keys.key_blocks) - 1
        print(bpy.context.scene.frame_end)
        obj.data.use_auto_smooth = 0
        obj.data.shape_keys.use_relative = False
        driver = obj.data.shape_keys.driver_add("eval_time")
        driver.driver.expression = "(frame) * 10"
        
        prev_anim_name = ""
        for frm, sk in enumerate(obj.data.shape_keys.key_blocks):
            anim_name = sk.name[:-3]
            if anim_name != prev_anim_name:
                if len(context.object.jam_animations) > 0:
                    context.object.jam_animations[-1].end_frame = frm
                anim = context.object.jam_animations.add()
                anim.frame_duration = 100
                anim.name = anim_name
                anim.start_frame = frm
                prev_anim_name = anim_name
        
        context.object.jam_animations[-1].end_frame = len(obj.data.shape_keys.key_blocks) - 1
        
        return {"FINISHED"}

# JSM export operator
class JSMJAMEXPORT_OT_export_jsm(bpy.types.Operator):
    """Export to a JSM format""" 
    bl_idname = "object.export_jsm"
    bl_label = "Export to static JSM format"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}

    def execute(self, context):
        data = export_jsm()
        if data is not None:
            save_file(data, bpy.path.abspath(context.scene.render.filepath), context.object.name, "jsm")
        else:
            self.report({'ERROR'}, "Object is not triangulated")
        return {"FINISHED"}
    
    
# JWM export operator
class JSMJAMEXPORT_OT_export_jwm(bpy.types.Operator):
    """Export to a JWM format""" 
    bl_idname = "object.export_jwm"
    bl_label = "Export to static JWM format"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}

    def execute(self, context):
        data = export_jwm()
        if data is not None:
            save_file(data, bpy.path.abspath(context.scene.render.filepath), context.object.name, "jwm")
        else:
            self.report({'ERROR'}, "Object is not triangulated")
        return {"FINISHED"}


# UI
class JSMJAMEXPORT_PT_options(bpy.types.Panel):
    bl_idname = "JSMJAMEXPORT_PT_options"
    bl_label = "JSM/JAM Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "JSM/JAM Export"
    bl_context = "objectmode"
    
    def draw(self, context):
        layout = self.layout.column()
        layout.operator("object.export_jwm")
        layout.separator()
        layout.separator()
        layout.operator("object.export_jsm")
        layout.separator()
        layout.separator()
        layout.operator("object.export_jam")
        layout.separator()
        
        
        # Row for each animation
        for i, anim in enumerate(context.object.jam_animations):
            layout = self.layout.row()
            layout.prop(context.object.jam_animations[i], "name")
            layout.prop(context.object.jam_animations[i], "start_frame")
            layout.prop(context.object.jam_animations[i], "end_frame")
            layout.prop(context.object.jam_animations[i], "frame_duration")
            
        layout = self.layout.column()
        layout.separator()
        
        layout.operator("object.add_animation")
        layout.operator("object.remove_animation")
        layout.operator("object.process_md2")


# Add an animation data block operator
class JSMJAMEXPORT_OT_add_animation(bpy.types.Operator):
    
    """Add animation""" 
    bl_idname = "object.add_animation"
    bl_label = "Add an animation to the current objects list"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}
    
    def execute(self, context):
        temp = context.object.jam_animations[-1].end_frame if len(context.object.jam_animations) > 0 else 0
        item = context.object.jam_animations.add()
        item.start_frame = temp
        item.end_frame = temp
        return {"FINISHED"}


# Remove an animation data block operator
class JSMJAMEXPORT_OT_remove_animation(bpy.types.Operator):
    
    """Remove last animation""" 
    bl_idname = "object.remove_animation"
    bl_label = "Remove last animation from the current objects list"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}
    
    def execute(self, context):
        context.object.jam_animations.remove(len(bpy.context.object.jam_animations) - 1)
        return {"FINISHED"}


# JSM exporter function
def export_jsm():
    
    # Setup object structure
    obj = {
        "Ident": "JSM",
        "Version": "0.1.3",
        "NumVertices": -1,
        "Vertices": [],
        "Normals": [],
        "TextureCoords": [],
    }
    
    # Fetch selected object
    selected_obj = bpy.context.object
    dg = bpy.context.evaluated_depsgraph_get()
    
    # Get current mesh data
    dg.update()
    obj_eval = selected_obj.evaluated_get(dg)
    mesh = obj_eval.to_mesh()
    
    # Transform to correct coordinate system
    mesh.transform(bpy.context.object.matrix_world)
    mesh.transform(mathutils.Matrix.Rotation(pi/2, 4, 'X')) 
    mesh.transform(mathutils.Matrix.Rotation(pi, 4, 'Z')) 
    
    # Vertices, Normals
    for tri in mesh.polygons:
        for li in tri.loop_indices:
            # Return error if object is not triangulated
            if len(tri.loop_indices) != 3:
                return None
            
            vert = mesh.vertices[mesh.loops[li].vertex_index]
            for i in range(0, 3):
                obj["Vertices"].append(round(vert.co[i], 4))
                obj["Normals"].append(round(vert.normal[i], 4))
                
    # TextureCoords
    for tri in mesh.polygons:
        for li in tri.loop_indices:
            obj["TextureCoords"].append(round(mesh.uv_layers.active.data[li].uv[0], 4))
            obj["TextureCoords"].append(1 - round(mesh.uv_layers.active.data[li].uv[1], 4))
                
    obj["NumVertices"] = int(len(obj["Vertices"]) / 3)
                
    return obj



# JAM exporter function
def export_jam():
    
    # Setup object structure
    obj = {
        "Ident": "JAM",
        "Version": "0.1.3",
        "NumVertices": -1,
        "Frames": [],
        "TextureCoords": [],
        "Animations": []
    }
    
    # Fetch selected object
    selected_obj = bpy.context.object
    dg = bpy.context.evaluated_depsgraph_get()
    
    # Go to start frame
    bpy.context.scene.frame_current = bpy.context.scene.frame_start

    # For each frame
    while bpy.context.scene.frame_current <= bpy.context.scene.frame_end:
        
        # Get current mesh data
        dg.update()
        obj_eval = selected_obj.evaluated_get(dg)
        mesh = obj_eval.to_mesh()
        
        # Transform to correct coordinate system
        mesh.transform(bpy.context.object.matrix_world)
        mesh.transform(mathutils.Matrix.Rotation(pi/2, 4, 'X')) 
        mesh.transform(mathutils.Matrix.Rotation(pi, 4, 'Z')) 
        
        
        vertices = []
        normals = [] 
        
        # Vertices, Normals
        for tri in mesh.polygons:
            for li in tri.loop_indices:
                # Return error if object is not triangulated
                if len(tri.loop_indices) != 3:
                    return None
                
                vert = mesh.vertices[mesh.loops[li].vertex_index]
                for i in range(0, 3):
                    vertices.append(round(vert.co[i], 4))
                    normals.append(round(vert.normal[i], 4))
                    
        # Append to obj
        obj["Frames"].append({"Vertices": vertices, "Normals": normals})
        
        obj["NumVertices"] = int(len(obj["Frames"][0]["Vertices"]) / 3)
    
        bpy.context.scene.frame_current += 1
        
        
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    obj_eval = selected_obj.evaluated_get(depsgraph)
    mesh = obj_eval.data

    # TextureCoords
    for tri in mesh.polygons:
        for li in tri.loop_indices:
            obj["TextureCoords"].append(round(mesh.uv_layers.active.data[li].uv[0], 4))
            obj["TextureCoords"].append(1 - round(mesh.uv_layers.active.data[li].uv[1], 4))
                
    # Animations
    for anim in selected_obj.jam_animations:
        obj["Animations"].append({"Name": anim.name,
                                  "StartFrame": anim.start_frame, 
                                  "EndFrame": anim.end_frame,
                                  "FrameDuration": anim.frame_duration})
    
    return obj


# JWM exporter function
def export_jwm():
    obj = {
        "Ident": "JWM",
        "Sectors": [],
        "AccessPool": [],
        "NeighborPool": [],
    }

    # Fetch selected object
    selected_obj = bpy.context.object
    dg = bpy.context.evaluated_depsgraph_get()

    # Get current mesh data
    dg.update()
    obj_eval = selected_obj.evaluated_get(dg)
    mesh = obj_eval.to_mesh()

    # Transform to correct coordinate system
    mesh.transform(bpy.context.object.matrix_world)
    mesh.transform(mathutils.Matrix.Rotation(pi/2, 4, 'X')) 
    mesh.transform(mathutils.Matrix.Rotation(pi, 4, 'Z')) 

    for tri in mesh.polygons:
        sector = []
        for i, li in enumerate(tri.loop_indices):
            trii = []
            for j in range(0, 3):
                trii.append(round(mesh.vertices[mesh.loops[li].vertex_index].co[j], 4))
            sector.append(trii)
        obj["Sectors"].append(sector)
        
    # Theres probably a better way to do this
    # access pool is shared vertices
    # neighbor pool is shared edges
                            
    for i in range(len(obj["Sectors"])):
        neighbors = [-1,-1,-1]
        access = [i]
        
        for j in range(3):
            p1 = obj["Sectors"][i][j]
            p2 = obj["Sectors"][i][(j + 1) % 3]
            
            for k in range(len(obj["Sectors"])):
                if obj["Sectors"][k] == obj["Sectors"][i]:
                    continue

                for l in range(3):
                    p1prime = obj["Sectors"][k][l]
                    p2prime = obj["Sectors"][k][(l + 1) % 3]
                    
                    neighbor_test1 = p1 == p1prime and p2 == p2prime
                    neighbor_test2 = p1 == p2prime and p2 == p1prime
                    
                    if neighbor_test1 or neighbor_test2:
                        neighbors[j] = k
                    
                    if p1 == p1prime and not k in access:
                        access.append(k)
            
        obj["NeighborPool"].append(neighbors)
        obj["AccessPool"].append(access)

    return obj

# Save to file
def save_file(obj, path, filename, extension):
    if path == "":
        path = bpy.path.abspath("//")
    file = Path(path + "/" + filename + "." + extension)
    i = 1
    
    # In order to avoid overwriting files, add _i where i will increment until there is no file named that
    while file.exists():
        file = Path(path + "/" + filename + "_" + str(i) + "." + extension)
        i += 1
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False)
    
    
    
# Blender class to allow saving jam_animations to objects as a data block
class JamAnimation(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    start_frame: bpy.props.IntProperty(name="Start frame")
    end_frame: bpy.props.IntProperty(name="End frame")
    frame_duration: bpy.props.IntProperty(name="Frame Duration")



# Blender stuff
def register():
    bpy.utils.register_class(JSMJAMEXPORT_OT_export_jwm)
    bpy.utils.register_class(JSMJAMEXPORT_OT_export_jsm)
    bpy.utils.register_class(JSMJAMEXPORT_OT_export_jam)
    bpy.utils.register_class(JSMJAMEXPORT_OT_process_md2)
    bpy.utils.register_class(JSMJAMEXPORT_PT_options)
    
    bpy.utils.register_class(JSMJAMEXPORT_OT_add_animation)
    bpy.utils.register_class(JSMJAMEXPORT_OT_remove_animation)
    
    bpy.utils.register_class(JamAnimation)
    bpy.types.Object.jam_animations = bpy.props.CollectionProperty(type=JamAnimation)
    
def unregister():
    bpy.utils.unregister_class(JSMJAMEXPORT_OT_export_jwm)
    bpy.utils.unregister_class(JSMJAMEXPORT_OT_export_jsm)
    bpy.utils.unregister_class(JSMJAMEXPORT_OT_export_jam)
    bpy.utils.unregister_class(JSMJAMEXPORT_OT_process_md2)
    bpy.utils.unregister_class(JSMJAMEXPORT_PT_options)
    
    bpy.utils.unregister_class(JSMJAMEXPORT_OT_add_animation)
    bpy.utils.unregister_class(JSMJAMEXPORT_OT_remove_animation)
    bpy.utils.unregister_class(JamAnimation)

if __name__ == "__main__":
    register()