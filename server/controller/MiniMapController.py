from io import BytesIO

import cv2
from flask import Blueprint, request, jsonify, send_file

from matchmap.gia_rotation import RotationGIA
from matchmap.sifttest.sifttest5 import MiniMap
from capture.capture_factory import capture
from myutils.imgutils import crop_img, cvimg_to_base64

minimap_bp = Blueprint('minimap', __name__)
minimap = MiniMap()
large_map = minimap.map_2048['img']
minimap.get_position()
rotate = RotationGIA(True)
capture.add_observer(rotate)
capture.add_observer(minimap)

class MiniMapController:
    @staticmethod
    @minimap_bp.route('/usermap/get_position', methods=['GET'])
    def get_user_map_position():
        return jsonify(minimap.get_user_map_position())

    @staticmethod
    @minimap_bp.route('/usermap/get_scale', methods=['GET'])
    def get_user_map_scale():
        return jsonify(minimap.get_user_map_scale())

    @staticmethod
    @minimap_bp.route('/usermap/create_cache', methods=['POST'])
    def create_cached_local_map():
        data = request.json  # 获取JSON数据
        center_pos = data.get('center_pos')
        use_middle_map = data.get('use_middle_map')
        result = False
        if center_pos:
            # 用户传过来的是相对位置，要转换成绝对位置
            pix_pos = minimap.relative_axis_to_pix_axis(center_pos)
            result = minimap.global_match_cache(pix_pos)
        elif use_middle_map:
            # 现在传送移动地图不是移动到中心点，传送的时候禁止用此方法创建缓存
            pos = minimap.get_user_map_position()
            if pos:
                pos = minimap.relative_axis_to_pix_axis(pos)
                result = minimap.global_match_cache(pos)
        else:
            result = minimap.create_local_map_cache_thread()

        return jsonify({"result": result})

    @staticmethod
    @minimap_bp.route('/minimap/get_position', methods=['GET'])
    def get_position():
        absolute_position = request.args.get('absolute_position', 0) == '1'
        pos = minimap.get_position(absolute_position=absolute_position)
        return jsonify(pos)

    @staticmethod
    @minimap_bp.route('/minimap/get_rotation', methods=['GET'])
    def get_rotation():
        img = capture.get_mini_map()
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return jsonify(rotate.predict_rotation(img))

    from io import BytesIO

    @staticmethod
    @minimap_bp.route('/minimap/get_region_map', methods=['GET'])
    def get_region_map():
        global large_map
        x = request.args.get('x')
        y = request.args.get('y')
        width = request.args.get('width')
        scale = request.args.get('scale')
        if x is not None and y is not None and width is not None:
            width = int(float(width))
            x = int(float(x))
            y = int(float(y))
            if scale is None: scale = 1
            scale = float(scale)

            pix_pos = minimap.relative_axis_to_pix_axis((x, y))

            if large_map is None:
                from myutils.configutils import get_bigmap_path
                large_map = cv2.imread(get_bigmap_path(2048), cv2.IMREAD_GRAYSCALE)
                if large_map is None:
                    raise Exception("无法加载大地图")

            # tem_local_map = crop_img(app.large_map, pix_pos[0], pix_pos[1], crop_size=width, scale=scale)
            tem_local_map = crop_img(large_map, pix_pos[0], pix_pos[1], crop_size=width, scale=scale)
            if tem_local_map is None:
                raise Exception("无法裁剪大地图")

            _, img_encoded = cv2.imencode('.jpg', tem_local_map)
            return send_file(BytesIO(img_encoded), mimetype='image/jpeg')



    @staticmethod
    @minimap_bp.route('/minimap/get_local_map', methods=['GET'])
    def get_local_map():
        local_map_pos = minimap.local_map_pos
        if local_map_pos is None:
            return jsonify({'result': False})

        pix_pos = minimap.local_map_pos
        width = minimap.local_map_size
        tem_local_map = crop_img(large_map, pix_pos[0], pix_pos[1], width)
        img_base64 = cvimg_to_base64(tem_local_map)
        data = {
            'result': True,
            'data': {
                'position': pix_pos,
                'xywh': None,
                'img_base64': img_base64
            }
        }
        return jsonify(data)
