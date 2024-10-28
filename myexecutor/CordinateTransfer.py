import json
import os

import cv2

from myutils.configutils import resource_path

center_x = 19689.298
center_y = 13528.16


def get_map_absolute_xyxy(map_name, version=0):
    """
    获取地图绝对像素坐标：左上角(x1,y1)和右小角(x2,y2)
    :param map_name:
    :param version:
    :return:
    """
    from myutils.configutils import MapConfig
    allmap = MapConfig.get_all_map()
    name = allmap[map_name]['img_name']
    img_path = os.path.join(resource_path, 'map', 'segments', f'{name}_2048_v{version}.png')
    img = cv2.imread(img_path)
    h, w = img.shape[:2]
    center = allmap[map_name]['center']
    x1, y1 = center_x - center[0], center_y - center[1]
    x2, y2 = x1 + w, y1 + h
    return x1, y1, x2, y2


def to_abs_position(x, y):
    """
    minimap坐标转像素坐标
    :param x:
    :param y:
    :return:
    """
    return center_x + x, center_y + y


def get_country_from_minimap_position(x, y):
    """
    通过minimap坐标获取坐标所在地图
    思路：已知每张地图的尺寸和距离璃月中心点的偏差。
    :param x:
    :param y:
    :return:
    """

    def within_map(x, y, map_name):
        # 先将相对坐标转换为像素坐标
        x, y = to_abs_position(x, y)
        x1, y1, x2, y2 = get_map_absolute_xyxy(map_name)
        print(x1, y1, x2, y2)
        if x1 <= x <= x2 and y1 <= y <= y2: return map_name
        return None

    result = within_map(x, y, '蒙德') or \
             within_map(x, y, '璃月') or \
             within_map(x, y, '须弥') or \
             within_map(x, y, '枫丹') or \
             within_map(x, y, '稻妻') or \
             within_map(x, y, '纳塔')
    return result

    # if x1 > x > x2 and  y1 > y > y2: print("璃月")


def bgi2minimap(bgi_json, save_path, save=False):
    dx, dy = 790, 1241
    with open(bgi_json, 'r', encoding='utf8') as f:
        data = json.load(f)
        new_data = dict()
        info = data.get('info')
        print(info)
        new_data['name'] = info.get('name')
        new_data['anchor_name'] = '传送锚点'
        new_data['country'] = '璃月'
        point_type = info.get('type')
        if point_type == 'collect':
            new_data['executor'] = 'CollectPathExecutor'
        positions = data.get('positions', [])
        for position in positions:
            if position.get('move_mode') == 'walk':
                position['move_mode'] = 'normal'
            if position.get('type') == 'teleport':
                position['type'] = 'path'
            x = -position.get('x') + dx / 2
            y = -position.get('y') - dy / 2
            position['x'] = x * 2
            position['y'] = y * 2

        new_data['positions'] = positions
    print(new_data)
    # 如果 save 为 True，则保存修改后的 JSON 文件
    if save:
        with open(save_path, 'w', encoding='utf8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=4)
        print(f"修改后的 JSON 已保存到 {save_path}")


def minimap2bgi(minimap_json, save_path, save=False):
    dx, dy = 790, 1241
    with open(minimap_json, 'r', encoding='utf8') as f:
        data = json.load(f)
        new_data = dict()
        new_data['info'] = {
            'name': data.get('name'),
            'type': 'collect' if data.get('executor') == 'CollectPathExecutor' else 'other'
        }
        positions = data.get('positions', [])
        for index, position in enumerate(positions, start=1):  # 从1开始递增
            position['id'] = index  # 添加 id 字段
            if position.get('move_mode') == 'normal':
                position['move_mode'] = 'walk'
            if position.get('type') == 'path':
                position['type'] = 'teleport'
            x = -position.get('x') / 2 + dx / 2
            y = -position.get('y') / 2 - dy / 2
            position['x'] = x
            position['y'] = y

        new_data['positions'] = positions
    print(new_data)
    # 如果 save 为 True，则保存修改后的 JSON 文件
    if save:
        with open(save_path, 'w', encoding='utf8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=4)
        print(f"修改后的 JSON 已保存到 {save_path}")


def test1():
    folder = os.path.join(resource_path, 'pathlist', '灼灼彩菊')
    new_folder = os.path.join(resource_path, 'pathlist', 'bgi灼灼彩菊')
    if not os.path.exists(new_folder):
        os.makedirs(new_folder)
    files = os.listdir(folder)
    for file in files:
        file_path = os.path.join(folder, file)
        save_path = os.path.join(new_folder, f'bgi{file.split(".json")[0]}.json')
        try:
            # bgi2minimap(bgi_json=file_path, save_path=save_path, save=True)
            minimap2bgi(minimap_json=file_path, save_path=save_path, save=True)
        except Exception as e:
            print(e)


if __name__ == '__main__':
    country = get_country_from_minimap_position(0, 0)
    # country = get_country_from_minimap_position(1948,-4946)
    print(country)
