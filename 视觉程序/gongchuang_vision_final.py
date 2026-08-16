import os
import sys
import serial
import cv2
import numpy as np
import time 
import threading
from collections import defaultdict
from pyzbar.pyzbar import decode, ZBarSymbol
cv2.setUseOptimized(True)
cv2.setNumThreads(8)
A = ['1','3','2','+','3','1','2']   # 用于存储二维码数据
#A=[]
C_1 = None  
C_2 = None  
C_1_loop2 = None
C_2_loop2 = None
INDEX = 0
INDEX1 = 0
INDEX2 = 0
INDEX_loop2 = 0
INDEX1_loop2 = 0
INDEX2_loop2 = 0
cap=None
cap2=None

# 固定三工位物料区使用同一组 h/i 指令执行两轮。
# 0=二维码 A1/A2/A3，1=二维码 A4/A5/A6，2=两轮已完成。
sangeyuanxin_dangqian_lunci = 0
SANGEYUANXIN_ZONG_LUNCI = 2


def ensure_video2_camera():  # 复用上摄像头
    global cap, cap2

    candidates = []
    for camera in (cap, cap2):
        if camera is None or any(camera is existing for existing in candidates):
            continue
        try:
            if camera.isOpened():
                candidates.append(camera)
        except (cv2.error, AttributeError, TypeError):
            continue

    if candidates:
        selected = candidates[0]
        for duplicate in candidates[1:]:
            try:
                duplicate.release()
            except (cv2.error, AttributeError, TypeError):
                pass
        cap = selected
        cap2 = selected
        return selected

    stale_objects = []
    for camera in (cap, cap2):
        if camera is None or any(camera is existing for existing in stale_objects):
            continue
        stale_objects.append(camera)
        try:
            camera.release()
        except (cv2.error, AttributeError, TypeError):
            pass
    cap = None
    cap2 = None

    camera = cv2.VideoCapture("/dev/video2", cv2.CAP_V4L2)
    if camera is None or not camera.isOpened():
        if camera is not None:
            try:
                camera.release()
            except (cv2.error, AttributeError, TypeError):
                pass
        print("摄像头初始化失败")
        return None

    cap = camera
    cap2 = camera
    print("上摄像头已打开")
    return camera


def release_video2_camera():  # 释放上摄像头
    global cap, cap2
    released = []
    for camera in (cap, cap2):
        if camera is None or any(camera is existing for existing in released):
            continue
        released.append(camera)
        try:
            camera.release()
        except (cv2.error, AttributeError, TypeError):
            pass
    cap = None
    cap2 = None

roi_params_dingxin=(160,140,320,210)
roi_params = (220,70,200, 140)   # 正下方A3    c1
roi_params1 = (110,290,170,160)  # 左下角A1
roi_params2 = (320, 280, 210,160) # 右下角A2
roi_param_zhuazi=(210,300,220,160)#爪子

# 非转盘物料区参数，格式均为 (x, y, width, height)。
# 现场只需调下面三个ROI；Q1/Q2/Q3分别代表三个固定夹取位置。
SANGEYUANXIN_Q1_ROI = (90, 100, 180, 240)
SANGEYUANXIN_Q2_ROI = (225, 100, 170, 240)
SANGEYUANXIN_Q3_ROI = (360, 100, 170, 240)
SANGEYUANXIN_REGION_STABLE_FRAMES = 3
SANGEYUANXIN_COLOR_MIN_AREA_RATIO = 0.02
SANGEYUANXIN_COLOR_DOMINANCE_RATIO = 1.15
SANGEYUANXIN_TOTAL_TIMEOUT = 8.0

# 成品区转盘 Code 128 参数。条码1/2/3就是固定的第一/第二/第三夹取目标，
# 与二维码数组A和颜色映射完全独立。
TIAOXINGMA_VALID_CODES = frozenset(("1", "2", "3"))
TIAOXINGMA_FRAME_WIDTH = 640
TIAOXINGMA_FRAME_HEIGHT = 480
TIAOXINGMA_DINGBIAO_ROI = (120, 80, 400, 217)
TIAOXINGMA_BIANHUA_ROI = (220, 80, 200, 200)
TIAOXINGMA_WEIZHI23_ROI = (160, 270, 300, 200)
TIAOXINGMA_DINGBIAO_DX = 0
TIAOXINGMA_DINGBIAO_DY = 0
TIAOXINGMA_DINGBIAO_STABLE_FRAMES = 30
TIAOXINGMA_DINGBIAO_HISTORY = 15
TIAOXINGMA_BIANHUA_STABLE_FRAMES = 15
TIAOXINGMA_BIANHUA_HISTORY = 15
TIAOXINGMA_XUANZE_STABLE_FRAMES = 30
TIAOXINGMA_XUANZE_HISTORY = 15
TIAOXINGMA_BUJU_STABLE_FRAMES = 3
TIAOXINGMA_MAX_PIXEL_MOVE = 10.0
TIAOXINGMA_CODE_CONFIDENCE = 0.7
TIAOXINGMA_TIMEOUT_SECONDS = 8.0
TIAOXINGMA_FAILURE_PAYLOAD = "000000004"
TIAOXINGMA_CONFIRM_PAYLOAD = "987654321"

# 条码转盘独立状态；禁止复用二维码数组A或颜色转盘的C_1/INDEX等状态。
dingbiao_tiaoma = None
dingbiao_zhongxin = None
bianhua_tiaoma = None
diyici_jiaqu_weizhi = None
dierci_jiaqu_weizhi = None
disanci_jiaqu_weizhi = None
tiaoxingma_fangxiang = None

ser = serial.Serial(
    port='/dev/ttyUSB0',      # 根据你的STM32实际端口进行修改
    baudrate=9600,            # 设置波特率为9600
    bytesize=serial.EIGHTBITS, # 数据位为8
    stopbits=serial.STOPBITS_ONE,  # 停止位为1
    parity=serial.PARITY_NONE,     # 校验位为None 
    timeout=0.1
)

def restart_program():
    print("接收到数字指令0，程序将在20秒后重新启动...")
    time.sleep(20)
    python = sys.executable
    os.execl(python, python, *sys.argv)

def send_data(data):
    array = [ord(char) for char in data]
    while len(array) < 9: 
        array.append(0)
    data_packet = bytes([0xFF] + array[:9] + [0xFE]) 
    ser.write(data_packet)
    print(f"发送: {data_packet}") 

def receive_data():
    if ser.in_waiting > 0:
        data = ser.readline().decode('utf-8').strip()
        return data
    return None

def wait_and_receive_data():
    global A
    start_time = time.time()
    while time.time() - start_time < 1:
        data = receive_data()
        if data and len(data) == 7:
            A = list(data)
            _sangeyuanxin_chongzhi_lunci()
            print(f"接收到的数据: {data}")
            print(f"已存储到数组A: {A}")
            return
    print("等待1秒钟未接收到数据，重新开始...")

def get_color_name(bgr_val):
    blue, green, red = bgr_val
    if red > blue and red > green:
        return "Red", "1"
    elif green > red and green > blue:
        return "Green", "2"
    elif blue > red and blue > green:
        return "Blue", "3"
    else:
        return "Unknown", "0"
    
def run_erweima():
    global A
    #if not ser.is_open:
        #ser.open()
    print(f"串口已打开，执行二维码检测任务...")
    
    cap0 = cv2.VideoCapture("/dev/video0",cv2.CAP_V4L2)
    if not cap0.isOpened():
        print("无法打开摄像头")
        send_data("摄像头打开失败")
        return

    consistent_count = 0
    last_data = None
    last_valid_data = None

    try:
        while True:
            ret, frame = cap0.read()
            if not ret:
                print("无法接收帧，退出...")
                send_data("帧读取错误")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            decoded_objects = decode(gray)

            current_data = None
            
            for obj in decoded_objects:
                try:
                    data = obj.data.decode('utf-8').strip()
                    if len(data) == 7:  # 只处理7字符长度的数据
                        current_data = data
                        break
                except:
                    continue

            if current_data:
                print(f"检测到二维码数据: {current_data}")

                if current_data == last_data:
                    consistent_count += 1
                else:
                    consistent_count = 1
                    last_data = current_data

                if consistent_count >= 3:
                    A = list(current_data)  # 存储到全局数组A
                    _sangeyuanxin_chongzhi_lunci()
                    print(f"解析二维码数据到数组 A: {A}")
                    
                    # 格式化发送数据（7字符+补零）
                    formatted_data = current_data.ljust(7, '0')[:7] + '0'
                    send_data(formatted_data)
                    last_valid_data = current_data
                    break

            # cv2.imshow('QR Code Scanner', frame)
            if cv2.waitKey(1) == ord('q'):
                print("用户手动终止识别")
                break

    finally:
        cap0.release()
        cv2.destroyAllWindows()
        if last_valid_data is None:
            send_data("二维码数据错误")
    

def _configure_calibration_camera(camera, width, height):
    if camera is None or not camera.isOpened():
        print("摄像头未打开，无法配置定标模式")
        return False

    settings = (
        ("fourcc", cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG")),
        ("width", cv2.CAP_PROP_FRAME_WIDTH, width),
        ("height", cv2.CAP_PROP_FRAME_HEIGHT, height),
        ("fps", cv2.CAP_PROP_FPS, 30),
        ("buffers", cv2.CAP_PROP_BUFFERSIZE, 2),
    )
    results = {}
    for name, prop, value in settings:
        try:
            results[name] = bool(camera.set(prop, value))
        except (cv2.error, TypeError, ValueError) as exc:
            results[name] = False
            print(f"设置 {name} 失败: {exc}")

    try:
        actual_fourcc_value = int(camera.get(cv2.CAP_PROP_FOURCC))
        actual_fourcc = "".join(
            chr((actual_fourcc_value >> (8 * index)) & 0xFF) for index in range(4)
        )
        if not actual_fourcc.isprintable() or not actual_fourcc.strip("\x00"):
            actual_fourcc = "UNKNOWN"
        actual_width = int(round(camera.get(cv2.CAP_PROP_FRAME_WIDTH)))
        actual_height = int(round(camera.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        actual_fps = float(camera.get(cv2.CAP_PROP_FPS))
    except (cv2.error, TypeError, ValueError, OverflowError) as exc:
        actual_fourcc = "UNKNOWN"
        actual_width = 0
        actual_height = 0
        actual_fps = 0.0
        print(f"读取摄像头实际参数失败: {exc}")

    set_ok = all(results.values())
    print(
        f"摄像头请求{width}x{height}@30/MJPG，"
        f"实际{actual_width}x{actual_height}@{actual_fps:.2f}/{actual_fourcc}"
    )
    if not set_ok:
        print("部分相机参数未被驱动接受，继续使用实际模式")
    return set_ok


def tiaoxingma_huoqu_fuhao_weizhi(fuhao):
    dianji = []
    for dian in (getattr(fuhao, "polygon", None) or ()):
        try:
            dian_x = float(dian.x)
            dian_y = float(dian.y)
        except (AttributeError, TypeError, ValueError):
            try:
                dian_x = float(dian[0])
                dian_y = float(dian[1])
            except (IndexError, TypeError, ValueError):
                continue
        if np.isfinite(dian_x) and np.isfinite(dian_y):
            dianji.append((dian_x, dian_y))

    if len(dianji) >= 3:
        try:
            dian_array = np.asarray(dianji, dtype=np.float32)
            (zhongxin_x, zhongxin_y), _, _ = cv2.minAreaRect(dian_array)
            tubao = cv2.convexHull(dian_array)
            mianji = abs(float(cv2.contourArea(tubao)))
            if (
                np.isfinite(zhongxin_x)
                and np.isfinite(zhongxin_y)
                and mianji > 0
            ):
                return float(zhongxin_x), float(zhongxin_y), mianji
        except (cv2.error, TypeError, ValueError):
            pass

    rect = getattr(fuhao, "rect", None)
    if rect is None:
        return None
    try:
        left = float(rect.left)
        top = float(rect.top)
        width = float(rect.width)
        height = float(rect.height)
    except (AttributeError, TypeError, ValueError):
        return None
    if (
        not np.all(np.isfinite((left, top, width, height)))
        or width <= 0
        or height <= 0
    ):
        return None
    return left + width / 2.0, top + height / 2.0, width * height


def tiaoxingma_jiema_danzhen(tuxiang, roi=None, clahe=None):
    if tuxiang is None or getattr(tuxiang, "size", 0) == 0:
        return {}

    pianyi_x = 0
    pianyi_y = 0
    roi_tuxiang = tuxiang
    if roi is not None:
        try:
            roi_x, roi_y, roi_w, roi_h = (int(value) for value in roi)
        except (TypeError, ValueError):
            return {}
        tuxiang_h, tuxiang_w = tuxiang.shape[:2]
        if (
            roi_x < 0
            or roi_y < 0
            or roi_w <= 0
            or roi_h <= 0
            or roi_x + roi_w > tuxiang_w
            or roi_y + roi_h > tuxiang_h
        ):
            return {}
        roi_tuxiang = tuxiang[roi_y:roi_y + roi_h, roi_x:roi_x + roi_w]
        pianyi_x = roi_x
        pianyi_y = roi_y

    if len(roi_tuxiang.shape) == 2:
        huidu = roi_tuxiang
    else:
        huidu = cv2.cvtColor(roi_tuxiang, cv2.COLOR_BGR2GRAY)
    if clahe is None:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    jiema_jieguo = {}
    for houxuan_tuxiang in (huidu, clahe.apply(huidu)):
        try:
            fuhaoji = decode(houxuan_tuxiang, symbols=[ZBarSymbol.CODE128])
        except TypeError:
            # 兼容少数不支持 symbols 参数的旧版 pyzbar，仍严格检查码制。
            fuhaoji = decode(houxuan_tuxiang)

        for fuhao in fuhaoji or ():
            if str(getattr(fuhao, "type", "")).upper() != "CODE128":
                continue
            try:
                tiaoma = fuhao.data.decode("ascii")
            except (AttributeError, UnicodeDecodeError):
                continue
            if tiaoma not in TIAOXINGMA_VALID_CODES:
                continue

            weizhi = tiaoxingma_huoqu_fuhao_weizhi(fuhao)
            if weizhi is None:
                continue
            quanju_weizhi = (
                weizhi[0] + pianyi_x,
                weizhi[1] + pianyi_y,
                weizhi[2],
            )
            shangyige = jiema_jieguo.get(tiaoma)
            if shangyige is None or quanju_weizhi[2] > shangyige[2]:
                jiema_jieguo[tiaoma] = quanju_weizhi
    return jiema_jieguo


def tiaoxingma_yonghu_zhongzhi():
    try:
        return (cv2.waitKey(1) & 0xFF) == ord("q")
    except cv2.error:
        return False


def tiaoxingma_huoqu_gongxiang_xiangji():
    global cap, cap2
    xiangji = ensure_video2_camera()
    if xiangji is None:
        return None
    cap = xiangji
    cap2 = xiangji
    _configure_calibration_camera(
        xiangji,
        TIAOXINGMA_FRAME_WIDTH,
        TIAOXINGMA_FRAME_HEIGHT,
    )
    return xiangji


def tiaoxingma_qingkong_quanbu_zhuangtai():
    global dingbiao_tiaoma, dingbiao_zhongxin, bianhua_tiaoma
    global diyici_jiaqu_weizhi, dierci_jiaqu_weizhi
    global disanci_jiaqu_weizhi, tiaoxingma_fangxiang
    dingbiao_tiaoma = None
    dingbiao_zhongxin = None
    bianhua_tiaoma = None
    diyici_jiaqu_weizhi = None
    dierci_jiaqu_weizhi = None
    disanci_jiaqu_weizhi = None
    tiaoxingma_fangxiang = None


def tiaoxingma_qingkong_jiaqu_zhuangtai():
    global bianhua_tiaoma, diyici_jiaqu_weizhi, dierci_jiaqu_weizhi
    global disanci_jiaqu_weizhi, tiaoxingma_fangxiang
    bianhua_tiaoma = None
    diyici_jiaqu_weizhi = None
    dierci_jiaqu_weizhi = None
    disanci_jiaqu_weizhi = None
    tiaoxingma_fangxiang = None


def tiaoxingma_wending_jiance(
    xiangji,
    roi,
    wending_zhenshu,
    lishi_changdu,
    xindu_yuzhi,
    mubiao_tiaoma=None,
    jizhun_tiaoma=None,
    jieduan_mingcheng="条码检测",
):
    if xiangji is None or not xiangji.isOpened():
        return None, None, "相机未打开"

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    kaishi_shijian = time.monotonic()
    jizhun_zhongxin = None
    wending_jishu = 0
    yangben = []
    duqu_shibai = 0
    shangci_qiyi_tiaoma = None

    while time.monotonic() - kaishi_shijian < TIAOXINGMA_TIMEOUT_SECONDS:
        ret, tuxiang = xiangji.read()
        if not ret or tuxiang is None:
            duqu_shibai += 1
            if duqu_shibai == 1 or duqu_shibai % 30 == 0:
                print(f"[TIAOXINGMA] {jieduan_mingcheng}读取画面失败，次数={duqu_shibai}")
            time.sleep(0.02)
            continue
        duqu_shibai = 0

        jiema_jieguo = tiaoxingma_jiema_danzhen(tuxiang, roi, clahe)
        if len(jiema_jieguo) != 1:
            if len(jiema_jieguo) > 1:
                qiyi_tiaoma = tuple(sorted(jiema_jieguo))
                if qiyi_tiaoma != shangci_qiyi_tiaoma:
                    print(
                        f"[TIAOXINGMA] {jieduan_mingcheng}同一ROI出现多个编号，"
                        f"本帧作废: {qiyi_tiaoma}"
                    )
                shangci_qiyi_tiaoma = qiyi_tiaoma
            else:
                shangci_qiyi_tiaoma = None
            if tiaoxingma_yonghu_zhongzhi():
                return None, None, "用户按q终止"
            continue
        shangci_qiyi_tiaoma = None

        dangqian_tiaoma, dangqian_weizhi = next(iter(jiema_jieguo.items()))
        dangqian_zhongxin = (dangqian_weizhi[0], dangqian_weizhi[1])

        if mubiao_tiaoma is not None and dangqian_tiaoma != mubiao_tiaoma:
            jizhun_zhongxin = None
            wending_jishu = 0
            yangben = []
            if tiaoxingma_yonghu_zhongzhi():
                return None, None, "用户按q终止"
            continue
        if jizhun_tiaoma is not None and dangqian_tiaoma == jizhun_tiaoma:
            jizhun_zhongxin = None
            wending_jishu = 0
            yangben = []
            if tiaoxingma_yonghu_zhongzhi():
                return None, None, "用户按q终止"
            continue

        if jizhun_zhongxin is None:
            jizhun_zhongxin = dangqian_zhongxin
            wending_jishu = 1
            yangben = [(dangqian_tiaoma, *dangqian_zhongxin)]
        else:
            juli = float(np.hypot(
                dangqian_zhongxin[0] - jizhun_zhongxin[0],
                dangqian_zhongxin[1] - jizhun_zhongxin[1],
            ))
            if juli < TIAOXINGMA_MAX_PIXEL_MOVE:
                wending_jishu += 1
                yangben.append((dangqian_tiaoma, *dangqian_zhongxin))
            else:
                jizhun_zhongxin = dangqian_zhongxin
                wending_jishu = 1
                yangben = [(dangqian_tiaoma, *dangqian_zhongxin)]

        if wending_jishu >= wending_zhenshu and len(yangben) >= lishi_changdu:
            tiaoma_jishu = defaultdict(int)
            for tiaoma, _, _ in yangben:
                tiaoma_jishu[tiaoma] += 1
            zuiduo_tiaoma, zuiduo_cishu = max(
                tiaoma_jishu.items(),
                key=lambda item: item[1],
            )
            xindu = zuiduo_cishu / len(yangben)
            if xindu >= xindu_yuzhi:
                zhongxin_yangben = np.asarray(
                    [
                        (zhongxin_x, zhongxin_y)
                        for tiaoma, zhongxin_x, zhongxin_y in yangben
                        if tiaoma == zuiduo_tiaoma
                    ],
                    dtype=np.float64,
                )
                if zhongxin_yangben.size > 0:
                    zhongxin = (
                        float(np.median(zhongxin_yangben[:, 0])),
                        float(np.median(zhongxin_yangben[:, 1])),
                    )
                    print(
                        f"[TIAOXINGMA] {jieduan_mingcheng}稳定: "
                        f"编号={zuiduo_tiaoma}, 中心={zhongxin}, "
                        f"样本={len(yangben)}, 置信度={xindu:.2f}"
                    )
                    return zuiduo_tiaoma, zhongxin, None

        if tiaoxingma_yonghu_zhongzhi():
            return None, None, "用户按q终止"

    return None, None, f"{jieduan_mingcheng}超时"


def tiaoxingma_fasong_shibai(yuanyin):
    print(f"[TIAOXINGMA] 任务失败: {yuanyin}")
    send_data(TIAOXINGMA_FAILURE_PAYLOAD)
    return None


def yunxing_tiaoxingma_dingbiao():  # 成品区条码首次定标
    global dingbiao_tiaoma, dingbiao_zhongxin
    tiaoxingma_qingkong_quanbu_zhuangtai()
    xiangji = tiaoxingma_huoqu_gongxiang_xiangji()
    if xiangji is None:
        return tiaoxingma_fasong_shibai("/dev/video2初始化失败")

    tiaoma, zhongxin, yuanyin = tiaoxingma_wending_jiance(
        xiangji,
        TIAOXINGMA_DINGBIAO_ROI,
        TIAOXINGMA_DINGBIAO_STABLE_FRAMES,
        TIAOXINGMA_DINGBIAO_HISTORY,
        TIAOXINGMA_CODE_CONFIDENCE,
        jieduan_mingcheng="d定标",
    )
    if tiaoma is None or zhongxin is None:
        return tiaoxingma_fasong_shibai(yuanyin or "d定标未得到稳定条码")

    fasong_x = int(round(zhongxin[0] + TIAOXINGMA_DINGBIAO_DX))
    fasong_y = int(round(zhongxin[1] + TIAOXINGMA_DINGBIAO_DY))
    if not (
        0 <= fasong_x < TIAOXINGMA_FRAME_WIDTH
        and 0 <= fasong_y < TIAOXINGMA_FRAME_HEIGHT
    ):
        return tiaoxingma_fasong_shibai(
            f"d定标补偿后坐标越界: ({fasong_x}, {fasong_y})"
        )

    baowen = f"{fasong_x:04d}{fasong_y:04d}{tiaoma}"
    if len(baowen) != 9:
        return tiaoxingma_fasong_shibai(f"d定标报文长度异常: {baowen}")

    dingbiao_tiaoma = tiaoma
    dingbiao_zhongxin = (fasong_x, fasong_y)
    send_data(baowen)
    print(
        f"[TIAOXINGMA] d定标成功: 原始中心={zhongxin}, "
        f"补偿=({TIAOXINGMA_DINGBIAO_DX}, {TIAOXINGMA_DINGBIAO_DY}), "
        f"条码={tiaoma}, 已发送={baowen}"
    )
    return baowen


def yunxing_tiaoxingma_dengdai_bianhua(xiangji):
    global bianhua_tiaoma
    if dingbiao_tiaoma not in TIAOXINGMA_VALID_CODES:
        return None, "尚未完成d条码定标"

    tiaoma, _, yuanyin = tiaoxingma_wending_jiance(
        xiangji,
        TIAOXINGMA_BIANHUA_ROI,
        TIAOXINGMA_BIANHUA_STABLE_FRAMES,
        TIAOXINGMA_BIANHUA_HISTORY,
        TIAOXINGMA_CODE_CONFIDENCE,
        jizhun_tiaoma=dingbiao_tiaoma,
        jieduan_mingcheng="e等待变化",
    )
    if tiaoma is None:
        return None, yuanyin or "e未检测到变化条码"
    bianhua_tiaoma = tiaoma
    print(
        f"[TIAOXINGMA] e确认条码变化: "
        f"基准={dingbiao_tiaoma}, 当前={bianhua_tiaoma}"
    )
    return tiaoma, None


def tiaoxingma_shibie_sange_weizhi(xiangji):
    if xiangji is None or not xiangji.isOpened():
        return None, "三位置识别时相机未打开"

    quyuji = {
        "zuoxia": roi_params1,
        "youxia": roi_params2,
        "shangfang": roi_params,
    }
    houxuan = {mingcheng: None for mingcheng in quyuji}
    wending_jishu = {mingcheng: 0 for mingcheng in quyuji}
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    kaishi_shijian = time.monotonic()
    duqu_shibai = 0
    shangci_chongfu_jieguo = None

    while time.monotonic() - kaishi_shijian < TIAOXINGMA_TIMEOUT_SECONDS:
        ret, tuxiang = xiangji.read()
        if not ret or tuxiang is None:
            duqu_shibai += 1
            if duqu_shibai == 1 or duqu_shibai % 30 == 0:
                print(f"[TIAOXINGMA] 三位置读取画面失败，次数={duqu_shibai}")
            time.sleep(0.02)
            continue
        duqu_shibai = 0

        for mingcheng, roi in quyuji.items():
            jiema_jieguo = tiaoxingma_jiema_danzhen(tuxiang, roi, clahe)
            if len(jiema_jieguo) != 1:
                if len(jiema_jieguo) > 1:
                    houxuan[mingcheng] = None
                    wending_jishu[mingcheng] = 0
                continue
            tiaoma = next(iter(jiema_jieguo))
            if tiaoma == houxuan[mingcheng]:
                wending_jishu[mingcheng] += 1
            else:
                houxuan[mingcheng] = tiaoma
                wending_jishu[mingcheng] = 1

        if all(
            wending_jishu[mingcheng] >= TIAOXINGMA_BUJU_STABLE_FRAMES
            for mingcheng in quyuji
        ):
            jieguo = (
                houxuan["zuoxia"],
                houxuan["youxia"],
                houxuan["shangfang"],
            )
            if set(jieguo) == TIAOXINGMA_VALID_CODES and len(set(jieguo)) == 3:
                print(
                    f"[TIAOXINGMA] 三位置稳定: 左下={jieguo[0]}, "
                    f"右下={jieguo[1]}, 上方={jieguo[2]}"
                )
                return jieguo, None
            if jieguo != shangci_chongfu_jieguo:
                print(f"[TIAOXINGMA] 三位置编号不完整或重复，继续检测: {jieguo}")
                shangci_chongfu_jieguo = jieguo

        if tiaoxingma_yonghu_zhongzhi():
            return None, "用户按q终止三位置识别"

    return None, f"三位置识别超时，候选={houxuan}，稳定计数={wending_jishu}"


def tiaoxingma_jisuan_jiaqu_weizhi(
    zuoxia_tiaoma,
    youxia_tiaoma,
    shangfang_tiaoma,
    jizhun_tiaoma,
):
    weizhi_tiaoma = (zuoxia_tiaoma, youxia_tiaoma, shangfang_tiaoma)
    if set(weizhi_tiaoma) != TIAOXINGMA_VALID_CODES or len(set(weizhi_tiaoma)) != 3:
        return None
    if jizhun_tiaoma not in TIAOXINGMA_VALID_CODES:
        return None

    nishizhen = zuoxia_tiaoma == jizhun_tiaoma
    b_shuzu = [shangfang_tiaoma, youxia_tiaoma, zuoxia_tiaoma]
    if nishizhen:
        b1_shuzu = [youxia_tiaoma, zuoxia_tiaoma, shangfang_tiaoma]
        b2_shuzu = [zuoxia_tiaoma, shangfang_tiaoma, youxia_tiaoma]
        fangxiang = "逆时针"
    else:
        b1_shuzu = [zuoxia_tiaoma, shangfang_tiaoma, youxia_tiaoma]
        b2_shuzu = [youxia_tiaoma, zuoxia_tiaoma, shangfang_tiaoma]
        fangxiang = "顺时针"

    diyici_weizhi = b_shuzu.index("1") + 1
    dierci_weizhi = b1_shuzu.index("2") + 1
    disanci_weizhi = b2_shuzu.index("3") + 1
    return {
        "fangxiang": fangxiang,
        "nishizhen": nishizhen,
        "B": tuple(b_shuzu),
        "B1": tuple(b1_shuzu),
        "B2": tuple(b2_shuzu),
        "weizhi": (diyici_weizhi, dierci_weizhi, disanci_weizhi),
    }


def yunxing_tiaoxingma_zhuanpan():  # 成品区转盘判向和三次夹取位置
    global diyici_jiaqu_weizhi, dierci_jiaqu_weizhi
    global disanci_jiaqu_weizhi, tiaoxingma_fangxiang
    tiaoxingma_qingkong_jiaqu_zhuangtai()
    if dingbiao_tiaoma not in TIAOXINGMA_VALID_CODES:
        return tiaoxingma_fasong_shibai("未完成d定标，不能执行e")

    xiangji = tiaoxingma_huoqu_gongxiang_xiangji()
    if xiangji is None:
        return tiaoxingma_fasong_shibai("e任务/dev/video2初始化失败")

    _, yuanyin = yunxing_tiaoxingma_dengdai_bianhua(xiangji)
    if yuanyin is not None:
        return tiaoxingma_fasong_shibai(yuanyin)

    sange_jieguo, yuanyin = tiaoxingma_shibie_sange_weizhi(xiangji)
    if sange_jieguo is None:
        tiaoxingma_qingkong_jiaqu_zhuangtai()
        return tiaoxingma_fasong_shibai(yuanyin or "未识别完整三位置")
    zuoxia_tiaoma, youxia_tiaoma, shangfang_tiaoma = sange_jieguo

    jisuan_jieguo = tiaoxingma_jisuan_jiaqu_weizhi(
        zuoxia_tiaoma,
        youxia_tiaoma,
        shangfang_tiaoma,
        dingbiao_tiaoma,
    )
    if jisuan_jieguo is None:
        tiaoxingma_qingkong_jiaqu_zhuangtai()
        return tiaoxingma_fasong_shibai("B/B1/B2夹取位置推演失败")

    (
        diyici_jiaqu_weizhi,
        dierci_jiaqu_weizhi,
        disanci_jiaqu_weizhi,
    ) = jisuan_jieguo["weizhi"]
    tiaoxingma_fangxiang = jisuan_jieguo["fangxiang"]
    baowen = (
        f"{diyici_jiaqu_weizhi}{dierci_jiaqu_weizhi}"
        f"{disanci_jiaqu_weizhi}456789"
    )
    if len(baowen) != 9:
        tiaoxingma_qingkong_jiaqu_zhuangtai()
        return tiaoxingma_fasong_shibai(f"e位置报文长度异常: {baowen}")

    send_data(baowen)
    print(
        f"[TIAOXINGMA] e识别成功: 方向={tiaoxingma_fangxiang}, "
        f"B={jisuan_jieguo['B']}, B1={jisuan_jieguo['B1']}, "
        f"B2={jisuan_jieguo['B2']}, 夹取位置={jisuan_jieguo['weizhi']}, "
        f"已发送={baowen}"
    )
    return baowen


def yunxing_tiaoxingma_xuanzequyu(jiaqu_weizhi, mubiao_tiaoma):
    if jiaqu_weizhi not in (1, 2, 3):
        return tiaoxingma_fasong_shibai(f"夹取位置无效: {jiaqu_weizhi}")
    if mubiao_tiaoma not in TIAOXINGMA_VALID_CODES:
        return tiaoxingma_fasong_shibai(f"目标条码无效: {mubiao_tiaoma}")

    xiangji = tiaoxingma_huoqu_gongxiang_xiangji()
    if xiangji is None:
        return tiaoxingma_fasong_shibai("夹取确认/dev/video2初始化失败")

    # 原命令5/6只有位置1看上方ROI，其余位置都在夹爪ROI确认。
    roi = roi_params if jiaqu_weizhi == 1 else roi_param_zhuazi
    tiaoma, _, yuanyin = tiaoxingma_wending_jiance(
        xiangji,
        roi,
        TIAOXINGMA_XUANZE_STABLE_FRAMES,
        TIAOXINGMA_XUANZE_HISTORY,
        TIAOXINGMA_CODE_CONFIDENCE,
        mubiao_tiaoma=mubiao_tiaoma,
        jieduan_mingcheng=f"夹取确认{mubiao_tiaoma}",
    )
    if tiaoma != mubiao_tiaoma:
        return tiaoxingma_fasong_shibai(yuanyin or f"未稳定识别条码{mubiao_tiaoma}")

    send_data(TIAOXINGMA_CONFIRM_PAYLOAD)
    print(
        f"[TIAOXINGMA] 条码{mubiao_tiaoma}已稳定，位置={jiaqu_weizhi}，"
        f"已发送={TIAOXINGMA_CONFIRM_PAYLOAD}"
    )
    return TIAOXINGMA_CONFIRM_PAYLOAD


def run_wukuaiyuanxin_1():  # 第一圈物块定标
    global cap
    if not cap.isOpened():
        print("摄像头初始化失败")
        return
    _configure_calibration_camera(cap, 640, 480)
    
    color_thresholds = {
        'red': {'lower1': [0, 100, 100], 'upper1': [10, 255, 255],
                'lower2': [160, 100, 100], 'upper2': [180, 255, 255]},
        'green': {'lower': [35, 40, 40], 'upper': [89, 255, 255]},
        'blue': {'lower': [90, 60, 60], 'upper': [140, 255, 255]}
    }
    
    detection_area = [120, 80, 400, 217]
    circle_params = {'min_radius': 25, 'max_radius': 45, 'param1': 25, 'param2': 25}
    stability_settings = {
        'threshold': 30,
        'max_pixel_move': 10,
        'color_stable_threshold': 15,
        'color_confidence': 0.7
    }
    timeout_settings = {'timeout_ms': 100}
    kernel_size = 3
    
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    stable_count = 0
    first_center = None
    last_detection_time = None
    color_history = []
    final_color = None
    last_radius = 0
    last_color_code = None
    
    def detect_stacking_and_color(frame):
        nonlocal last_radius, last_color_code
        x, y, w, h = detection_area
        roi_img = frame[y:y+h, x:x+w]
        
        gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (9, 9), 2, 2)
        
        circles = cv2.HoughCircles(
            gray, cv2.HOUGH_GRADIENT, 1, 20,
            param1=circle_params['param1'],
            param2=circle_params['param2'],
            minRadius=circle_params['min_radius'],
            maxRadius=circle_params['max_radius']
        )
        
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                center = (i[0] + x, i[1] + y)
                radius = i[2]
                last_radius = radius
                
                mask = np.zeros_like(gray)
                cv2.circle(mask, (i[0], i[1]), radius, 255, -1)
                hsv_img = cv2.cvtColor(roi_img, cv2.COLOR_BGR2HSV)
                
                lower_red1 = np.array(color_thresholds['red']['lower1'])
                upper_red1 = np.array(color_thresholds['red']['upper1'])
                lower_red2 = np.array(color_thresholds['red']['lower2'])
                upper_red2 = np.array(color_thresholds['red']['upper2'])
                lower_green = np.array(color_thresholds['green']['lower'])
                upper_green = np.array(color_thresholds['green']['upper'])
                lower_blue = np.array(color_thresholds['blue']['lower'])
                upper_blue = np.array(color_thresholds['blue']['upper'])
                
                red_mask1 = cv2.inRange(hsv_img, lower_red1, upper_red1)
                red_mask2 = cv2.inRange(hsv_img, lower_red2, upper_red2)
                red_mask = cv2.bitwise_or(red_mask1, red_mask2)
                green_mask = cv2.inRange(hsv_img, lower_green, upper_green)
                blue_mask = cv2.inRange(hsv_img, lower_blue, upper_blue)
                
                red_mask = cv2.erode(red_mask, kernel, iterations=1)
                red_mask = cv2.dilate(red_mask, kernel, iterations=2)
                green_mask = cv2.erode(green_mask, kernel, iterations=2)
                green_mask = cv2.dilate(green_mask, kernel, iterations=6)
                blue_mask = cv2.erode(blue_mask, kernel, iterations=1)
                blue_mask = cv2.dilate(blue_mask, kernel, iterations=3)
                
                red_area = cv2.countNonZero(cv2.bitwise_and(red_mask, mask))
                green_area = cv2.countNonZero(cv2.bitwise_and(green_mask, mask))
                blue_area = cv2.countNonZero(cv2.bitwise_and(blue_mask, mask))
                
                max_area = max(red_area, green_area, blue_area)
                if max_area == red_area:
                    color_code = "1"
                elif max_area == green_area:
                    color_code = "2"
                else:
                    color_code = "3"
                
                last_color_code = color_code
                formatted_data = f"{center[0]:04}{center[1]:04}{color_code}{radius:01}"
                return formatted_data, center, color_code
        return None, None, None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("无法读取摄像头帧")
            break
        
        x, y, w, h = detection_area
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        current_time = cv2.getTickCount()
        data, current_center, current_color = detect_stacking_and_color(frame)
        
        if data and current_color:
            last_detection_time = current_time
            color_history.append(current_color)
            
            if first_center is None:
                first_center = current_center
                stable_count = 1
            else:
                distance = np.sqrt((current_center[0] - first_center[0])**2 + 
                                 (current_center[1] - first_center[1])**2)
                if distance < stability_settings['max_pixel_move']:
                    stable_count += 1
                else:
                    stable_count = 1
                    first_center = current_center
                    color_history = []
            
            if len(color_history) >= stability_settings['color_stable_threshold']:
                color_counter = defaultdict(int)
                for color in color_history:
                    color_counter[color] += 1
                
                most_common_color = max(color_counter.items(), key=lambda x: x[1])[0]
                confidence = color_counter[most_common_color] / len(color_history)
                
                if confidence >= stability_settings['color_confidence']:
                    final_color = most_common_color
                    print(f"颜色识别稳定: {most_common_color} (置信度: {confidence:.2f})")
            
            if (stable_count >= stability_settings['threshold'] and 
                final_color is not None):
                formatted_data = f"{current_center[0]:04}{current_center[1]:04}{final_color}{last_radius:01}"
                send_data(formatted_data)
                print(f"发送的物块数据: {formatted_data}")
                C_1 = final_color
                break
        else:
            if last_detection_time is not None:
                elapsed_time = (current_time - last_detection_time) / cv2.getTickFrequency() * 1000
                if elapsed_time > timeout_settings['timeout_ms']:
                    print("检测超时，跳过本次识别")
                    continue
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cv2.destroyAllWindows()
    return C_1

def run_wukuaiyuanxin_2():  # 转盘第二个物块
    global cap
    if not cap.isOpened():
        print("摄像头初始化失败")
        return
    _configure_calibration_camera(cap, 640, 480)
    
    color_thresholds = {
        'red': {'lower1': [0, 100, 100], 'upper1': [10, 255, 255],
                'lower2': [160, 100, 100], 'upper2': [180, 255, 255]},
        'green': {'lower': [35, 40, 40], 'upper': [89, 255, 255]},
        'blue': {'lower': [90, 60, 60], 'upper': [140, 255, 255]}
    }
    
    detection_area = [220,80,200,200]
    circle_params = {'min_radius': 25, 'max_radius': 45, 'param1': 25, 'param2': 25}
    stability_settings = {
        'threshold': 10,
        'max_pixel_move': 10,
        'color_stable_threshold': 15,
        'color_confidence': 0.7
    }
    timeout_settings = {'timeout_ms': 1000}
    kernel_size = 3
    
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    stable_count = 0
    first_center = None
    last_detection_time = None
    color_history = []
    final_color = None
    last_radius = 0
    last_color_code = None
    
    def detect_stacking_and_color(frame):
        nonlocal last_radius, last_color_code
        x, y, w, h = detection_area
        roi_img = frame[y:y+h, x:x+w]
        
        gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (9, 9), 2, 2)
        
        circles = cv2.HoughCircles(
            gray, cv2.HOUGH_GRADIENT, 1, 20,
            param1=circle_params['param1'],
            param2=circle_params['param2'],
            minRadius=circle_params['min_radius'],
            maxRadius=circle_params['max_radius']
        )
        
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                center = (i[0] + x, i[1] + y)
                radius = i[2]
                last_radius = radius
                
                mask = np.zeros_like(gray)
                cv2.circle(mask, (i[0], i[1]), radius, 255, -1)
                hsv_img = cv2.cvtColor(roi_img, cv2.COLOR_BGR2HSV)
                
                lower_red1 = np.array(color_thresholds['red']['lower1'])
                upper_red1 = np.array(color_thresholds['red']['upper1'])
                lower_red2 = np.array(color_thresholds['red']['lower2'])
                upper_red2 = np.array(color_thresholds['red']['upper2'])
                lower_green = np.array(color_thresholds['green']['lower'])
                upper_green = np.array(color_thresholds['green']['upper'])
                lower_blue = np.array(color_thresholds['blue']['lower'])
                upper_blue = np.array(color_thresholds['blue']['upper'])
                
                red_mask1 = cv2.inRange(hsv_img, lower_red1, upper_red1)
                red_mask2 = cv2.inRange(hsv_img, lower_red2, upper_red2)
                red_mask = cv2.bitwise_or(red_mask1, red_mask2)
                green_mask = cv2.inRange(hsv_img, lower_green, upper_green)
                blue_mask = cv2.inRange(hsv_img, lower_blue, upper_blue)
                
                red_mask = cv2.erode(red_mask, kernel, iterations=1)
                red_mask = cv2.dilate(red_mask, kernel, iterations=2)
                green_mask = cv2.erode(green_mask, kernel, iterations=2)
                green_mask = cv2.dilate(green_mask, kernel, iterations=6)
                blue_mask = cv2.erode(blue_mask, kernel, iterations=1)
                blue_mask = cv2.dilate(blue_mask, kernel, iterations=3)
                
                red_area = cv2.countNonZero(cv2.bitwise_and(red_mask, mask))
                green_area = cv2.countNonZero(cv2.bitwise_and(green_mask, mask))
                blue_area = cv2.countNonZero(cv2.bitwise_and(blue_mask, mask))
                
                max_area = max(red_area, green_area, blue_area)
                if max_area == red_area:
                    color_code = "1"
                elif max_area == green_area:
                    color_code = "2"
                else:
                    color_code = "3"
                
                last_color_code = color_code
                formatted_data = f"{center[0]:04}{center[1]:04}{color_code}{radius:01}"
                return formatted_data, center, color_code
        return None, None, None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("无法读取摄像头帧")
            break
        
        x, y, w, h = detection_area
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        current_time = cv2.getTickCount()
        data, current_center, current_color = detect_stacking_and_color(frame)
        
        if data and current_color:
            last_detection_time = current_time
            color_history.append(current_color)
            
            if first_center is None:
                first_center = current_center
                stable_count = 1
            else:
                distance = np.sqrt((current_center[0] - first_center[0])**2 + 
                                 (current_center[1] - first_center[1])**2)
                if distance < stability_settings['max_pixel_move']:
                    stable_count += 1
                else:
                    stable_count = 1
                    first_center = current_center
                    color_history = []
            
            if len(color_history) >= stability_settings['color_stable_threshold']:
                color_counter = defaultdict(int)
                for color in color_history:
                    color_counter[color] += 1
                
                most_common_color = max(color_counter.items(), key=lambda x: x[1])[0]
                confidence = color_counter[most_common_color] / len(color_history)
                
                if confidence >= stability_settings['color_confidence']:
                    final_color = most_common_color
                    print(f"颜色识别稳定: {most_common_color} (置信度: {confidence:.2f})")
            
            if (stable_count >= stability_settings['threshold'] and 
                final_color is not None):
                formatted_data = f"{current_center[0]:04}{current_center[1]:04}{final_color}{last_radius:01}"
                #send_data(formatted_data)
                print(f"检测转过来的第二个物块数据: {formatted_data}")
                C_2 = final_color
                break
        else:
            if last_detection_time is not None:
                elapsed_time = (current_time - last_detection_time) / cv2.getTickFrequency() * 1000
                if elapsed_time > timeout_settings['timeout_ms']:
                    print("检测超时，跳过本次识别")
                    continue
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cv2.destroyAllWindows()
    return C_2


def run_wukuaiyuanxin_xuanzequyu(i, yanse):  # 指定区域确认物块颜色
    global cap
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 50, 50])
    upper_red2 = np.array([180, 255, 255])
    lower_green = np.array([30, 40, 40])
    upper_green = np.array([89, 255, 255])
    lower_blue = np.array([90, 50, 50])
    upper_blue = np.array([140, 255, 255])
    
    kernel = np.ones((3, 3), np.uint8)
    
    if i == 1:
        roi_params_xuanze = (220, 70, 200, 140)   # 正下方A3
    elif i == 3:
        roi_params_xuanze = (160, 270, 300, 200)  # 左下角A1c
    elif i == 2:
        roi_params_xuanze = (160, 270, 300, 200) # 右下角A2
    elif i == 0:
        roi_params_xuanze = (210, 300, 220, 160) # 爪子识别区域
        
    def detect_stacking_and_color(frame, loop_radius=(25, 45), roi=roi_params_xuanze):
        roi_img = frame[roi[1]:roi[1] + roi[3], roi[0]:roi[0] + roi[2]]
        gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (9, 9), 2, 2)
        circles = cv2.HoughCircles(
            gray, 
            cv2.HOUGH_GRADIENT, 
            1, 
            20, 
            param1=25, 
            param2=25, 
            minRadius=loop_radius[0], 
            maxRadius=loop_radius[1]
        )

        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                center = (i[0] + roi[0], i[1] + roi[1])
                radius = i[2]

                mask = np.zeros_like(gray)
                cv2.circle(mask, (i[0], i[1]), radius, 255, -1)
                hsv_img = cv2.cvtColor(roi_img, cv2.COLOR_BGR2HSV)
                
                red_mask1 = cv2.inRange(hsv_img, lower_red1, upper_red1)
                red_mask2 = cv2.inRange(hsv_img, lower_red2, upper_red2)
                red_mask = red_mask1 + red_mask2
                green_mask = cv2.inRange(hsv_img, lower_green, upper_green)
                blue_mask = cv2.inRange(hsv_img, lower_blue, upper_blue)

                red_mask = cv2.erode(red_mask, kernel, iterations=1)
                red_mask = cv2.dilate(red_mask, kernel, iterations=2)
                green_mask = cv2.erode(green_mask, kernel, iterations=2)
                green_mask = cv2.dilate(green_mask, kernel, iterations=6)
                blue_mask = cv2.erode(blue_mask, kernel, iterations=1)
                blue_mask = cv2.dilate(blue_mask, kernel, iterations=3)

                red_area = cv2.countNonZero(cv2.bitwise_and(red_mask, mask))
                green_area = cv2.countNonZero(cv2.bitwise_and(green_mask, mask))
                blue_area = cv2.countNonZero(cv2.bitwise_and(blue_mask, mask))
                
                max_area = max(red_area, green_area, blue_area)
                if max_area == red_area:
                    color_code = "1"
                elif max_area == green_area:
                    color_code = "2"
                else:
                    color_code = "3"

                formatted_data = f"{center[0]:04}{center[1]:04}{color_code}{radius:01}"
                return formatted_data, center
        return None, None

    # 复用全流程唯一的 /dev/video2 句柄，避免与调度器重复打开。
    cap = ensure_video2_camera()
    if cap is None:
        print("摄像头初始化失败")
        return
        
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    stability_threshold = 30
    stable_count = 0
    last_center = None
    last_detection_time = None
    timeout_ms = 100

    while True:
        ret, frame = cap.read()
        if not ret:
            print("无法读取摄像头帧")
            break

        current_time = cv2.getTickCount()
        data, current_center = detect_stacking_and_color(frame)

        if data and data[8] == yanse:
            last_detection_time = current_time
            
            if last_center is not None:
                distance = np.sqrt((current_center[0] - last_center[0])**2 + 
                             (current_center[1] - last_center[1])**2)
                if distance < 10:
                    stable_count += 1
                else:
                    stable_count = 1
            else:
                stable_count = 1
            
            last_center = current_center
            
            if stable_count >= stability_threshold:
                send_data("987654321")
                print(f"判断物块颜色确实是{yanse}，稳定，发送的物块数据: 987654321")
                break
        else:
            if last_detection_time is not None:
                elapsed_time = (current_time - last_detection_time) / cv2.getTickFrequency() * 1000  # 毫秒
                if elapsed_time > timeout_ms:
                    print("检测超时，跳过本次识别")
                    continue
            
        # cv2.imshow("物块检测", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

def run_wukuaiyuanxin_A():  #初赛/决赛看三个物块的颜色
    global A1, A2, A3
    global cap
    
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 50, 50])
    upper_red2 = np.array([180, 255, 255])
    lower_green = np.array([35, 40, 40])
    upper_green = np.array([89, 255, 255])
    lower_blue = np.array([90, 60, 60])
    upper_blue = np.array([130, 255, 255])
    kernel = np.ones((3, 3), np.uint8)
    
    AREA_RATIO_THRESHOLD = 0.05

    def detect_color_only(frame, roi):
        try:
            roi_img = frame[roi[1]:roi[1]+roi[3], roi[0]:roi[0]+roi[2]]
            hsv_img = cv2.cvtColor(roi_img, cv2.COLOR_BGR2HSV)
            
            roi_area = roi_img.shape[0] * roi_img.shape[1]
            min_valid_area = roi_area * AREA_RATIO_THRESHOLD
            
            red_mask1 = cv2.inRange(hsv_img, lower_red1, upper_red1)
            red_mask2 = cv2.inRange(hsv_img, lower_red2, upper_red2)
            red_mask = cv2.bitwise_or(red_mask1, red_mask2)
            green_mask = cv2.inRange(hsv_img, lower_green, upper_green)
            blue_mask = cv2.inRange(hsv_img, lower_blue, upper_blue)

            red_mask = cv2.erode(red_mask, kernel, iterations=1)
            red_mask = cv2.dilate(red_mask, kernel, iterations=2)
            green_mask = cv2.erode(green_mask, kernel, iterations=2)
            green_mask = cv2.dilate(green_mask, kernel, iterations=5)
            blue_mask = cv2.erode(blue_mask, kernel, iterations=1)
            blue_mask = cv2.dilate(blue_mask, kernel, iterations=2)

            red_area = cv2.countNonZero(red_mask)
            green_area = cv2.countNonZero(green_mask)
            blue_area = cv2.countNonZero(blue_mask)
            
            max_area = max(red_area, green_area, blue_area)
            if max_area < min_valid_area:
                print(f"所有颜色区域面积不足(最大面积:{max_area}, 要求面积:{min_valid_area})")
                return None, None
            
            if red_area > green_area and red_area > blue_area and red_area >= min_valid_area:
                color_code = "1"
            elif green_area > red_area and green_area > blue_area and green_area >= min_valid_area:
                color_code = "2"
            elif blue_area > red_area and blue_area > green_area and blue_area >= min_valid_area:
                color_code = "3"
            else:
                print("没有检测到有效的颜色区域")
                return None, None

            formatted_data = f"00000000{color_code}00"
            return formatted_data, (0, 0)
        except Exception as e:
            print(f"检测过程中发生错误: {e}")
            return None, None

    def stable_detect(roi, single_timeout_ms=200):
        while True:
            start_time = cv2.getTickCount()
            detected = False
            
            while True:
                current_time = cv2.getTickCount()
                elapsed_time = (current_time - start_time) / cv2.getTickFrequency() * 1000
                
                if elapsed_time > single_timeout_ms:
                    print(f"单次检测超时 ({single_timeout_ms}ms)，重新开始检测")
                    break
                    
                ret, frame = cap.read()
                if not ret:
                    print("无法读取摄像头帧")
                    time.sleep(0.01)
                    continue
                    
                data, _ = detect_color_only(frame, roi)
                
                if data:
                    print(f"发送的物块数据: {data}")
                    print(f"本次检测时间为: {elapsed_time}ms")
                    elapsed_time=0
                    return data[8]
                    
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    raise KeyboardInterrupt("用户主动终止检测")
                
                time.sleep(0.01)

    if not cap.isOpened():
        print("摄像头初始化失败")
        return None, None, None
        
    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        A1 = stable_detect(roi_params1)
        time.sleep(0.1)
        A2 = stable_detect(roi_params2)
        
        if A1 == A2:
            print("两个区域颜色相同，重新检测...")
            time.sleep(0.2)
            A1 = stable_detect(roi_params1)
            time.sleep(0.1)
            A2 = stable_detect(roi_params2)
        
        all_colors = {'1', '2', '3'}
        detected_colors = {A1, A2}
        remaining_colors = all_colors - detected_colors
        A3 = remaining_colors.pop() if len(remaining_colors) == 1 else None
        
        print(f"最终检测结果 - A1: {A1}, A2: {A2}, A3: {A3}")
        return A1, A2, A3
        
    except KeyboardInterrupt:
        print("检测被用户中断")
        return None, None, None
    except Exception as e:
        print(f"主流程发生错误: {e}")
        return None, None, None
    finally:
        cv2.destroyAllWindows()
        
def main_logic_loop1():
    global C_1, C_2
    global INDEX
    global INDEX1
    global INDEX2
    #A1=run_wukuaiyuanxin_A1()
    #A2=run_wukuaiyuanxin_A2()
    #A3=run_wukuaiyuanxin_A3()
    A1,A2,A3=run_wukuaiyuanxin_A()
    print(f"快速扫描结果 - A1:{A1},A2: {A2}, A3: {A3}")
    is_clockwise = (A1 == C_1)
    B = [A3, A2, A1] if is_clockwise else [A3, A2, A1]
    B1 = [A2, A1, A3] if is_clockwise else [A1, A3, A2]
    B2 = [A1, A3, A2] if is_clockwise else [A2, A1, A3]
    for index,element in enumerate(B):
        if element ==A[0]:
            print(f"任务码的第一个数字在位置{index+1}")
            INDEX=index+1
    for index1,element1 in enumerate(B1):
        if element1 ==A[1]:
            print(f"任务码的第二个数字在位置{index1+1}")
            INDEX1=index1+1
    for index2,element2 in enumerate(B2):
        if element2 ==A[2]:
            print(f"任务码的第三个数字在位置{index2+1}")
            INDEX2=index2+1
    print(f"当前B数组: {B}，旋转方向:逆时针") if is_clockwise else print(f"当前B数组: {B}，旋转方向:顺时针")
    data=f"{INDEX}{INDEX1}{INDEX2}456789"
    send_data(data)
    print(f"已发送数据{INDEX}{INDEX1}{INDEX2}456789")

def LOOP1():
    global C_1,C_2
    C_2=run_wukuaiyuanxin_2()
    if C_1 != C_2:
        print("不相等，开始检测")
        main_logic_loop1()
    else:
        print("相等，开始循环")
        while True:
            C_2=run_wukuaiyuanxin_2()
            if C_2 is not None and C_2 != C_1:
                print("不相等，开始检测")
                main_logic_loop1()
                break
            time.sleep(0.1)

def main_logic_loop2():
    global C_1_loop2, C_2_loop2
    global INDEX_loop2
    global INDEX1_loop2
    global INDEX2_loop2
    #A1=run_wukuaiyuanxin_A1()
    #A2=run_wukuaiyuanxin_A2()
    #A3=run_wukuaiyuanxin_A3()
    A1,A2,A3=run_wukuaiyuanxin_A()
    print(f"快速扫描结果 - A1:{A1},A2: {A2}, A3: {A3}")
    is_clockwise = (A1 == C_1_loop2)
    B = [A3, A2, A1] if is_clockwise else [A3, A2, A1]
    B1 = [A2, A1, A3] if is_clockwise else [A1, A3, A2]
    B2 = [A1, A3, A2] if is_clockwise else [A2, A1, A3]
    for index,element in enumerate(B):
        if element ==A[4]:
            print(f"任务码的第一个数字在位置{index+1}")
            INDEX_loop2=index+1
    for index1,element1 in enumerate(B1):
        if element1 ==A[5]:
            print(f"任务码的第二个数字在位置{index1+1}")
            INDEX1_loop2=index1+1
    for index2,element2 in enumerate(B2):
        if element2 ==A[6]:
            print(f"任务码的第三个数字在位置{index2+1}")
            INDEX2_loop2=index2+1
    print(f"当前B数组: {B}，旋转方向:逆时针") if is_clockwise else print(f"当前B数组: {B}，旋转方向:顺时针")
    data=f"{INDEX_loop2}{INDEX1_loop2}{INDEX2_loop2}456789"
    send_data(data)
    print(f"已发送数据{INDEX_loop2}{INDEX1_loop2}{INDEX2_loop2}456789")

def LOOP2():
    global C_1_loop2,C_2_loop2
    C_2_loop2=run_wukuaiyuanxin_2()
    if C_1_loop2 != C_2_loop2:
        print("不相等，开始检测")
        main_logic_loop2()
    else:
        print("相等，开始循环")
        while True:
            C_2_loop2=run_wukuaiyuanxin_2()
            if C_2_loop2 is not None and C_2_loop2 != C_1_loop2:
                print("不相等，开始检测")
                main_logic_loop2()
                break
            time.sleep(0.1)

def detect_boundary_line():
    global cap2
    if not cap2.isOpened():
        print("无法打开摄像头")
        return
    
    cap2.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap2.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    canny_threshold1 = 50
    canny_threshold2 = 150
    hough_threshold = 20
    min_line_length = 140
    max_line_gap = 10
    roi_top = 0.1    # ROI区域顶部边界
    roi_bottom = 0.9  # ROI区域底部边界
    roi_left = 0.1    # ROI区域左侧边界
    roi_right = 0.9   # ROI区域右侧边界
    variance_threshold = 1.0  # 方差容忍阈值(角度平方)
    max_attempts = 10  # 最大尝试次数
    
    attempt_count = 0
    while attempt_count < max_attempts:
        angle_results = []  # 存储三次有效检测的结果
        
        while len(angle_results) < 3:
            ret, frame = cap2.read()
            if not ret:
                print("无法读取帧")
                continue
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape
            roi = gray[int(height*roi_top):int(height*roi_bottom), 
                      int(width*roi_left):int(width*roi_right)]
            blurred = cv2.GaussianBlur(roi, (5, 5), 0)
            edges = cv2.Canny(blurred, canny_threshold1, canny_threshold2)
            
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=hough_threshold,
                                  minLineLength=min_line_length, maxLineGap=max_line_gap)
            
            if lines is not None:
                angles = []
                weights = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = np.arctan2(y2 - y1, x2 - x1)
                    angles.append(angle)
                    weights.append(np.sqrt((x2-x1)**2 + (y2-y1)**2))  # 线段长度作为权重
                
                if angles:
                    total_weight = sum(weights)
                    avg_angle_rad = sum(a*w for a, w in zip(angles, weights)) / total_weight
                    avg_angle_deg = np.degrees(avg_angle_rad)
                    angle_results.append(avg_angle_deg)
                    print(f"第 {len(angle_results)} 次有效检测 - 角度: {avg_angle_deg:.2f}°")
            
            time.sleep(0.05)
        
        if len(angle_results) == 3:
            variance = np.var(angle_results)
            print(f"本次检测方差: {variance:.2f} (阈值: {variance_threshold})")
            
            if variance <= variance_threshold:
                final_angle = round(np.mean(angle_results), 1) - 2.0  # 减去0.7度校准值
                final_angle = max(-9.9, min(9.9, final_angle))
                
                sign = 1 if final_angle >= 0 else 0
                abs_angle = abs(final_angle)
                integer_part = int(abs_angle)
                decimal_part = int(round(abs_angle * 10)) % 10
                data_str = f"000000{sign}{integer_part}{decimal_part}"
                #data_str = f"000000000"
                send_data(data_str)
                print(f"角度稳定，发送数据: {data_str}，平均角度: {final_angle}°")
                return
            else:
                print("角度波动过大，重新检测...")
                attempt_count += 1
        else:
            print("未能收集到3次有效检测，重新尝试...")
            attempt_count += 1
    
    send_data("000000004")  # 发送全零数据表示检测失败
    print("达到最大尝试次数仍未获得稳定角度，发送默认数据")

def run_sehuanyuanxin2():  # 初赛放物块的时候，色环第一次定标的程序（地上的圆形）
    global cap2
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 50, 50])
    upper_red2 = np.array([180, 255, 255])
    lower_green = np.array([30, 40, 40])
    upper_green = np.array([89, 255, 255])
    lower_blue = np.array([90, 50, 90])
    upper_blue = np.array([140, 255, 255])
    kernel = np.ones((3, 3), np.uint8)

    center_x, center_y = 320, 240
    square_side = 433
    square_side1 = 222
    square_side2 = 240
    half_side = square_side // 2
    half_side1 = square_side1 // 2
    half_side2 = square_side2 // 2

    if not cap2.isOpened():
        print("无法读取摄像头帧")
        return
    _configure_calibration_camera(cap2, 640, 480)

    POSITION_STABLE_THRESHOLD = 10   # 位置稳定阈值(像素)
    COLOR_STABLE_THRESHOLD = 5       # 颜色稳定所需出现次数（非连续）
    COLOR_CONFIDENCE = 0.5           # 颜色置信度要求
    FRAME_WINDOW_SIZE = 15           # 检测窗口大小
    TIMEOUT_MS = 200                 # 单次检测超时(毫秒)
    TOTAL_TIMEOUT = 8.0              # 总超时时间(秒)

    start_time = time.time()
    last_detection_time = None
    frame_count = 0
    
    color_stats = {
        "1": {"count": 0, "positions": []},
        "2": {"count": 0, "positions": []}, 
        "3": {"count": 0, "positions": []}
    }
    confirmed_color = None
    confirmed_position = None
    
    position_history = []
    position_stable_count = 0

    while True:
        ret, frame = cap2.read()
        if not ret:
            print("无法读取摄像头帧")
            break

        current_time = cv2.getTickCount()
        frame_count += 1
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        filtered_img = cv2.GaussianBlur(gray, (3, 3), 0)
        circles = cv2.HoughCircles(filtered_img,
                                cv2.HOUGH_GRADIENT, dp=1, minDist=30,
                                param1=50, param2=30,
                                minRadius=35, maxRadius=38)

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)

        red_mask = cv2.erode(red_mask, kernel, iterations=1)
        red_mask = cv2.dilate(red_mask, kernel, iterations=2)
        green_mask = cv2.erode(green_mask, kernel, iterations=2)
        green_mask = cv2.dilate(green_mask, kernel, iterations=6)
        blue_mask = cv2.erode(blue_mask, kernel, iterations=1)
        blue_mask = cv2.dilate(blue_mask, kernel, iterations=3)

        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            for (x, y, r) in circles:
                if not (center_x - half_side <= x <= center_x + half_side and
                        center_y - half_side1 <= y <= center_y + half_side2):
                    continue

                x = np.clip(x, 0, frame.shape[1] - 1)
                y = np.clip(y, 0, frame.shape[0] - 1)

                mask = np.zeros_like(gray)
                cv2.circle(mask, (x, y), int(1.4 * r), 255, -1)

                red_area = cv2.countNonZero(cv2.bitwise_and(red_mask, mask))
                green_area = cv2.countNonZero(cv2.bitwise_and(green_mask, mask))
                blue_area = cv2.countNonZero(cv2.bitwise_and(blue_mask, mask))

                max_area = max(red_area, green_area, blue_area)
                if max_area == 0:
                    continue
                
                if max_area == red_area:
                    current_color = "1"
                elif max_area == green_area:
                    current_color = "2"
                else:
                    current_color = "3"
                
                last_detection_time = current_time
                
                color_stats[current_color]["count"] += 1
                color_stats[current_color]["positions"].append((x, y))
                if len(color_stats[current_color]["positions"]) > FRAME_WINDOW_SIZE:
                    color_stats[current_color]["positions"].pop(0)
                
                masked = cv2.bitwise_and(hsv, hsv, mask=mask)
                avg_hsv = cv2.mean(masked, mask=mask)[:3]
                print(f"帧 {frame_count}: 检测到颜色 {current_color}，坐标 ({x}, {y})，HSV: H={avg_hsv[0]:.1f}, S={avg_hsv[1]:.1f}, V={avg_hsv[2]:.1f}")
                
                for color in ["1", "2", "3"]:
                    if (color_stats[color]["count"] >= COLOR_STABLE_THRESHOLD and
                        len(color_stats[color]["positions"]) >= 3 and
                        color_stats[color]["count"]/frame_count >= COLOR_CONFIDENCE):
                        
                        avg_x = int(np.mean([p[0] for p in color_stats[color]["positions"]]))
                        avg_y = int(np.mean([p[1] for p in color_stats[color]["positions"]]))
                        
                        confirmed_color = color
                        confirmed_position = (avg_x, avg_y)
                        print(f"颜色 {color} 已达到稳定条件，平均坐标 ({avg_x}, {avg_y})")
                        break
                
                if confirmed_color is not None:
                    current_pos = (x, y) if current_color == confirmed_color else confirmed_position
                    position_history.append(current_pos)
                    
                    if len(position_history) > 5:
                        position_history.pop(0)
                    
                    if len(position_history) >= 3:
                        distances = [
                            np.sqrt((position_history[i][0]-position_history[i-1][0])**2 + 
                                   (position_history[i][1]-position_history[i-1][1])**2)
                            for i in range(1, len(position_history))
                        ]
                        
                        if all(d < POSITION_STABLE_THRESHOLD for d in distances):
                            position_stable_count += 1
                        else:
                            position_stable_count = max(0, position_stable_count - 1)
                
                if (confirmed_color is not None and 
                    position_stable_count >= 3):
                    
                    formatted_data = f"{confirmed_position[0]:04}{confirmed_position[1]:04}{confirmed_color}"
                    send_data(formatted_data)
                    print(f"最终结果: 颜色 {confirmed_color} 稳定坐标 {confirmed_position}")
                    return confirmed_color
                
                break  # 只处理第一个检测到的圆形
        else:
            if last_detection_time is not None:
                elapsed_time = (current_time - last_detection_time) / cv2.getTickFrequency() * 1000
                if elapsed_time > TIMEOUT_MS:
                    print(f"帧 {frame_count}: 检测超时，跳过本次识别")
                    continue
            
        if time.time() - start_time > TOTAL_TIMEOUT:
            if confirmed_color is not None:
                avg_x = int(np.mean([p[0] for p in color_stats[confirmed_color]["positions"]]))
                avg_y = int(np.mean([p[1] for p in color_stats[confirmed_color]["positions"]]))
                formatted_data = f"{avg_x:04}{avg_y:04}{confirmed_color}"
                send_data(formatted_data)
                print(f"超时结果: 颜色 {confirmed_color} 坐标 ({avg_x}, {avg_y})")
                return confirmed_color
            else:
                best_color = max(color_stats.items(), key=lambda x: x[1]["count"])[0]
                if color_stats[best_color]["count"] > 0:
                    avg_x = int(np.mean([p[0] for p in color_stats[best_color]["positions"]]))
                    avg_y = int(np.mean([p[1] for p in color_stats[best_color]["positions"]]))
                    formatted_data = f"{avg_x:04}{avg_y:04}{best_color}"
                    send_data(formatted_data)
                    print(f"超时备用结果: 颜色 {best_color} 坐标 ({avg_x}, {avg_y})")
                    return best_color
                else:
                    send_data("000000004")
                    print("检测超时，发送默认信号")
                    return "4"
        
        time.sleep(0.02)

SEHUAN_TIMEOUT = 8.0
SEHUAN_NO_DET_MS = 300
SEHUAN_MIN_R = 150
SEHUAN_MAX_R = 180
SEHUAN_SCALE = 0.5
SEHUAN_ROI_GUARD = 16
SEHUAN_R_TOL = 12
SEHUAN_C_TOL = 24
SEHUAN_REFINE_GUARD = 10
SEHUAN_MIN_X = 710
SEHUAN_MAX_X = 1210
SEHUAN_MIN_Y = 290
SEHUAN_MAX_Y = 790
SEHUAN_STABLE = 3
SEHUAN_COLOR_STABLE = 3
SEHUAN_COLOR_CONF = 0.7
SEHUAN_MAX_MOVE = 10

SEHUAN_KERNEL = np.ones((3, 3), np.uint8)
SEHUAN_LOW_R1 = np.array([0, 50, 50])
SEHUAN_UP_R1 = np.array([10, 255, 255])
SEHUAN_LOW_R2 = np.array([160, 50, 50])
SEHUAN_UP_R2 = np.array([180, 255, 255])
SEHUAN_LOW_G = np.array([30, 40, 40])
SEHUAN_UP_G = np.array([89, 255, 255])
SEHUAN_LOW_B = np.array([90, 50, 90])
SEHUAN_UP_B = np.array([140, 255, 255])

def _sehuanyuanxin_roi(frame):
    height, width = frame.shape[:2]
    x0 = max(
        0,
        SEHUAN_MIN_X - SEHUAN_MAX_R - SEHUAN_ROI_GUARD,
    )
    y0 = max(
        0,
        SEHUAN_MIN_Y - SEHUAN_MAX_R - SEHUAN_ROI_GUARD,
    )
    x1 = min(
        width,
        SEHUAN_MAX_X + SEHUAN_MAX_R + SEHUAN_ROI_GUARD + 1,
    )
    y1 = min(
        height,
        SEHUAN_MAX_Y + SEHUAN_MAX_R + SEHUAN_ROI_GUARD + 1,
    )
    if x0 >= x1 or y0 >= y1:
        raise ValueError("色环精细定标ROI无效")
    return x0, y0, x1, y1


def _sehuanyuanxin_center_ok(circle_x, circle_y):
    return (
        SEHUAN_MIN_X <= circle_x <= SEHUAN_MAX_X
        and SEHUAN_MIN_Y <= circle_y <= SEHUAN_MAX_Y
    )


def _sehuanyuanxin_jingxiu(frame, coarse_circle):
    coarse_x, coarse_y, coarse_radius = coarse_circle
    min_radius = max(SEHUAN_MIN_R, coarse_radius - SEHUAN_R_TOL)
    max_radius = min(SEHUAN_MAX_R, coarse_radius + SEHUAN_R_TOL)
    if min_radius >= max_radius:
        return None
    height, width = frame.shape[:2]
    extent = max_radius + SEHUAN_C_TOL + SEHUAN_REFINE_GUARD
    x0 = max(0, coarse_x - extent)
    y0 = max(0, coarse_y - extent)
    x1 = min(width, coarse_x + extent + 1)
    y1 = min(height, coarse_y + extent + 1)
    patch = frame[y0:y1, x0:x1]
    if patch.size == 0:
        return None
    gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
    filtered = cv2.GaussianBlur(gray, (3, 3), 0)
    detected = cv2.HoughCircles(
        filtered,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=30,
        param1=50,
        param2=20,
        minRadius=min_radius,
        maxRadius=max_radius,
    )
    if detected is None:
        return None
    best_circle = None
    best_score = float('inf')
    for local_x, local_y, radius in np.round(detected[0, :]).astype('int'):
        global_x = int(local_x) + x0
        global_y = int(local_y) + y0
        radius = int(radius)
        center_error = float(np.hypot(global_x - coarse_x, global_y - coarse_y))
        if center_error > SEHUAN_C_TOL:
            continue
        if not _sehuanyuanxin_center_ok(global_x, global_y):
            continue
        score = center_error + 0.5 * abs(radius - coarse_radius)
        if score < best_score:
            best_score = score
            best_circle = (global_x, global_y, radius)
    return best_circle


def _sehuanyuanxin_detect(frame):
    x0, y0, x1, y1 = _sehuanyuanxin_roi(frame)
    source = frame[y0:y1, x0:x1]
    work = cv2.resize(
        source,
        None,
        fx=SEHUAN_SCALE,
        fy=SEHUAN_SCALE,
        interpolation=cv2.INTER_AREA,
    )
    gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
    filtered = cv2.GaussianBlur(gray, (3, 3), 0)
    detected = cv2.HoughCircles(
        filtered,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=max(1, int(round(30 * SEHUAN_SCALE))),
        param1=50,
        param2=20,
        minRadius=int(round(SEHUAN_MIN_R * SEHUAN_SCALE)),
        maxRadius=int(round(SEHUAN_MAX_R * SEHUAN_SCALE)),
    )
    if detected is None:
        return []
    confirmed = []
    for local_x, local_y, local_radius in np.round(detected[0, :]).astype('int'):
        global_x = int(round(local_x / SEHUAN_SCALE)) + x0
        global_y = int(round(local_y / SEHUAN_SCALE)) + y0
        radius = int(round(local_radius / SEHUAN_SCALE))
        if not _sehuanyuanxin_center_ok(global_x, global_y):
            continue
        refined = _sehuanyuanxin_jingxiu(frame, (global_x, global_y, radius))
        if refined is None:
            continue
        score = float(np.hypot(refined[0] - global_x, refined[1] - global_y)) + 0.5 * abs(refined[2] - radius)
        confirmed.append((score, refined))
    if not confirmed:
        return []
    confirmed.sort(key=lambda item: item[0])
    return [confirmed[0][1]]


def _sehuanyuanxin_yanse_mask(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    red_mask = cv2.bitwise_or(
        cv2.inRange(hsv, SEHUAN_LOW_R1, SEHUAN_UP_R1),
        cv2.inRange(hsv, SEHUAN_LOW_R2, SEHUAN_UP_R2),
    )
    green_mask = cv2.inRange(hsv, SEHUAN_LOW_G, SEHUAN_UP_G)
    blue_mask = cv2.inRange(hsv, SEHUAN_LOW_B, SEHUAN_UP_B)
    red_mask = cv2.dilate(
        cv2.erode(red_mask, SEHUAN_KERNEL, iterations=1),
        SEHUAN_KERNEL,
        iterations=2,
    )
    green_mask = cv2.dilate(
        cv2.erode(green_mask, SEHUAN_KERNEL, iterations=2),
        SEHUAN_KERNEL,
        iterations=6,
    )
    blue_mask = cv2.dilate(
        cv2.erode(blue_mask, SEHUAN_KERNEL, iterations=1),
        SEHUAN_KERNEL,
        iterations=3,
    )
    return hsv, (red_mask, green_mask, blue_mask)


def _sehuanyuanxin_yanse(frame, circle_x, circle_y, radius):
    height, width = frame.shape[:2]
    mask_radius = int(1.4 * radius)
    extent = mask_radius + 10
    x0 = max(0, int(circle_x) - extent)
    y0 = max(0, int(circle_y) - extent)
    x1 = min(width, int(circle_x) + extent + 1)
    y1 = min(height, int(circle_y) + extent + 1)
    if x0 >= x1 or y0 >= y1:
        return None

    patch = frame[y0:y1, x0:x1]
    hsv, masks = _sehuanyuanxin_yanse_mask(patch)
    local_x = int(circle_x) - x0
    local_y = int(circle_y) - y0
    circle_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    cv2.circle(circle_mask, (local_x, local_y), mask_radius, 255, -1)
    areas = tuple(
        cv2.countNonZero(cv2.bitwise_and(color_mask, circle_mask))
        for color_mask in masks
    )
    max_area = max(areas)
    if max_area == 0:
        return None
    color_index = areas.index(max_area)
    selected_mask = cv2.bitwise_and(masks[color_index], circle_mask)
    masked_hsv = cv2.bitwise_and(hsv, hsv, mask=selected_mask)
    average_hsv = cv2.mean(masked_hsv, mask=selected_mask)[:3]
    if average_hsv[0] == 0 and average_hsv[1] == 0 and average_hsv[2] == 0:
        return None
    return str(color_index + 1), average_hsv, areas


def run_sehuanyuanxin2_centered():  # 色环第二次精细定标
    global cap2
    start_time = time.time()
    last_detection_time = None
    timeout_ms = 300
    stable_count = 0
    first_center = None
    color_history = []
    final_color = None

    if cap2 is None or not cap2.isOpened():
        print('无法读取摄像头帧')
        send_data('000000004')
        return
    _configure_calibration_camera(cap2, 1920, 1080)

    while True:
        if time.time() - start_time > SEHUAN_TIMEOUT:
            send_data('000000004')
            print('检测超时，发送默认信号')
            return
        ret, frame = cap2.read()
        if not ret or frame is None:
            print('无法读取摄像头帧')
            send_data('000000004')
            return
        current_time = cv2.getTickCount()
        circles = _sehuanyuanxin_detect(frame)
        if not circles:
            if last_detection_time is not None:
                elapsed_ms = (current_time - last_detection_time) / cv2.getTickFrequency() * 1000
                if elapsed_ms > SEHUAN_NO_DET_MS:
                    print('检测超时，跳过本次识别')
            continue
        circle_x, circle_y, radius = circles[0]
        classified = _sehuanyuanxin_yanse(frame, circle_x, circle_y, radius)
        if classified is None:
            print('检测到无效颜色区域（HSV全为0），跳过...')
            continue
        current_color, average_hsv, _ = classified
        last_detection_time = current_time
        current_center = (circle_x, circle_y)
        print(f'检测到颜色 {current_color}，HSV值: H={average_hsv[0]:.1f}, S={average_hsv[1]:.1f}, V={average_hsv[2]:.1f}')
        color_history.append(current_color)
        if first_center is None:
            first_center = current_center
            stable_count = 1
        else:
            distance = np.hypot(current_center[0] - first_center[0], current_center[1] - first_center[1])
            if distance < SEHUAN_MAX_MOVE:
                stable_count += 1
            else:
                stable_count = 1
                first_center = current_center
                color_history = []
        if len(color_history) >= SEHUAN_COLOR_STABLE:
            color_counts = defaultdict(int)
            for historical_color in color_history:
                color_counts[historical_color] += 1
            most_common_color = max(color_counts.items(), key=lambda item: item[1])[0]
            confidence = color_counts[most_common_color] / len(color_history)
            if confidence >= SEHUAN_COLOR_CONF:
                final_color = most_common_color
                print(f'颜色识别稳定: {final_color} (置信度: {confidence:.2f})')
        if stable_count >= SEHUAN_STABLE and final_color is not None:
            formatted_data = f'{current_center[0]:04}{current_center[1]:04}{final_color}'
            send_data(formatted_data)
            print(f'稳定坐标发送: {formatted_data}')
            return


def _sangeyuanxin_shengcheng_yanse_yanmo(image):
    if image is None or image.size == 0:
        return None
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    kernel = np.ones((3, 3), np.uint8)
    red = cv2.bitwise_or(
        cv2.inRange(hsv, np.array([0, 50, 50]), np.array([10, 255, 255])),
        cv2.inRange(hsv, np.array([160, 50, 50]), np.array([180, 255, 255])),
    )
    green = cv2.inRange(hsv, np.array([30, 40, 40]), np.array([89, 255, 255]))
    blue = cv2.inRange(hsv, np.array([90, 50, 50]), np.array([140, 255, 255]))
    red = cv2.dilate(cv2.erode(red, kernel, iterations=1), kernel, iterations=2)
    green = cv2.dilate(cv2.erode(green, kernel, iterations=2), kernel, iterations=5)
    blue = cv2.dilate(cv2.erode(blue, kernel, iterations=1), kernel, iterations=2)
    return hsv, {"1": red, "2": green, "3": blue}


def _sangeyuanxin_xuanze_yanse(areas, minimum_area):
    ranked = sorted(areas.items(), key=lambda item: item[1], reverse=True)
    if not ranked or ranked[0][1] < minimum_area:
        return None
    second_area = ranked[1][1] if len(ranked) > 1 else 0
    if second_area > 0 and ranked[0][1] < second_area * SANGEYUANXIN_COLOR_DOMINANCE_RATIO:
        return None
    return ranked[0][0]


def _sangeyuanxin_shibie_roi_yanse(frame, roi):
    if frame is None or frame.size == 0:
        return None
    height, width = frame.shape[:2]
    x, y, roi_width, roi_height = (int(value) for value in roi)
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(width, x + roi_width), min(height, y + roi_height)
    if x0 >= x1 or y0 >= y1:
        return None
    patch = frame[y0:y1, x0:x1]
    context = _sangeyuanxin_shengcheng_yanse_yanmo(patch)
    if context is None:
        return None
    hsv, masks = context
    areas = {color: cv2.countNonZero(mask) for color, mask in masks.items()}
    minimum_area = patch.shape[0] * patch.shape[1] * SANGEYUANXIN_COLOR_MIN_AREA_RATIO
    color = _sangeyuanxin_xuanze_yanse(areas, minimum_area)
    if color is None:
        return None
    average_hsv = cv2.mean(hsv, mask=masks[color])[:3]
    return color, areas, average_hsv


def _sangeyuanxin_shengcheng_jiaqu_baowen(q_colors, task_colors):
    q_yanse = tuple(str(color) for color in q_colors)
    renwu_yanse = tuple(str(color) for color in task_colors)
    if len(q_yanse) != 3 or set(q_yanse) != {"1", "2", "3"}:
        return None
    if (renwu_yanse is None or len(renwu_yanse) != 3 or
            set(renwu_yanse) != {"1", "2", "3"}):
        return None
    yanse_dao_q = {color: str(index + 1) for index, color in enumerate(q_yanse)}
    jiaqu_shunxu = "".join(yanse_dao_q[color] for color in renwu_yanse)
    return jiaqu_shunxu + "456789"


def _sangeyuanxin_chongzhi_lunci():
    global sangeyuanxin_dangqian_lunci
    sangeyuanxin_dangqian_lunci = 0
    print("[SANGEYUANXIN_Q] 新二维码已生效，固定物料区轮次重置为第1轮")


def _sangeyuanxin_huoqu_renwu_yanse(erweima_shuju, lunci):
    if lunci == 0:
        qishi, jieshu = 0, 3
    elif lunci == 1:
        qishi, jieshu = 4, 7
    else:
        return None
    if erweima_shuju is None or len(erweima_shuju) < jieshu:
        return None
    return tuple(str(color) for color in erweima_shuju[qishi:jieshu])


def _sangeyuanxin_tuijin_lunci():
    global sangeyuanxin_dangqian_lunci
    if sangeyuanxin_dangqian_lunci < SANGEYUANXIN_ZONG_LUNCI:
        sangeyuanxin_dangqian_lunci += 1
    return sangeyuanxin_dangqian_lunci


def yunxing_sangeyuanxin_shibie_q123():  # 固定物料区Q1/Q2/Q3识别
    global cap, cap2, A, sangeyuanxin_dangqian_lunci

    if sangeyuanxin_dangqian_lunci >= SANGEYUANXIN_ZONG_LUNCI:
        print("[SANGEYUANXIN_Q] 固定物料区两轮均已完成，拒绝重复执行任务 i")
        send_data("000000004")
        return None

    dangqian_lunci = sangeyuanxin_dangqian_lunci
    lunci_xianshi = dangqian_lunci + 1
    renwu_biaoqian = "A1/A2/A3" if dangqian_lunci == 0 else "A4/A5/A6"
    renwu_yanse = _sangeyuanxin_huoqu_renwu_yanse(A, dangqian_lunci)
    print(
        f"[SANGEYUANXIN_Q] 开始第{lunci_xianshi}轮，"
        f"使用{renwu_biaoqian}: {renwu_yanse}"
    )
    if len(renwu_yanse) != 3 or set(renwu_yanse) != {"1", "2", "3"}:
        print(
            f"[SANGEYUANXIN_Q] 第{lunci_xianshi}轮二维码任务无效 "
            f"({renwu_biaoqian}): {renwu_yanse}"
        )
        send_data("000000004")
        return None

    camera = ensure_video2_camera()
    if camera is None:
        send_data("000000004")
        return None
    cap = camera
    cap2 = camera
    _configure_calibration_camera(camera, 640, 480)
    rois = (
        ("Q1", SANGEYUANXIN_Q1_ROI),
        ("Q2", SANGEYUANXIN_Q2_ROI),
        ("Q3", SANGEYUANXIN_Q3_ROI),
    )
    started = time.perf_counter()
    last_colors = None
    stable_count = 0

    while time.perf_counter() - started <= SANGEYUANXIN_TOTAL_TIMEOUT:
        ret, frame = camera.read()
        if not ret or frame is None:
            print("[SANGEYUANXIN_Q] 无法读取摄像头帧")
            send_data("000000004")
            return None
        results = [_sangeyuanxin_shibie_roi_yanse(frame, roi) for _, roi in rois]
        if any(result is None for result in results):
            stable_count = 0
            last_colors = None
            print("[SANGEYUANXIN_Q] 存在无效区域，继续检测")
            continue
        colors = tuple(result[0] for result in results)
        payload = _sangeyuanxin_shengcheng_jiaqu_baowen(colors, renwu_yanse)
        areas_text = " ".join(
            f"{name}={color}:{result[1]}"
            for (name, _), color, result in zip(rois, colors, results)
        )
        if payload is None:
            stable_count = 0
            last_colors = None
            print(f"[SANGEYUANXIN_Q] 三色不唯一 colors={colors} {areas_text}")
            continue
        if colors == last_colors:
            stable_count += 1
        else:
            last_colors = colors
            stable_count = 1
        print(
            f"[SANGEYUANXIN_Q] colors={colors} stable="
            f"{stable_count}/{SANGEYUANXIN_REGION_STABLE_FRAMES} {areas_text}"
        )
        if stable_count < SANGEYUANXIN_REGION_STABLE_FRAMES:
            continue
        mapping = {name: color for (name, _), color in zip(rois, colors)}
        send_data(payload)
        xiayi_lunci = _sangeyuanxin_tuijin_lunci()
        lunci_zhuangtai = (
            "两轮已完成"
            if xiayi_lunci >= SANGEYUANXIN_ZONG_LUNCI
            else f"等待第{xiayi_lunci + 1}轮 h/i"
        )
        print(
            f"[SANGEYUANXIN_Q] result=success round={lunci_xianshi} "
            f"source={renwu_biaoqian} mapping={mapping} task={renwu_yanse} "
            f"pickup_q={payload[:3]} payload={payload} next={lunci_zhuangtai}"
        )
        return mapping

    print("[SANGEYUANXIN_Q] 检测超时")
    send_data("000000004")
    return None


def run_maduoyuanxin2():  # 初赛放物块的时候，色环第一次定标的程序（地上的圆形）
    global cap2
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 50, 50])
    upper_red2 = np.array([180, 255, 255])
    lower_green = np.array([30, 40, 40])
    upper_green = np.array([89, 255, 255])
    lower_blue = np.array([90, 50, 90])
    upper_blue = np.array([140, 255, 255])
    kernel = np.ones((3, 3), np.uint8)

    center_x, center_y = 305, 240
    square_side = 210
    square_side1 = 200
    square_side2 = 260
    half_side = square_side // 2
    half_side1 = square_side1 // 2
    half_side2 = square_side2 // 2

    if not cap2.isOpened():
        print("无法读取摄像头帧")
        return
    _configure_calibration_camera(cap2, 640, 480)

    POSITION_STABLE_THRESHOLD = 10   # 位置稳定阈值(像素)
    COLOR_STABLE_THRESHOLD = 5       # 颜色稳定所需出现次数（非连续）
    COLOR_CONFIDENCE = 0.5           # 颜色置信度要求
    FRAME_WINDOW_SIZE = 15           # 检测窗口大小
    TIMEOUT_MS = 200                 # 单次检测超时(毫秒)
    TOTAL_TIMEOUT = 8.0              # 总超时时间(秒)

    start_time = time.time()
    last_detection_time = None
    frame_count = 0
    
    color_stats = {
        "1": {"count": 0, "positions": []},
        "2": {"count": 0, "positions": []}, 
        "3": {"count": 0, "positions": []}
    }
    confirmed_color = None
    confirmed_position = None
    
    position_history = []
    position_stable_count = 0

    while True:
        ret, frame = cap2.read()
        if not ret:
            print("无法读取摄像头帧")
            break

        current_time = cv2.getTickCount()
        frame_count += 1
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        filtered_img = cv2.GaussianBlur(gray, (3, 3), 0)
        circles = cv2.HoughCircles(filtered_img,
                                cv2.HOUGH_GRADIENT, dp=1, minDist=30,
                                param1=50, param2=30,
                                minRadius=20, maxRadius=27)

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)

        red_mask = cv2.erode(red_mask, kernel, iterations=1)
        red_mask = cv2.dilate(red_mask, kernel, iterations=2)
        green_mask = cv2.erode(green_mask, kernel, iterations=2)
        green_mask = cv2.dilate(green_mask, kernel, iterations=6)
        blue_mask = cv2.erode(blue_mask, kernel, iterations=1)
        blue_mask = cv2.dilate(blue_mask, kernel, iterations=3)

        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            for (x, y, r) in circles:
                if not (center_x - half_side <= x <= center_x + half_side and
                        center_y - half_side1 <= y <= center_y + half_side2):
                    continue

                x = np.clip(x, 0, frame.shape[1] - 1)
                y = np.clip(y, 0, frame.shape[0] - 1)

                mask = np.zeros_like(gray)
                cv2.circle(mask, (x, y), int(1.4 * r), 255, -1)

                red_area = cv2.countNonZero(cv2.bitwise_and(red_mask, mask))
                green_area = cv2.countNonZero(cv2.bitwise_and(green_mask, mask))
                blue_area = cv2.countNonZero(cv2.bitwise_and(blue_mask, mask))

                max_area = max(red_area, green_area, blue_area)
                if max_area == 0:
                    continue
                
                if max_area == red_area:
                    current_color = "1"
                elif max_area == green_area:
                    current_color = "2"
                else:
                    current_color = "3"
                
                last_detection_time = current_time
                
                color_stats[current_color]["count"] += 1
                color_stats[current_color]["positions"].append((x, y))
                if len(color_stats[current_color]["positions"]) > FRAME_WINDOW_SIZE:
                    color_stats[current_color]["positions"].pop(0)
                
                masked = cv2.bitwise_and(hsv, hsv, mask=mask)
                avg_hsv = cv2.mean(masked, mask=mask)[:3]
                print(f"帧 {frame_count}: 检测到颜色 {current_color}，坐标 ({x}, {y})，HSV: H={avg_hsv[0]:.1f}, S={avg_hsv[1]:.1f}, V={avg_hsv[2]:.1f}")
                
                for color in ["1", "2", "3"]:
                    if (color_stats[color]["count"] >= COLOR_STABLE_THRESHOLD and
                        len(color_stats[color]["positions"]) >= 3 and
                        color_stats[color]["count"]/frame_count >= COLOR_CONFIDENCE):
                        
                        avg_x = int(np.mean([p[0] for p in color_stats[color]["positions"]]))
                        avg_y = int(np.mean([p[1] for p in color_stats[color]["positions"]]))
                        
                        confirmed_color = color
                        confirmed_position = (avg_x, avg_y)
                        print(f"颜色 {color} 已达到稳定条件，平均坐标 ({avg_x}, {avg_y})")
                        break
                
                if confirmed_color is not None:
                    current_pos = (x, y) if current_color == confirmed_color else confirmed_position
                    position_history.append(current_pos)
                    
                    if len(position_history) > 5:
                        position_history.pop(0)
                    
                    if len(position_history) >= 3:
                        distances = [
                            np.sqrt((position_history[i][0]-position_history[i-1][0])**2 + 
                                   (position_history[i][1]-position_history[i-1][1])**2)
                            for i in range(1, len(position_history))
                        ]
                        
                        if all(d < POSITION_STABLE_THRESHOLD for d in distances):
                            position_stable_count += 1
                        else:
                            position_stable_count = max(0, position_stable_count - 1)
                
                if (confirmed_color is not None and 
                    position_stable_count >= 4):
                    
                    formatted_data = f"{confirmed_position[0]:04}{confirmed_position[1]:04}{confirmed_color}"
                    send_data(formatted_data)
                    print(f"最终结果: 颜色 {confirmed_color} 稳定坐标 {confirmed_position}")
                    return confirmed_color
                
                break  # 只处理第一个检测到的圆形
        else:
            if last_detection_time is not None:
                elapsed_time = (current_time - last_detection_time) / cv2.getTickFrequency() * 1000
                if elapsed_time > TIMEOUT_MS:
                    print(f"帧 {frame_count}: 检测超时，跳过本次识别")
                    continue
            
        if time.time() - start_time > TOTAL_TIMEOUT:
            if confirmed_color is not None:
                avg_x = int(np.mean([p[0] for p in color_stats[confirmed_color]["positions"]]))
                avg_y = int(np.mean([p[1] for p in color_stats[confirmed_color]["positions"]]))
                formatted_data = f"{avg_x:04}{avg_y:04}{confirmed_color}"
                send_data(formatted_data)
                print(f"超时结果: 颜色 {confirmed_color} 坐标 ({avg_x}, {avg_y})")
                return confirmed_color
            else:
                best_color = max(color_stats.items(), key=lambda x: x[1]["count"])[0]
                if color_stats[best_color]["count"] > 0:
                    avg_x = int(np.mean([p[0] for p in color_stats[best_color]["positions"]]))
                    avg_y = int(np.mean([p[1] for p in color_stats[best_color]["positions"]]))
                    formatted_data = f"{avg_x:04}{avg_y:04}{best_color}"
                    send_data(formatted_data)
                    print(f"超时备用结果: 颜色 {best_color} 坐标 ({avg_x}, {avg_y})")
                    return best_color
                else:
                    send_data("000000004")
                    print("检测超时，发送默认信号")
                    return "4"
        
        time.sleep(0.02)

def run_maduoyuanxin2_centered():  # 初赛放物块的时候，色环第二次定标的程序（地上的圆形）
    global cap2
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 50, 50])
    upper_red2 = np.array([180, 255, 255])
    lower_green = np.array([30, 40, 40])
    upper_green = np.array([89, 255, 255])
    lower_blue = np.array([90, 50, 90])
    upper_blue = np.array([140, 255, 255])
    kernel = np.ones((3, 3), np.uint8)

    center_x, center_y = 320, 240
    square_side = 150
    square_side1 = 150
    square_side2 = 150
    half_side = square_side // 2
    half_side1 = square_side1 // 2
    half_side2 = square_side2 // 2

    if not cap2.isOpened():
        print("无法读取摄像头帧")
        return

    _configure_calibration_camera(cap2, 640, 480)

    start_time = time.time()
    last_detection_time = None
    timeout_ms = 200  # 超时时间300毫秒
    
    stable_count = 0  # 位置稳定计数
    color_stable_count = 0  # 颜色稳定计数
    last_center = None  # 上次检测到的中心点
    first_center = None  # 第一次检测到的中心点
    color_history = []  # 颜色历史记录
    final_color = None  # 最终确定的颜色
    last_radius = 0  # 最后检测到的半径
    
    STABLE_THRESHOLD = 5  # 位置稳定阈值(帧数)
    COLOR_STABLE_THRESHOLD = 5  # 颜色稳定阈值(帧数)
    COLOR_CONFIDENCE = 0.7  # 颜色置信度阈值
    MAX_PIXEL_MOVE = 10  # 最大允许移动像素(因分辨率更高)

    while True:
        ret, frame = cap2.read()
        if not ret:
            print("无法读取摄像头帧")
            break

        current_time = cv2.getTickCount()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        filtered_img = cv2.GaussianBlur(gray, (3, 3), 0)
        circles = cv2.HoughCircles(filtered_img,
                                cv2.HOUGH_GRADIENT, dp=1, minDist=30,
                                param1=50, param2=30,
                                minRadius=20, maxRadius=27)

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)

        red_mask = cv2.erode(red_mask, kernel, iterations=1)
        red_mask = cv2.dilate(red_mask, kernel, iterations=2)
        green_mask = cv2.erode(green_mask, kernel, iterations=2)
        green_mask = cv2.dilate(green_mask, kernel, iterations=6)
        blue_mask = cv2.erode(blue_mask, kernel, iterations=1)
        blue_mask = cv2.dilate(blue_mask, kernel, iterations=3)

        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            for (x, y, r) in circles:
                if not (center_x - half_side <= x <= center_x + half_side and
                        center_y - half_side1 <= y <= center_y + half_side2):
                    continue

                x = np.clip(x, 0, frame.shape[1] - 1)
                y = np.clip(y, 0, frame.shape[0] - 1)

                mask = np.zeros_like(gray)
                cv2.circle(mask, (x, y), int(1.4 * r), 255, -1)

                red_area = cv2.countNonZero(cv2.bitwise_and(red_mask, mask))
                green_area = cv2.countNonZero(cv2.bitwise_and(green_mask, mask))
                blue_area = cv2.countNonZero(cv2.bitwise_and(blue_mask, mask))

                max_area = max(red_area, green_area, blue_area)
                if max_area == 0:
                    print("检测到无效颜色区域（HSV全为0），跳过...")
                    continue
                
                last_detection_time = current_time
                current_center = (x, y)
                last_radius = r  # 记录半径
                
                if max_area == red_area:
                    current_color = "1"
                    masked = cv2.bitwise_and(hsv, hsv, mask=cv2.bitwise_and(red_mask, mask))
                elif max_area == green_area:
                    current_color = "2"
                    masked = cv2.bitwise_and(hsv, hsv, mask=cv2.bitwise_and(green_mask, mask))
                else:
                    current_color = "3"
                    masked = cv2.bitwise_and(hsv, hsv, mask=cv2.bitwise_and(blue_mask, mask))
                
                avg_hsv = cv2.mean(masked, mask=cv2.bitwise_and(red_mask if current_color == "1" else (green_mask if current_color == "2" else blue_mask), mask))[:3]
                
                if avg_hsv[0] == 0 and avg_hsv[1] == 0 and avg_hsv[2] == 0:
                    print(f"检测到无效{current_color}区域（HSV全为0），跳过...")
                    continue
                
                print(f"检测到颜色 {current_color}，HSV值: H={avg_hsv[0]:.1f}, S={avg_hsv[1]:.1f}, V={avg_hsv[2]:.1f}")
                
                color_history.append(current_color)
                
                if first_center is None:
                    first_center = current_center
                    stable_count = 1
                else:
                    distance = np.sqrt((current_center[0] - first_center[0])**2 + 
                                     (current_center[1] - first_center[1])**2)
                    if distance < MAX_PIXEL_MOVE:
                        stable_count += 1
                    else:
                        stable_count = 1
                        first_center = current_center
                        color_history = []  # 位置变化大时清空颜色历史
                
                if len(color_history) >= COLOR_STABLE_THRESHOLD:
                    from collections import defaultdict
                    color_counter = defaultdict(int)
                    for color in color_history:
                        color_counter[color] += 1
                    
                    most_common_color = max(color_counter.items(), key=lambda x: x[1])[0]
                    confidence = color_counter[most_common_color] / len(color_history)
                    
                    if confidence >= COLOR_CONFIDENCE:
                        final_color = most_common_color
                        print(f"颜色识别稳定: {final_color} (置信度: {confidence:.2f})")
                
                if (stable_count >= STABLE_THRESHOLD and 
                    final_color is not None):
                    formatted_data = f"{current_center[0]:04}{current_center[1]:04}{final_color}"
                    send_data(formatted_data)
                    print(f"稳定坐标发送: {formatted_data}")
                    return
        else:
            if last_detection_time is not None:
                elapsed_time = (current_time - last_detection_time) / cv2.getTickFrequency() * 1000  # 毫秒
                if elapsed_time > timeout_ms:
                    print("检测超时，跳过本次识别")
                    continue
            
        if time.time() - start_time > 8.0:
            send_data("000000004")
            print("检测超时，发送默认信号")
            break
            
        time.sleep(0.05)

class SerialInterruptHandler:
    def __init__(self):
        self.running = True
        self.last_data_time = time.time()
    def handle_serial_data(self, data):
        global cap, cap2, C_1, C_2, C_1_loop2, C_2_loop2
        global INDEX, INDEX1, INDEX2, INDEX_loop2, INDEX1_loop2, INDEX2_loop2
        data = data.strip()
        print(f"接收到: {data}")
        self.last_data_time = time.time()

        def require_video2():
            camera = ensure_video2_camera()
            if camera is None:
                print("摄像头初始化失败")
                return False
            return True

        if data == "1":
            print(f"检测到任务1: 执行二维码检测")
            run_erweima()
        elif data == "2":
            if not require_video2():
                return
            print(f"检测到任务2: 执行物块检测")
            C_1 = run_wukuaiyuanxin_1()
        elif data == "a":
            if not require_video2():
                return
            print(f"检测到任务2: 执行物块检测")
            C_1_loop2 = run_wukuaiyuanxin_1()
        elif data == "3":
            if not require_video2():
                return
            print(f"检测到任务2: 执行第一圈的转盘物块检测")
            LOOP1()
        elif data == "4":
            if not require_video2():
                return
            print(f"检测到任务2: 执行第二圈的转盘物块检测")
            LOOP2()
        elif data == "5":
            if not require_video2():
                return
            print(f"first loop已经抓完第一个物块，识别第二个物块是否稳定")
            if INDEX1 == 1:
                run_wukuaiyuanxin_xuanzequyu(INDEX1, A[1])
            else:
                run_wukuaiyuanxin_xuanzequyu(0, A[1])
        elif data == "6":
            if not require_video2():
                return
            print(f"first_loop已经抓完第二个物块，识别第三个物块是否稳定")
            if INDEX2 == 1:
                run_wukuaiyuanxin_xuanzequyu(INDEX2, A[2])
            else:
                run_wukuaiyuanxin_xuanzequyu(0, A[2])
        elif data == "b":
            if not require_video2():
                return
            print(f"second_loop已经抓完第一个物块，识别第二个物块是否稳定")
            if INDEX1_loop2 == 1:
                run_wukuaiyuanxin_xuanzequyu(INDEX1_loop2, A[5])
            else:
                run_wukuaiyuanxin_xuanzequyu(0, A[5])
        elif data == "c":
            if not require_video2():
                return
            print(f"second_loop已经抓完第二个物块，识别第三个物块是否稳定")
            if INDEX2_loop2 == 1:
                run_wukuaiyuanxin_xuanzequyu(INDEX2_loop2, A[6])
            else:
                run_wukuaiyuanxin_xuanzequyu(0, A[6])
        elif data == "7":
            if not require_video2():
                return
            print(f"进行色环检测的第一次定标")
            run_sehuanyuanxin2()
        elif data == "d":
            print("进行成品区 Code128 条形码首次定标")
            yunxing_tiaoxingma_dingbiao()
        elif data == "e":
            print("等待成品区 Code128 条码变化，并计算三次夹取位置")
            yunxing_tiaoxingma_zhuanpan()
        elif data == "f":
            print("第一次夹取完成，确认第二个目标条码2稳定")
            yunxing_tiaoxingma_xuanzequyu(dierci_jiaqu_weizhi, "2")
        elif data == "g":
            print("第二次夹取完成，确认第三个目标条码3稳定")
            yunxing_tiaoxingma_xuanzequyu(disanci_jiaqu_weizhi, "3")
        elif data == "8":
            if not require_video2():
                return
            print(f"进行色环检测的精细定标")
            run_sehuanyuanxin2_centered()
        elif data == "h":
            if not require_video2():
                return
            print("进行固定物料区 maduoyuanxin2 定标")
            run_maduoyuanxin2()
        elif data == "i":
            print("识别固定物料区 Q1/Q2/Q3，并按二维码顺序发送夹取位置")
            yunxing_sangeyuanxin_shibie_q123()
        elif data == "9":
            if not require_video2():
                return
            print(f"进行码垛检测的第一次定标")
            run_maduoyuanxin2()
        elif data == "0":
            if not require_video2():
                return
            print(f"进行码垛检测的精细定标")
            run_maduoyuanxin2()
        elif data == "r":
            ser.close()
            restart_program()
            print(f"串口 {ser.port} 已打开")
            send_data("987654321")
            print("已发送987654321")
        elif data == "end":
            print(f"任务序列完成。")
            self.running = False
        else:
            print(f"未识别的任务指令: {data}")
    def run(self):
        if not ser.is_open:
            ser.open()
        print(f"串口 {ser.port} 已打开")
        send_data("987654321")
        print("已发送987654321")
        
        try:
            while self.running:
                data = receive_data()
                if data:
                    self.handle_serial_data(data)
                else:
                    time.sleep(0.01)
                    
                if time.time() - self.last_data_time > 300:
                    print("警告: 300秒未收到任何数据，检查连接...")
                    self.last_data_time = time.time()
                    
        except KeyboardInterrupt:
            print("程序被用户终止")
        finally:
            ser.close()
            print(f"串口 {ser.port} 已关闭")
            release_video2_camera()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    handler = SerialInterruptHandler()
    handler.run()
