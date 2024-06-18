import os
import time
import shutil
import xml.etree.ElementTree as ET


class ConvertKmz:
    def __init__(self):
        super().__init__()
        self.temp_path = "temp"
        self.conf = {
            "model": "M3T",
            "droneEnumValue": "77",
            "droneSubEnumValue": "1",
            "payloadEnumValue": "67",
            "payloadPositionIndex": "0",
        }

    def start(self, path):
        self.data = self.getKmlData(path)
        os.makedirs(self.temp_path + "/wpmz", exist_ok=True)
        f1 = self.make("template.kml")
        f2 = self.make("waylines.wpml")
        shutil.make_archive("temp", "zip", self.temp_path, "wpmz")
        shutil.move("temp.zip", self.getName(path) + ".kmz")
        self.clearTemp()
        return f1 or f2

    def toDict(self, element):
        res = {}
        for child in element:
            if child.tag == "Placemark":
                if child.tag not in res:
                    res[child.tag] = []
                res[child.tag].append(self.toDict(child))
            elif child.tag == "actions":
                if child.tag not in res:
                    res[child.tag] = []
                res[child.tag].append(
                    {
                        "action": child.text,
                        "label": child.attrib.get("label", ""),
                        "param": child.attrib.get("param", ""),
                        "targetMode": child.attrib.get("targetMode", ""),
                    }
                )
            elif len(child) == 0:
                res[child.tag] = child.text
            else:
                res[child.tag] = self.toDict(child)
        return res

    def getKmlData(self, path):
        tree = ET.parse(path)
        root = tree.getroot()
        for element in root.iter():
            if "}" in element.tag:
                element.tag = element.tag.split("}", 1)[1]
        json_dict = self.toDict(root)
        return json_dict

    def make(self, file):
        status = False
        is_template = file == "template.kml"
        namespace = {"xmlns": "http://www.opengis.net/kml/2.2", "xmlns:wpml": "http://www.dji.com/wpmz/1.0.6"}
        kml = ET.Element("kml", namespace)
        Document = ET.SubElement(kml, "Document")

        if is_template:
            author = ET.SubElement(Document, "wpml:author")
            author.text = self.data["Document"]["name"]  # 文件创建作者，可选
            now = str(int(time.time() * 1000))
            createTime = ET.SubElement(Document, "wpml:createTime")
            createTime.text = now  # 文件创建时间（Unix Timestamp），可选
            updateTime = ET.SubElement(Document, "wpml:updateTime")
            updateTime.text = now  # 文件更新时间（Unix Timestamp），可选

        missionConfig = ET.SubElement(Document, "wpml:missionConfig")
        flyToWaylineMode = ET.SubElement(missionConfig, "wpml:flyToWaylineMode")
        flyToWaylineMode.text = "safely"  # 飞向首航点模式，safely：安全模式；pointToPoint：倾斜飞行模式
        finishAction = ET.SubElement(missionConfig, "wpml:finishAction")
        finishAction.text = "goHome"  # 航线结束动作，goHome：飞行器完成航线任务后，退出航线模式并返航。noAction：飞行器完成航线任务后，退出航线模式；autoLand：飞行器完成航线任务后，退出航线模式并原地降落；gotoFirstWaypoint：飞行器完成航线任务后，立即飞向航线起始点，到达后退出航线模式。
        exitOnRCLost = ET.SubElement(missionConfig, "wpml:exitOnRCLost")
        exitOnRCLost.text = "executeLostAction"  # 失控是否继续执行航线，goContinue：继续执行航线；executeLostAction：退出航线，执行失控动作
        executeRCLostAction = ET.SubElement(missionConfig, "wpml:executeRCLostAction")
        executeRCLostAction.text = "goBack"  # 失控动作类型，goBack：返航。飞行器从失控位置飞向起飞点；landing：降落。飞行器从失控位置原地降落；hover：悬停。飞行器从失控位置悬停
        globalTransitionalSpeed = ET.SubElement(missionConfig, "wpml:globalTransitionalSpeed")
        globalTransitionalSpeed.text = self.data["Document"]["Placemark"][0]["ExtendedData"]["autoFlightSpeed"]  # 全局航线过渡速度
        droneInfo = ET.SubElement(missionConfig, "wpml:droneInfo")
        droneEnumValue = ET.SubElement(droneInfo, "wpml:droneEnumValue")
        droneEnumValue.text = self.conf["droneEnumValue"]  # 飞行器机型主类型
        droneSubEnumValue = ET.SubElement(droneInfo, "wpml:droneSubEnumValue")
        droneSubEnumValue.text = self.conf["droneSubEnumValue"]  # 飞行器机型子类型
        payloadInfo = ET.SubElement(missionConfig, "wpml:payloadInfo")
        payloadEnumValue = ET.SubElement(payloadInfo, "wpml:payloadEnumValue")
        payloadEnumValue.text = self.conf["payloadEnumValue"]  # 负载机型主类型
        payloadSubEnumValue = ET.SubElement(payloadInfo, "wpml:payloadSubEnumValue")
        payloadSubEnumValue.text = "0"  # 未知
        payloadPositionIndex = ET.SubElement(payloadInfo, "wpml:payloadPositionIndex")
        payloadPositionIndex.text = self.conf["payloadPositionIndex"]  # 负载挂载位置

        Folder = ET.SubElement(Document, "Folder")
        if is_template:
            templateType = ET.SubElement(Folder, "wpml:templateType")
            templateType.text = "waypoint"  # 预定义模板类型，waypoint：航点飞行；mapping2d：建图航拍；mapping3d：倾斜摄影；mappingStrip：航带飞行
        templateId = ET.SubElement(Folder, "wpml:templateId")
        templateId.text = "0"  # 模板ID
        if is_template:
            waylineCoordinateSysParam = ET.SubElement(Folder, "wpml:waylineCoordinateSysParam")
            coordinateMode = ET.SubElement(waylineCoordinateSysParam, "wpml:coordinateMode")
            coordinateMode.text = "WGS84"  # 经纬度坐标系
            heightMode = ET.SubElement(waylineCoordinateSysParam, "wpml:heightMode")
            heightMode.text = "EGM96"  # 航点高程参考平面
            positioningType = ET.SubElement(waylineCoordinateSysParam, "wpml:positioningType")
            positioningType.text = "GPS"  # 经纬度与高度数据源
        else:
            executeHeightMode = ET.SubElement(Folder, "wpml:executeHeightMode")
            executeHeightMode.text = "WGS84"  # 执行高度模式
            waylineId = ET.SubElement(Folder, "wpml:waylineId")
            waylineId.text = "0"  # 航线ID
            distance = ET.SubElement(Folder, "wpml:distance")
            distance.text = "0"  # 航线长度
            duration = ET.SubElement(Folder, "wpml:duration")
            duration.text = "0"  # 预计执行时间
        autoFlightSpeed = ET.SubElement(Folder, "wpml:autoFlightSpeed")
        autoFlightSpeed.text = globalTransitionalSpeed.text  # 全局航线飞行速度
        if is_template:
            globalHeight = ET.SubElement(Folder, "wpml:globalHeight")
            globalHeight.text = "0"  # 全局航线高度（相对起飞点高度）
            caliFlightEnable = ET.SubElement(Folder, "wpml:caliFlightEnable")
            caliFlightEnable.text = "0"  # 是否开启标定飞行
            gimbalPitchMode = ET.SubElement(Folder, "wpml:gimbalPitchMode")
            gimbalPitchMode.text = "manual"  # gimbalPitchMode
            globalWaypointHeadingParam = ET.SubElement(Folder, "wpml:globalWaypointHeadingParam")
            waypointHeadingMode = ET.SubElement(globalWaypointHeadingParam, "wpml:waypointHeadingMode")
            waypointHeadingMode.text = "smoothTransition"  # 飞行器偏航角模式
            waypointHeadingAngle = ET.SubElement(globalWaypointHeadingParam, "wpml:waypointHeadingAngle")
            waypointHeadingAngle.text = "0"  # 飞行器偏航角度
            waypointPoiPoint = ET.SubElement(globalWaypointHeadingParam, "wpml:waypointPoiPoint")
            waypointPoiPoint.text = "0.000000,0.000000,0.000000"  # 兴趣点
            waypointHeadingPoiIndex = ET.SubElement(globalWaypointHeadingParam, "wpml:waypointHeadingPoiIndex")
            waypointHeadingPoiIndex.text = "0"  # 未知
            globalWaypointTurnMode = ET.SubElement(Folder, "wpml:globalWaypointTurnMode")
            globalWaypointTurnMode.text = "toPointAndStopWithDiscontinuityCurvature"  # 全局航点类型（全局航点转弯模式）
            globalUseStraightLine = ET.SubElement(Folder, "wpml:globalUseStraightLine")
            globalUseStraightLine.text = "1"  # 全局航段轨迹是否尽量贴合直线

        _actionGroupId = 0
        _index = 0
        for Placemark_item in self.data["Document"]["Folder"]["Placemark"]:
            # for
            Placemark = ET.SubElement(Folder, "Placemark")
            Point = ET.SubElement(Placemark, "Point")
            coordinates = ET.SubElement(Point, "coordinates")
            coordinates_arr = Placemark_item["Point"]["coordinates"].split(",")
            coordinates.text = coordinates_arr[0] + "," + coordinates_arr[1]  # 航点经纬度<纬度,经度>
            index = ET.SubElement(Placemark, "wpml:index")
            index.text = str(_index)  # 航点序号
            _index += 1
            if is_template:
                ellipsoidHeight = ET.SubElement(Placemark, "wpml:ellipsoidHeight")
                ellipsoidHeight.text = coordinates_arr[2]  # 全局航线高度（椭球高）
                height = ET.SubElement(Placemark, "wpml:height")
                height.text = coordinates_arr[2]  # 全局航线高度（EGM96海拔高/相对起飞点高度/AGL相对地面高度）
            else:
                executeHeight = ET.SubElement(Placemark, "wpml:executeHeight")
                executeHeight.text = coordinates_arr[2]  # 航点执行高度
                waypointSpeed = ET.SubElement(Placemark, "wpml:waypointSpeed")
                waypointSpeed.text = globalTransitionalSpeed.text  # 航点飞行速度，当前航点飞向下一个航点的速度
            waypointHeadingParam = ET.SubElement(Placemark, "wpml:waypointHeadingParam")
            waypointHeadingMode = ET.SubElement(waypointHeadingParam, "wpml:waypointHeadingMode")
            waypointHeadingMode.text = "smoothTransition"  # 飞行器偏航角模式
            waypointHeadingAngle = ET.SubElement(waypointHeadingParam, "wpml:waypointHeadingAngle")
            waypointHeadingAngle.text = Placemark_item["ExtendedData"]["heading"] if "heading" in Placemark_item["ExtendedData"] else "0"  # 飞行器偏航角度
            waypointPoiPoint = ET.SubElement(waypointHeadingParam, "wpml:waypointPoiPoint")
            waypointPoiPoint.text = "0.000000,0.000000,0.000000"  # 兴趣点
            if not is_template:
                waypointHeadingAngleEnable = ET.SubElement(waypointHeadingParam, "wpml:waypointHeadingAngleEnable")
                waypointHeadingAngleEnable.text = "1"  # 未知
            waypointHeadingPathMode = ET.SubElement(waypointHeadingParam, "wpml:waypointHeadingPathMode")
            waypointHeadingPathMode.text = "followBadArc"  # 飞行器偏航角转动方向
            waypointHeadingPoiIndex = ET.SubElement(waypointHeadingParam, "wpml:waypointHeadingPoiIndex")
            waypointHeadingPoiIndex.text = "0"  # 未知
            if is_template:
                useGlobalSpeed = ET.SubElement(Placemark, "wpml:useGlobalSpeed")
                useGlobalSpeed.text = "1"  # 是否使用全局飞行速度
                useGlobalTurnParam = ET.SubElement(Placemark, "wpml:useGlobalTurnParam")
                useGlobalTurnParam.text = "1"  # 是否使用全局航点类型（全局航点转弯模式）
            else:
                waypointTurnParam = ET.SubElement(Placemark, "wpml:waypointTurnParam")
                waypointTurnMode = ET.SubElement(waypointTurnParam, "wpml:waypointTurnMode")
                waypointTurnMode.text = "toPointAndStopWithDiscontinuityCurvature"  # 航点类型
                waypointTurnDampingDist = ET.SubElement(waypointTurnParam, "wpml:waypointTurnDampingDist")
                waypointTurnDampingDist.text = "0"  # 航点转弯截距
            useStraightLine = ET.SubElement(Placemark, "wpml:useStraightLine")
            if is_template:
                useStraightLine.text = "0"  # 该航段是否贴合直线
            else:
                useStraightLine.text = "1"
            if "actions" in Placemark_item["ExtendedData"]:
                actionGroup = ET.SubElement(Placemark, "wpml:actionGroup")
                actionGroupId = ET.SubElement(actionGroup, "wpml:actionGroupId")
                actionGroupId.text = str(_actionGroupId)  # 动作组id
                actionGroupStartIndex = ET.SubElement(actionGroup, "wpml:actionGroupStartIndex")
                actionGroupStartIndex.text = str(_actionGroupId + 1)  # 动作组开始生效的航点
                actionGroupEndIndex = ET.SubElement(actionGroup, "wpml:actionGroupEndIndex")
                actionGroupEndIndex.text = actionGroupStartIndex.text  # 动作组结束生效的航点
                actionGroupMode = ET.SubElement(actionGroup, "wpml:actionGroupMode")
                actionGroupMode.text = "sequence"  # 动作执行模式
                actionTrigger = ET.SubElement(actionGroup, "wpml:actionTrigger")
                actionTriggerType = ET.SubElement(actionTrigger, "wpml:actionTriggerType")
                actionTriggerType.text = "reachPoint"  # 动作触发器类型
                _actionGroupId += 1

                _actionId = 0
                for actions_item in Placemark_item["ExtendedData"]["actions"]:
                    # while
                    action = ET.SubElement(actionGroup, "wpml:action")
                    actionId = ET.SubElement(action, "wpml:actionId")
                    if is_template:
                        actionId.text = "0"  # 动作id
                    else:
                        actionId.text = str(_actionId)
                        _actionId += 1
                    actionActuatorFunc = ET.SubElement(action, "wpml:actionActuatorFunc")  # 动作类型
                    actionActuatorFuncParam = ET.SubElement(action, "wpml:actionActuatorFuncParam")
                    if actions_item["action"] == "ShootPhoto":
                        actionActuatorFunc.text = "takePhoto"  # 单拍
                        payloadPositionIndex = ET.SubElement(actionActuatorFuncParam, "wpml:payloadPositionIndex")
                        payloadPositionIndex.text = "0"  # 负载挂载位置
                        fileSuffix = ET.SubElement(actionActuatorFuncParam, "wpml:fileSuffix")
                        fileSuffix.text = ""  # 拍摄照片文件后缀
                        # payloadLensIndex = ET.SubElement(actionActuatorFuncParam, "wpml:payloadLensIndex")
                        # payloadLensIndex.text = "1" #拍摄照片存储类型
                        useGlobalPayloadLensIndex = ET.SubElement(actionActuatorFuncParam, "wpml:useGlobalPayloadLensIndex")
                        useGlobalPayloadLensIndex.text = "1"  # 是否使用全局存储类型
                    elif actions_item["action"] == "StartRecording":
                        actionActuatorFunc.text = "startRecord"  # 开始录像
                        payloadPositionIndex = ET.SubElement(actionActuatorFuncParam, "wpml:payloadPositionIndex")
                        payloadPositionIndex.text = "0"  # 负载挂载位置
                        fileSuffix = ET.SubElement(actionActuatorFuncParam, "wpml:fileSuffix")
                        fileSuffix.text = ""  # 拍摄照片文件后缀
                        # payloadLensIndex = ET.SubElement(actionActuatorFuncParam, "wpml:payloadLensIndex")
                        # payloadLensIndex.text = "1" #视频存储类型
                        useGlobalPayloadLensIndex = ET.SubElement(actionActuatorFuncParam, "wpml:useGlobalPayloadLensIndex")
                        useGlobalPayloadLensIndex.text = "1"  # 是否使用全局存储类型
                    elif actions_item["action"] == "StopRecording":
                        actionActuatorFunc.text = "stopRecord"  # 结束录像
                        payloadPositionIndex = ET.SubElement(actionActuatorFuncParam, "wpml:payloadPositionIndex")
                        payloadPositionIndex.text = "0"  # 负载挂载位置
                        payloadLensIndex = ET.SubElement(actionActuatorFuncParam, "wpml:payloadLensIndex")
                        payloadLensIndex.text = "zoom"  # 视频存储类型
                    elif actions_item["action"] == "focus":
                        actionActuatorFunc.text = "focus"  # 对焦
                        payloadPositionIndex = ET.SubElement(actionActuatorFuncParam, "wpml:payloadPositionIndex")
                        payloadPositionIndex.text = "0"  # 负载挂载位置
                        isPointFocus = ET.SubElement(actionActuatorFuncParam, "wpml:isPointFocus")
                        isPointFocus.text = "0"  # 是否点对焦
                        focusX = ET.SubElement(actionActuatorFuncParam, "wpml:focusX")
                        focusX.text = "0.5"  # 对焦点位置
                        focusY = ET.SubElement(actionActuatorFuncParam, "wpml:focusY")
                        focusY.text = "0.5"  # 对焦点位置
                        focusRegionWidth = ET.SubElement(actionActuatorFuncParam, "wpml:focusRegionWidth")
                        focusRegionWidth.text = "0"  # 对焦区域宽度比
                        focusRegionHeight = ET.SubElement(actionActuatorFuncParam, "wpml:focusRegionHeight")
                        focusRegionHeight.text = "0"  # 对焦区域高度比
                        isInfiniteFocus = ET.SubElement(actionActuatorFuncParam, "wpml:isInfiniteFocus")
                        isInfiniteFocus.text = "0"  # 是否无穷远对焦
                    elif actions_item["action"] == "zoom":
                        actionActuatorFunc.text = "zoom"  # 变焦
                        payloadPositionIndex = ET.SubElement(actionActuatorFuncParam, "wpml:payloadPositionIndex")
                        payloadPositionIndex.text = "0"  # 负载挂载位置
                        focalLength = ET.SubElement(actionActuatorFuncParam, "wpml:focalLength")
                        focalLength.text = "50"  # 变焦焦距
                    elif actions_item["action"] == "customDirName":
                        actionActuatorFunc.text = "customDirName"  # 创建新文件夹
                        payloadPositionIndex = ET.SubElement(actionActuatorFuncParam, "wpml:payloadPositionIndex")
                        payloadPositionIndex.text = "0"  # 负载挂载位置
                        directoryName = ET.SubElement(actionActuatorFuncParam, "wpml:directoryName")
                        directoryName.text = "folder"  # 新文件夹的名称
                    elif actions_item["action"] == "GimbalPitch":
                        actionActuatorFunc.text = "gimbalRotate"  # 旋转云台
                        payloadPositionIndex = ET.SubElement(actionActuatorFuncParam, "wpml:payloadPositionIndex")
                        payloadPositionIndex.text = "0"  # 负载挂载位置
                        gimbalHeadingYawBase = ET.SubElement(actionActuatorFuncParam, "wpml:gimbalHeadingYawBase")
                        gimbalHeadingYawBase.text = "north"  # 云台偏航角转动坐标系
                        gimbalRotateMode = ET.SubElement(actionActuatorFuncParam, "wpml:gimbalRotateMode")
                        gimbalRotateMode.text = "absoluteAngle"  # 云台转动模式
                        gimbalPitchRotateEnable = ET.SubElement(actionActuatorFuncParam, "wpml:gimbalPitchRotateEnable")
                        gimbalPitchRotateEnable.text = "1"  # 是否使能云台Pitch转动
                        gimbalPitchRotateAngle = ET.SubElement(actionActuatorFuncParam, "wpml:gimbalPitchRotateAngle")
                        gimbalPitchRotateAngle.text = actions_item["param"]  # 云台Pitch转动角度
                        gimbalRollRotateEnable = ET.SubElement(actionActuatorFuncParam, "wpml:gimbalRollRotateEnable")
                        gimbalRollRotateEnable.text = "0"  # 是否使能云台Roll转动
                        gimbalRollRotateAngle = ET.SubElement(actionActuatorFuncParam, "wpml:gimbalRollRotateAngle")
                        gimbalRollRotateAngle.text = "0"  # 云台Roll转动角度
                        gimbalYawRotateEnable = ET.SubElement(actionActuatorFuncParam, "wpml:gimbalYawRotateEnable")
                        gimbalYawRotateEnable.text = "0"  # 是否使能云台Yaw转动
                        gimbalYawRotateAngle = ET.SubElement(actionActuatorFuncParam, "wpml:gimbalYawRotateAngle")
                        gimbalYawRotateAngle.text = "0"  # 云台Yaw转动角度
                        gimbalRotateTimeEnable = ET.SubElement(actionActuatorFuncParam, "wpml:gimbalRotateTimeEnable")
                        gimbalRotateTimeEnable.text = "0"  # 是否使能云台转动时间
                        gimbalRotateTime = ET.SubElement(actionActuatorFuncParam, "wpml:gimbalRotateTime")
                        gimbalRotateTime.text = "0"  # 云台完成转动用时
                    elif actions_item["action"] == "AircraftYaw":
                        actionActuatorFunc.text = "rotateYaw"  # 飞行器偏航
                        aircraftHeading = ET.SubElement(actionActuatorFuncParam, "wpml:aircraftHeading")
                        aircraftHeading.text = actions_item["param"]  # 飞行器目标偏航角（相对于地理北）
                        aircraftPathMode = ET.SubElement(actionActuatorFuncParam, "wpml:aircraftPathMode")
                        aircraftPathMode.text = "counterClockwise"  # 飞行器偏航角转动模式
                    elif actions_item["action"] == "Hovering":
                        actionActuatorFunc.text = "hover"  # 悬停等待
                        hoverTime = ET.SubElement(actionActuatorFuncParam, "wpml:hoverTime")
                        hoverTime.text = actions_item["param"]  # 飞行器悬停等待时间，秒
                    elif actions_item["action"] == "gimbalEvenlyRotate":
                        actionActuatorFunc.text = "gimbalEvenlyRotate"  # 航段间均匀转动云台pitch角
                        gimbalPitchRotateAngle = ET.SubElement(actionActuatorFuncParam, "wpml:gimbalPitchRotateAngle")
                        gimbalPitchRotateAngle.text = "0"  # 云台Pitch转动角度
                        payloadPositionIndex = ET.SubElement(actionActuatorFuncParam, "wpml:payloadPositionIndex")
                        payloadPositionIndex.text = "0"  # 负载挂载位置
                    elif actions_item["action"] == "orientedShoot":
                        actionActuatorFunc.text = "orientedShoot"  # 精准复拍动作
                    elif actions_item["action"] == "panoShot":
                        actionActuatorFunc.text = "panoShot"  # 全景拍照动作（仅支持M30/M30T）
                    elif actions_item["action"] == "recordPointCloud":
                        actionActuatorFunc.text = "recordPointCloud"  # 点云录制操作
                        payloadPositionIndex = ET.SubElement(actionActuatorFuncParam, "wpml:payloadPositionIndex")
                        payloadPositionIndex.text = "0"  # 负载挂载位置
                        recordPointCloudOperate = ET.SubElement(actionActuatorFuncParam, "wpml:recordPointCloudOperate")
                        recordPointCloudOperate.text = "startRecord"  # 点云操作，startRecord：开始点云录制，pauseRecord：暂停点云录制，resumeRecord：继续点云录制，stopRecord：结束点云录制

            if not is_template:
                waypointGimbalHeadingParam = ET.SubElement(Placemark, "wpml:waypointGimbalHeadingParam")
                waypointGimbalPitchAngle = ET.SubElement(waypointGimbalHeadingParam, "wpml:waypointGimbalPitchAngle")
                waypointGimbalPitchAngle.text = "0"  # 未知
                waypointGimbalYawAngle = ET.SubElement(waypointGimbalHeadingParam, "wpml:waypointGimbalYawAngle")
                waypointGimbalYawAngle.text = "0"  # 未知
            isRisky = ET.SubElement(Placemark, "wpml:isRisky")
            isRisky.text = "0"  # 是否危险点
            if not is_template:
                waypointWorkType = ET.SubElement(Placemark, "wpml:waypointWorkType")
                waypointWorkType.text = "0"  # 未知
            # end for

        if is_template:
            payloadParam = ET.SubElement(Folder, "wpml:payloadParam")
            payloadPositionIndex = ET.SubElement(payloadParam, "wpml:payloadPositionIndex")
            payloadPositionIndex.text = "0"  # 负载挂载位置

        xml_str = ET.tostring(kml, encoding="utf-8")
        content = xml_str.decode("utf-8")
        content = '<?xml version="1.0" encoding="UTF-8"?>' + content

        try:
            with open(os.path.join(self.temp_path, "wpmz", file), "w", encoding="UTF-8") as file:
                file.write(content)
        except:
            status = "保存文件异常"

        return status

    def clearTemp(self):
        if os.path.exists(self.temp_path):
            shutil.rmtree(self.temp_path)

    def getName(self, filepath):
        filename_with_extension = os.path.basename(filepath)
        filename, _ = os.path.splitext(filename_with_extension)
        return filename


if __name__ == "__main__":
    app = ConvertKmz()
