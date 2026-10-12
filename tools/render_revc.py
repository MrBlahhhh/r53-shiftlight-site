"""Render real Rev C CAD geometry with Blender; no generated/reconstructed parts."""
from pathlib import Path
import bpy
import json
import argparse
import sys
from mathutils import Vector

SITE = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--can-glb', type=Path, default=SITE / 'dist/assets/board.glb')
parser.add_argument('--kline-stl', type=Path, default=SITE.parent / 'R53_Mini_Kline_Canbus_Logger_Shiftlight/hardware/pcb/rev-c/r53-kline-can-carrier-rev-c.stl')
parser.add_argument('--output', type=Path, default=SITE / 'render')
options = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
CAN_GLB = options.can_glb
KLINE_STL = options.kline_stl
OUT = options.output
OUT.mkdir(parents=True, exist_ok=True)
CAN_STL = OUT / 'can-revc.stl'

def clear():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

clear()
bpy.ops.import_scene.gltf(filepath=str(CAN_GLB))
meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for obj in meshes:
    obj.select_set(True)
bpy.ops.wm.stl_export(filepath=str(CAN_STL), export_selected_objects=True, global_scale=1000.0)

def aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat('-Z', 'Y').to_euler()

def light(name, position, energy, size):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = energy
    data.shape = 'DISK'
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = position
    aim(obj, Vector((0, 0, 0)))

def render_model(source, prefix):
    clear()
    bpy.ops.wm.stl_import(filepath=str(source))
    objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    bounds = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    low = Vector(tuple(min(p[i] for p in bounds) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in bounds) for i in range(3)))
    dimensions = high - low
    center = (high + low) / 2
    factor = 1.0 / max(dimensions.x, dimensions.y)
    material = bpy.data.materials.new('Neutral CAD surface')
    material.use_nodes = True
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (0.60, 0.69, 0.66, 1.0)
    shader.inputs['Roughness'].default_value = 0.38
    shader.inputs['Metallic'].default_value = 0.08
    vertices = sum(len(obj.data.vertices) for obj in objects)
    polygons = sum(len(obj.data.polygons) for obj in objects)
    for obj in objects:
        # Imported STL has a single baked geometry; normalize only the render scene.
        obj.location -= center
        obj.location *= factor
        obj.scale *= factor
        obj.data.materials.clear()
        obj.data.materials.append(material)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.45, 0.45, 0.45, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = 0.5
    scene.view_settings.view_transform = 'AgX'
    light('Key', Vector((-1.4, -1.1, 2.4)), 90, 1.5)
    light('Fill', Vector((1.5, 0.5, 1.6)), 60, 1.2)
    light('Rim', Vector((-0.3, 1.8, 1.2)), 80, 1.0)
    data = bpy.data.cameras.new('Camera')
    camera = bpy.data.objects.new('Camera', data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    data.type = 'ORTHO'
    data.ortho_scale = 1.6
    camera.location = Vector((1.05, -1.5, 1.9))
    aim(camera, Vector((0, 0, 0)))
    scene.render.filepath = str(OUT / f'{prefix}_iso.png')
    bpy.ops.render.render(write_still=True)
    if prefix == 'shiftlight':
        camera.location = Vector((0, 0, 3))
        camera.rotation_euler = (0, 0, 0)
        data.ortho_scale = 1.42
        scene.render.filepath = str(OUT / 'pcb_top.png')
        bpy.ops.render.render(write_still=True)
    return {'source': str(source), 'dimensionsMm': list(dimensions), 'vertices': vertices, 'polygons': polygons}

stats = {
    'can': render_model(CAN_STL, 'shiftlight'),
    'kline': render_model(KLINE_STL, 'bridge'),
    'canOriginal': str(CAN_GLB),
    'canSourceCommit': 'fda212b',
}
(OUT / 'model-stats.json').write_text(json.dumps(stats, indent=2), encoding='utf-8')
print('RENDERED', json.dumps(stats))
