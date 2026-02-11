import cv2
import astar1


def main():
    image_path = "1.4.png" #存放二值化带白色路径的地图(用于让a*寻路)
    img = cv2.imread(image_path)
    image_path2 = "1.3.png" #存放彩色带白色路径的地图(用于显示地图窗口的可视化)
    img2 = cv2.imread(image_path2)

    if img is None:
        print(f"错误：无法加载图片 '{image_path}'，请检查文件路径！")
        return

    # 保留原始彩色图像用于彩色地图窗口
    original_color = img2.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # astar1.py 0 = 可通行区域 | 1 = 障碍物
    _, binary_map = cv2.threshold(gray, 127, 1, cv2.THRESH_BINARY_INV)
    _, display_binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

    # 二值地图显示（用于路径规划）
    binary_display = cv2.cvtColor(display_binary, cv2.COLOR_GRAY2BGR)
    # 彩色地图显示（原始彩色图像）
    color_display = original_color.copy()

    # ====== 缩小窗口大小 ======
    # 获取原始图像尺寸
    orig_h, orig_w = img.shape[:2]
    # 设置新窗口尺寸为原图的一半
    new_w = orig_w // 2
    new_h = orig_h // 2

    # 创建窗口并设置为缩小后的尺寸
    #cv2.namedWindow('Binary Map', cv2.WINDOW_NORMAL)
    cv2.namedWindow('Color Map', cv2.WINDOW_NORMAL)
    #cv2.resizeWindow('Binary Map', new_w, new_h)
    cv2.resizeWindow('Color Map', new_w, new_h)
    # =============================

    # 当前显示状态（两个窗口独立维护）
    binary_current = binary_display.copy()
    color_current = color_display.copy()

    start, end = None, None
    state = 0  # 0=待起点, 1=待终点
    path_to_draw = None
    draw_index = 0
    path_drawn = False

    # 路径绘制参数（两个窗口使用不同颜色以增强可见性）
    BINARY_PATH_COLOR = (0, 0, 255)  #
    COLOR_PATH_COLOR = (0, 0, 255)  #
    PATH_THICKNESS_BINARY = 8
    PATH_THICKNESS_COLOR = 8

    def draw_markers(img, start, end):
        """在图像上绘制起点和终点标记（通用函数）"""
        if start:
            x, y = start[1], start[0]
            cv2.circle(img, (x, y), 7, (0, 0, 255), -1)  # 红色实心
            cv2.circle(img, (x, y), 9, (0, 0, 0), 2)  # 黑色外框
        if end:
            x, y = end[1], end[0]
            cv2.circle(img, (x, y), 7, (0, 255, 0), -1)  # 绿色实心
            cv2.circle(img, (x, y), 9, (0, 0, 0), 2)  # 黑色外框

    def mouse_callback(event, x, y, flags, param):
        nonlocal start, end, state, binary_current, color_current, path_to_draw, draw_index, path_drawn

        if event != cv2.EVENT_LBUTTONDOWN:
            return

        # 边界检查
        if not (0 <= y < binary_map.shape[0] and 0 <= x < binary_map.shape[1]):
            print("点击位置超出图像范围！")
            return

        # 验证点击位置是否在可通行区域
        if binary_map[y, x] != 0:
            actual_val = gray[y, x]
            print(f"无效点击！(x={x},y={y}) 位于障碍区（灰度值={actual_val}，应>127），请在白色区域点击")
            # 视觉反馈（两个窗口）
            for display_img, window_name in [(binary_current.copy(), 'Binary Map'),
                                             (color_current.copy(), 'Color Map')]:
                cv2.rectangle(display_img, (max(0, x - 8), max(0, y - 8)),
                              (min(display_img.shape[1], x + 8), min(display_img.shape[0], y + 8)), (0, 0, 255), 2)
            #cv2.imshow('Binary Map', binary_current)
            cv2.imshow('Color Map', color_current)
            cv2.waitKey(150)
            return

        if state == 0:  # 设置起点
            start = (y, x)
            state = 1
            print(f"起点设置成功 | 坐标(x={x},y={y}) | 灰度值={gray[y, x]}")

            # 更新两个窗口的显示
            #binary_current = binary_display.copy()
            color_current = color_display.copy()
            #draw_markers(binary_current, start, end)
            draw_markers(color_current, start, end)
            #cv2.imshow('Binary Map', binary_current)
            cv2.imshow('Color Map', color_current)

        elif state == 1:  # 设置终点
            if (y, x) == start:
                print("终点不能与起点重合！")
                return
            end = (y, x)
            state = 2
            print(f"终点设置成功 | 坐标(x={x},y={y})")

            # ====== 关键：在两个窗口永久显示终点标记 ======
            #binary_current = binary_display.copy()
            color_current = color_display.copy()
            #draw_markers(binary_current, start, end)
            draw_markers(color_current, start, end)
            #cv2.imshow('Binary Map', binary_current)
            cv2.imshow('Color Map', color_current)

            # ====== 计算路径（在主循环中逐步绘制） ======
            print("计算路径中.")
            path, duration = astar1.method(binary_map, start, end, hchoice=1)

            if not path or path == 0 or len(path) < 2:
                print("路径规划失败！检查原因：")
                print(" 1. 起点/终点是否在连通区域内？")
                print(" 2. 是否存在狭窄通道（astar.py的blocked函数会阻挡斜穿）？")

                # 在两个窗口显示失败提示
                for display_img, window_name in [(binary_current, 'Binary Map'), (color_current, 'Color Map')]:
                    result = display_img.copy()
                    cv2.putText(result, "NO PATH FOUND", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    cv2.imshow(window_name, result)
            else:
                print(f"路径规划成功 | 路径点数: {len(path)} | 耗时: {duration:.4f}s")

                # ====== 新增：将路径写入txt文件 ======
                with open('path_result.txt', 'w') as f:
                    for (y, x) in path:
                        # 将坐标写成(x,y)格式（先x后y，符合常规坐标表示）
                        f.write(f"{x},{y}\n")
                print("路径已保存到path_result.txt")

                # 保存路径用于逐步绘制（两个窗口同步）
                path_to_draw = path
                draw_index = 0
                path_drawn = False

    # 启动提示
    print("=" * 50)
    print("左键点击设置起点 → 终点")
    print("系统自动计算并逐步绘制路径")
    print("Binary Map: 二值地图 ")
    print("Color Map: 原始彩色地图 ")
    print("按 R 重置 | 按 ESC 退出")
    print("=" * 50)
    print("提示：在任一窗口点击均可设置点位")
    print("问题排查：若路径失败，请检查起点/终点是否被障碍完全包围")
    print("=" * 50)

    # 初始显示（使用缩小后的窗口）
    #cv2.imshow('Binary Map', binary_display)
    cv2.imshow('Color Map', color_display)

    # 设置鼠标回调
    #cv2.setMouseCallback('Binary Map', mouse_callback)
    cv2.setMouseCallback('Color Map', mouse_callback)

    # 主循环
    while True:
        key = cv2.waitKey(1) & 0xFF  # 40ms ≈ 25fps，流畅动画

        if key == 27:  # ESC
            print("\n程序退出")
            break
        elif key in (ord('r'), ord('R')):  # 重置
            start, end, state = None, None, 0
            path_to_draw = None
            draw_index = 0
            path_drawn = False
            #binary_current = binary_display.copy()
            color_current = color_display.copy()
            #cv2.imshow('Binary Map', binary_display)
            cv2.imshow('Color Map', color_display)
            print("\n界面已重置，请在白色可通行区域重新设置起点")

        # ====== 同步逐步绘制路径到两个窗口 ======
        if path_to_draw is not None and not path_drawn and draw_index < len(path_to_draw):
            # 获取当前点（注意：astar返回的是(y,x)格式）
            curr_y, curr_x = path_to_draw[draw_index]

            # 如果不是第一个点，绘制线段
            if draw_index > 0:
                prev_y, prev_x = path_to_draw[draw_index - 1]

                # 在二值地图窗口绘制
                #cv2.line(binary_current, (prev_x, prev_y), (curr_x, curr_y), BINARY_PATH_COLOR, PATH_THICKNESS_BINARY)

                # 在彩色地图窗口绘制
                cv2.line(color_current, (prev_x, prev_y), (curr_x, curr_y), COLOR_PATH_COLOR, PATH_THICKNESS_COLOR)

            # 更新绘制索引
            draw_index += 10

            # 检查是否绘制完成
            if draw_index >= len(path_to_draw):
                path_drawn = True
                print(f"路径绘制完成 总长度: {len(path_to_draw)} 个节点")

            # 同步更新两个窗口
            #cv2.imshow('Binary Map', binary_current)
            cv2.imshow('Color Map', color_current)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()