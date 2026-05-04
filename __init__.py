bl_info = {
    "name": "RefTool Blender Edition",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > RefTool Tab",
    "description": "Reference Tool (Clean Viewport / Auto-Hide)",
    "category": "Interface",
}

import bpy
import os
import math
import mathutils
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, FloatProperty
from bpy.types import Operator, Panel
import bpy.utils.previews

preview_collections = {}
historyArray = [] 
_history_timer = None 

class CamHistory():
    def __init__(self, rot_h, rot_v, roll, zoom):
        self.rot_h = rot_h
        self.rot_v = rot_v
        self.roll = roll
        self.zoom = zoom

def isolate_ref_camera(scene, active_cam):
    for obj in scene.objects:
        if obj.type == 'CAMERA' and obj.name.startswith("REF_"):
            obj.hide_set(obj != active_cam)

def commit_history():
    global _history_timer
    _history_timer = None 
    
    cam = bpy.context.scene.camera
    if cam and cam.name.startswith("REF_"):
        if len(historyArray) > 0:
            last = historyArray[-1]
            if (abs(last.rot_h - cam.ref_orbit_h) < 0.001 and
                abs(last.rot_v - cam.ref_orbit_v) < 0.001 and
                abs(last.roll - cam.ref_roll) < 0.001 and
                abs(last.zoom - cam.ref_zoom) < 0.001):
                return None 
                
        history = CamHistory(cam.ref_orbit_h, cam.ref_orbit_v, cam.ref_roll, cam.ref_zoom)
        historyArray.append(history)
        
        if len(historyArray) > 11:
            historyArray.pop(0)
        
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
                    
    return None 

def update_camera_orbit(self, context):
    cam = self
    dist = cam.ref_zoom
    rot_h = cam.ref_orbit_h
    rot_v = cam.ref_orbit_v
    roll = cam.ref_roll
    
    x = dist * math.cos(rot_v) * math.sin(rot_h)
    y = -dist * math.cos(rot_v) * math.cos(rot_h)
    z = dist * math.sin(rot_v)
    cam.location = (x, y, z)
    
    direction = mathutils.Vector((0, 0, 0)) - mathutils.Vector((x, y, z))
    rot_quat = direction.to_track_quat('-Z', 'Y')
    roll_quat = mathutils.Quaternion((0, 0, 1), roll)
    cam.rotation_euler = (rot_quat @ roll_quat).to_euler()

    global _history_timer
    if _history_timer is not None and bpy.app.timers.is_registered(_history_timer):
        bpy.app.timers.unregister(_history_timer)
        
    _history_timer = commit_history
    bpy.app.timers.register(_history_timer, first_interval=0.4)

def update_focal_length(self, context):
    if self.type == 'CAMERA' and self.data:
        self.data.lens = self.ref_focal

class VIEW3D_OT_set_fixed_view(Operator):
    bl_idname = "view3d.set_fixed_view"
    bl_label = "Set Fixed View"
    view_type: StringProperty()

    def execute(self, context):
        if self.view_type == 'PERSP':
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    space = area.spaces.active
                    if space.region_3d.view_perspective == 'CAMERA':
                        bpy.ops.view3d.view_camera()
                    space.region_3d.view_perspective = 'PERSP'
        else:
            bpy.ops.view3d.view_axis(type=self.view_type)
        return {'FINISHED'}

class OBJECT_OT_add_ref_camera(Operator, ImportHelper):
    bl_idname = "object.add_ref_camera"
    bl_label = "Add Reference"
    bl_options = {'REGISTER', 'UNDO'} 
    
    filter_glob: StringProperty(default="*.jpg;*.jpeg;*.png;*.tif;*.tiff;*.bmp", options={'HIDDEN'})

    def execute(self, context):
        img = bpy.data.images.load(self.filepath)
        cam_data = bpy.data.cameras.new(name="REF_" + img.name)
        cam_obj = bpy.data.objects.new(name="REF_" + img.name, object_data=cam_data)
        context.collection.objects.link(cam_obj)

        cam_data.show_background_images = True
        bg = cam_data.background_images.new()
        bg.image = img
        bg.frame_method = 'FIT'
        bg.display_depth = 'FRONT'
        bg.alpha = 0.5

        context.scene.camera = cam_obj
        
        isolate_ref_camera(context.scene, cam_obj)
        
        bpy.ops.object.reset_ref_camera() 
        
        historyArray.clear()
        commit_history()
        
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_perspective = 'CAMERA'
        return {'FINISHED'}

class OBJECT_OT_switch_ref_camera(Operator):
    bl_idname = "object.switch_ref_camera"
    bl_label = "Select"
    bl_options = {'REGISTER', 'UNDO'} 
    cam_name: StringProperty()

    def execute(self, context):
        cam_obj = bpy.data.objects.get(self.cam_name)
        if cam_obj:
            context.scene.camera = cam_obj
            
            isolate_ref_camera(context.scene, cam_obj)
            
            historyArray.clear()
            commit_history()
            
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.spaces.active.region_3d.view_perspective = 'CAMERA'
        return {'FINISHED'}

class OBJECT_OT_reset_ref_camera(Operator):
    bl_idname = "object.reset_ref_camera"
    bl_label = "Reset Camera"

    def execute(self, context):
        cam = context.scene.camera 
        if cam and cam.name.startswith("REF_"):
            cam.ref_orbit_h = 0.0
            cam.ref_orbit_v = 0.0
            cam.ref_roll = 0.0
            cam.ref_zoom = 2.5 
            cam.ref_focal = 50.0 
            
            if cam.data.background_images:
                bg = cam.data.background_images[0]
                bg.offset = (0.0, 0.0)
                bg.rotation = 0.0
                bg.scale = 1.0
            
            historyArray.clear()
            commit_history()
                
        return {'FINISHED'}

class OBJECT_OT_undo_custom(Operator):
    bl_idname = "object.undo_custom"
    bl_label = "Undo Movement"
    
    def execute(self, context):
        cam = context.scene.camera
        if cam and cam.name.startswith("REF_") and len(historyArray) > 1:
            historyArray.pop()
            prev_state = historyArray[-1]
            
            cam.ref_orbit_h = prev_state.rot_h
            cam.ref_orbit_v = prev_state.rot_v
            cam.ref_roll = prev_state.roll
            cam.ref_zoom = prev_state.zoom
            
        return {'FINISHED'}

class VIEW3D_PT_reftool_main(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'RefTool'
    bl_label = "RefTool 5.3: Pro Sculpt"

    def draw(self, context):
        layout = self.layout
        pcoll = preview_collections.get("main")
        
        row = layout.row(align=True)
        row.scale_y = 1.5
        op = row.operator("view3d.set_fixed_view", text="Persp", icon='VIEW_PERSPECTIVE')
        op.view_type = 'PERSP'
        op = row.operator("view3d.set_fixed_view", text="Top", icon='AXIS_TOP')
        op.view_type = 'TOP'
        op = row.operator("view3d.set_fixed_view", text="Front", icon='AXIS_FRONT')
        op.view_type = 'FRONT'
        op = row.operator("view3d.set_fixed_view", text="Sides", icon='AXIS_SIDE')
        op.view_type = 'RIGHT'

        layout.separator()
        
        big_row = layout.row()
        big_row.scale_y = 1.5 
        big_row.operator("object.add_ref_camera", text="Load New Reference", icon='ADD', depress=True)
        
        layout.separator()
        layout.label(text="My References:", icon='GRID')
        ref_cameras = [obj for obj in context.scene.objects if obj.type == 'CAMERA' and obj.name.startswith("REF_")]
        
        col = layout.column(align=True)
        for cam in ref_cameras:
            row = col.row(align=True)
            is_active = (context.scene.camera == cam)
            
            icon_val = 0
            if cam.data.background_images:
                img = cam.data.background_images[0].image
                if img:
                    if cam.name not in pcoll:
                        filepath = bpy.path.abspath(img.filepath)
                        if filepath and os.path.exists(filepath):
                            pcoll.load(cam.name, filepath, 'IMAGE')
                    
                    if cam.name in pcoll:
                        icon_val = pcoll[cam.name].icon_id

            if icon_val:
                op = row.operator("object.switch_ref_camera", text=cam.name.replace("REF_", cam.name), icon_value=icon_val, depress=is_active)
            else:
                op = row.operator("object.switch_ref_camera", text=cam.name.replace("REF_", cam.name), icon='CAMERA_DATA', depress=is_active)
            
            op.cam_name = cam.name

        layout.separator()

        obj = context.scene.camera 
        if obj and obj.type == 'CAMERA' and obj.name.startswith("REF_"):
            box = layout.box()
            box.label(text=f"3D Settings: {obj.name.replace('REF_', '')}", icon='PROPERTIES')
            
            row_undo = box.row(align=True)
            row_undo.operator("object.reset_ref_camera", icon='FILE_REFRESH', text="Reset")
            
            sub_undo = row_undo.row(align=True)
            pasos_disponibles = len(historyArray) - 1 if len(historyArray) > 0 else 0
            sub_undo.operator("object.undo_custom", icon='CANCEL', text=f"Undo ({pasos_disponibles})")
            sub_undo.enabled = len(historyArray) > 1
            
            col = box.column(align=True)
            col.prop(obj, "ref_orbit_h", text="Orbit H", slider=True)
            col.prop(obj, "ref_orbit_v", text="Orbit V", slider=True)
            col.prop(obj, "ref_roll", text="Roll Z", slider=True)
            col.prop(obj, "ref_zoom", text="Zoom (Distance)", slider=True)
            
            cam_data = obj.data
            col.prop(obj, "ref_focal", text="Focal Length", slider=True)

            if cam_data.background_images:
                box.separator()
                box.label(text="Image Settings (2D)", icon='IMAGE_DATA')
                bg = cam_data.background_images[0]
                
                row_bg = box.row()
                row_bg.prop(bg, "display_depth", text="", expand=True)
                box.prop(bg, "alpha", text="Opacity", slider=True)
                
                col_img = box.column(align=True)
                col_img.prop(bg, "offset", text="Offset (X / Y)")
                col_img.prop(bg, "scale", text="Scale")
                col_img.prop(bg, "rotation", text="Rotate")

            box.separator()
            box.label(text=f"History in Memory ({pasos_disponibles}/10)", icon='WORDWRAP_ON')
            
            show_items = historyArray[-6:]
            for i, hist in enumerate(show_items):
                is_last = (i == len(show_items) - 1)
                tag = "▶ [Current]  " if is_last else f"   [Step -{len(show_items) - i - 1}]"
                box.label(text=f"{tag} Z: {hist.zoom:.1f} | H: {math.degrees(hist.rot_h):.0f}°")

def register():
    pcoll = bpy.utils.previews.new()
    preview_collections["main"] = pcoll

    bpy.types.Object.ref_orbit_h = FloatProperty(name="H", min=-math.pi, max=math.pi, default=0.0, subtype='ANGLE', update=update_camera_orbit)
    bpy.types.Object.ref_orbit_v = FloatProperty(name="V", min=-math.radians(85), max=math.radians(85), default=0.0, subtype='ANGLE', update=update_camera_orbit)
    bpy.types.Object.ref_roll = FloatProperty(name="Roll", min=-math.pi, max=math.pi, default=0.0, subtype='ANGLE', update=update_camera_orbit)
    bpy.types.Object.ref_zoom = FloatProperty(name="Z", min=0.1, max=5.0, default=2.5, update=update_camera_orbit)
    
    bpy.types.Object.ref_focal = FloatProperty(
        name="Focal", min=10.0, max=200.0, default=50.0, update=update_focal_length)

    bpy.utils.register_class(VIEW3D_OT_set_fixed_view)
    bpy.utils.register_class(OBJECT_OT_add_ref_camera)
    bpy.utils.register_class(OBJECT_OT_switch_ref_camera)
    bpy.utils.register_class(OBJECT_OT_reset_ref_camera)
    bpy.utils.register_class(OBJECT_OT_undo_custom)
    bpy.utils.register_class(VIEW3D_PT_reftool_main)

def unregister():
    global _history_timer
    if _history_timer is not None and bpy.app.timers.is_registered(_history_timer):
        bpy.app.timers.unregister(_history_timer)
        
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

    bpy.utils.unregister_class(VIEW3D_OT_set_fixed_view)
    bpy.utils.unregister_class(OBJECT_OT_add_ref_camera)
    bpy.utils.unregister_class(OBJECT_OT_switch_ref_camera)
    bpy.utils.unregister_class(OBJECT_OT_reset_ref_camera)
    bpy.utils.unregister_class(OBJECT_OT_undo_custom)
    bpy.utils.unregister_class(VIEW3D_PT_reftool_main)
    
    del bpy.types.Object.ref_orbit_h
    del bpy.types.Object.ref_orbit_v
    del bpy.types.Object.ref_roll
    del bpy.types.Object.ref_zoom
    del bpy.types.Object.ref_focal

if __name__ == "__main__":
    register()