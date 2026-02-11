from PIL import Image

# 1. 读取图像并转为灰度图（灰度处理）
image = Image.open('1.3.png').convert('L')  # 'L'模式：灰度图（0-255）

# 2. 二值化处理（阈值128，可自定义）
def binarize(image, threshold=210):  # 修正阈值为128
    return image.point(lambda p: 255 if p > threshold else 0)

# 3. 保存二值化结果
binary_image = binarize(image)
binary_image.save('1.4.png')  # 文件名更清晰

print("处理完成")