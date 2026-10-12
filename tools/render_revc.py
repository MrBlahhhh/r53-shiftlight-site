"""Render the actual Rev C CAN GLB with its original KiCad material colors."""
from pathlib import Path
import argparse
import json
import sys
import bpy
from mathutils import Matrix, Vector

SITE = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--can-glb', type=Path, default=SITE / 'dist/assets/board.glb')
parser.add_argument('--output', type=Path, default=SITE / 'render')
options = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
options.output.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(options.can_glb))
objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
bounds = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
low = Vector(tuple(min(p[i] for p in bounds) for i in range(3)))
high = Vector(tuple(max(p[i] for p in bounds) for i in range(3)))
dimensions = high - low
center = (high + low) / 2
factor = 1.0 / max(dimensions.x, dimensions.y)
transform = Matrix.Scale(factor, 4) @ Matrix.Translation(-center)
worlds = [(obj, obj.matrix_world.copy()) for obj in objects]
for obj, world in worlds:
    obj.parent = None
    obj.matrix_world = transform @ world

def aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat('-Z', 'Y').to_euler()

def light(name, position, energy, size):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.shape, data.size = energy, 'DISK', size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = position
    aim(obj, Vector((0, 0, 0)))

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = 1600, 1200
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
data.type, data.ortho_scale = 'ORTHO', 1.6
camera.location = Vector((1.05, -1.5, 1.9))
aim(camera, Vector((0, 0, 0)))
scene.render.filepath = str(options.output / 'shiftlight_iso.png')
bpy.ops.render.render(write_still=True)
camera.location, camera.rotation_euler = Vector((0, 0, 3)), (0, 0, 0)
data.ortho_scale = 1.42
scene.render.filepath = str(options.output / 'pcb_top.png')
bpy.ops.render.render(write_still=True)
stats = {
    'source': str(options.can_glb),
    'dimensionsMm': [round(value * 1000, 6) for value in dimensions],
    'materialCount': len({material.name for obj in objects for material in obj.data.materials if material}),
    'vertices': sum(len(obj.data.vertices) for obj in objects),
    'polygons': sum(len(obj.data.polygons) for obj in objects),
    'method': 'Direct GLB rendering, original KiCad material colors retained.',
}
(options.output / 'model-stats.json').write_text(json.dumps(stats, indent=2) + '\n', encoding='utf-8')
print('RENDERED', json.dumps(stats))
