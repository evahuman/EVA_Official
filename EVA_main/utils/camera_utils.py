#
# Copyright (C) 2023, Inria
# GRAPHDECO research group, https://team.inria.fr/graphdeco
# All rights reserved.
#
# This software is free for non-commercial, research and evaluation use 
# under the terms of the LICENSE.md file.
#
# For inquiries contact  george.drettakis@inria.fr
#

from scene.cameras import Camera
import numpy as np
from utils.general_utils import PILtoTorch
from utils.graphics_utils import fov2focal
import cv2
import torch

WARNED = False

def loadCam(args, id, cam_info, resolution_scale):
    orig_w, orig_h = cam_info.image.size

    if args.resolution in [1, 2, 4, 8]:
        resolution = round(orig_w/(resolution_scale * args.resolution)), round(orig_h/(resolution_scale * args.resolution))
    else:  # should be a type that converts to float
        if args.resolution == -1:
            if orig_w > 3200:
                global WARNED
                if not WARNED:
                    print("[ INFO ] Encountered quite large input images (>1.6K pixels width), rescaling to 1.6K.\n "
                        "If this is not desired, please explicitly specify '--resolution/-r' as 1")
                    WARNED = True
                global_down = orig_w / 1600
            else:
                global_down = 1
        else:
            global_down = orig_w / args.resolution

        scale = float(global_down) * float(resolution_scale)
        resolution = (int(orig_w / scale), int(orig_h / scale))

    resized_image_rgb = PILtoTorch(cam_info.image, resolution)

    gt_image = resized_image_rgb[:3, ...]
    loaded_mask = None

    if resized_image_rgb.shape[1] == 4:
        loaded_mask = resized_image_rgb[3:4, ...]

    if cam_info.bound_mask is not None:
        resized_bound_mask = PILtoTorch(cam_info.bound_mask, resolution)
    else:
        resized_bound_mask = None

    if cam_info.face_mask is not None:
        resized_face_mask = PILtoTorch(cam_info.face_mask, resolution)
    else:
        resized_face_mask = None

    if cam_info.lhand_mask is not None:
        resized_lhand_mask = PILtoTorch(cam_info.lhand_mask, resolution)
    else:
        resized_lhand_mask = None

    if cam_info.rhand_mask is not None:
        resized_rhand_mask = PILtoTorch(cam_info.rhand_mask, resolution)
    else:
        resized_rhand_mask = None

    if cam_info.face_render_mask is not None:
        resized_face_render_mask = PILtoTorch(cam_info.face_render_mask, resolution)
    else:
        resized_face_render_mask = None

    if cam_info.lhand_render_mask is not None:
        resized_lhand_render_mask = PILtoTorch(cam_info.lhand_render_mask, resolution)
    else:
        resized_lhand_render_mask = None

    if cam_info.rhand_render_mask is not None:
        resized_rhand_render_mask = PILtoTorch(cam_info.rhand_render_mask, resolution)
    else:
        resized_rhand_render_mask = None

    if cam_info.depth is not None:
        resized_depth = cv2.resize(cam_info.depth, resolution)
        resized_depth = torch.from_numpy(resized_depth)
    else:
        resized_depth = None

    if cam_info.kp2d is not None:
        kp2d = cam_info.kp2d / [resolution[0], resolution[1], 1]
        kp2d = torch.from_numpy(kp2d)
    else:
        kp2d = None

    if cam_info.bkgd_mask is not None:
        resized_bkgd_mask = PILtoTorch(cam_info.bkgd_mask, resolution)
    else:
        resized_bkgd_mask = None

    return Camera(colmap_id=cam_info.uid, pose_id=cam_info.pose_id, R=cam_info.R, T=cam_info.T, K=cam_info.K, 
                  FoVx=cam_info.FovX, FoVy=cam_info.FovY, 
                  image=gt_image, gt_alpha_mask=loaded_mask,
                  image_name=cam_info.image_name, uid=id, bkgd_mask=resized_bkgd_mask, 
                  bound_mask=resized_bound_mask, smpl_param=cam_info.smpl_param, 
                  world_vertex=cam_info.world_vertex, world_bound=cam_info.world_bound, 
                  big_pose_smpl_param=cam_info.big_pose_smpl_param, 
                  big_pose_world_vertex=cam_info.big_pose_world_vertex, 
                  big_pose_world_bound=cam_info.big_pose_world_bound, 
                  face_mask=resized_face_mask,
                  lhand_mask=resized_lhand_mask,
                  rhand_mask=resized_rhand_mask,
                  face_render_mask=resized_face_render_mask,
                  lhand_render_mask=resized_lhand_render_mask,
                  rhand_render_mask=resized_rhand_render_mask,
                  depth=resized_depth,
                  kp2d=kp2d,
                  data_device=args.data_device)

def cameraList_from_camInfos(cam_infos, resolution_scale, args):
    camera_list = []

    for id, c in enumerate(cam_infos):
        camera_list.append(loadCam(args, id, c, resolution_scale))

    return camera_list

def camera_to_JSON(id, camera : Camera):
    Rt = np.zeros((4, 4))
    Rt[:3, :3] = camera.R.transpose()
    Rt[:3, 3] = camera.T
    Rt[3, 3] = 1.0

    W2C = np.linalg.inv(Rt)
    pos = W2C[:3, 3]
    rot = W2C[:3, :3]
    serializable_array_2d = [x.tolist() for x in rot]
    camera_entry = {
        'id' : id,
        'img_name' : camera.image_name,
        'width' : camera.width,
        'height' : camera.height,
        'position': pos.tolist(),
        'rotation': serializable_array_2d,
        'fy' : fov2focal(camera.FovY, camera.height),
        'fx' : fov2focal(camera.FovX, camera.width)
    }
    return camera_entry
