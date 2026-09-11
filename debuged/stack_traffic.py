"""
ixnetwork_restpy L1Config 设置 + 流量测试完整脚本
硬件：Novus Hundred Gig 系列（100G）
IxNetwork 版本：9.6
作者：参考 OpenIxia ixnetwork_restpy 官方 samples

修正：
  - InstanceId is not a string（Issue #61/#73/#76）
  - 原因：RestPy 的 _update 方法在 PATCH body 中自动注入 "id" 字段
    IxNetwork 9.6 服务端 SDM 组件无法处理，报 InstanceId is not a string
    该 bug 在 9.20 Update 2 才修复
  - 方案：monkey-patch RestPy 的 _update 方法，移除 payload 中的 "id" 字段
    修复后可以直接用原生的 field.ValueType = '...' 写法
"""
import time
from ixnetwork_restpy import SessionAssistant
from ixnetwork_restpy.assistants.batch.batchupdate import BatchUpdate
from ixnetwork_restpy.connection import Connection

# ============================================================
# Step 0: 修复 InstanceId is not a string bug
# ============================================================
# 原因：RestPy 将 field 更新发送到集合端点（如 /stack/1/field），
# 并在 payload 中带 "id" 字段来标识要更新的子资源。
# IxNetwork 服务端 SDM 的 StackFieldHandler.Find() 无法正确
# 解析 payload 中的 "id"，报 "InstanceId is not a string"。
#
# 方案：拦截 Connection._update，如果 payload 中有 "id"，
# 则将 PATCH 发送到具体资源端点（{href}/{id}），并移除 payload 中的 "id"。
# 这样服务器可以从 URL 路径中直接识别资源，无需解析 payload 中的 id。
_original_conn_update = Connection._update


def _patched_conn_update(self, href, payload):
    """拦截 Connection._update，修复 field/stack 更新时的 InstanceId 错误"""
    if isinstance(payload, dict) and 'id' in payload:
        # 将 id 移到 URL 路径中，而不是放在 payload 里
        obj_id = payload['id']
        # 确保 id 是字符串形式
        obj_id_str = str(obj_id) if not isinstance(obj_id, str) else obj_id
        # 构造具体资源的 href
        item_href = href.rstrip('/') + '/' + obj_id_str
        # 移除 payload 中的 id
        new_payload = {k: v for k, v in payload.items() if k != 'id'}
        return _original_conn_update(self, item_href, new_payload)
    elif isinstance(payload, list):
        # 批量 payload：每个 item 如果有 id 就单独处理
        # 注意：批量更新可能不支持移到 URL，这里保守处理只移除 id
        new_payload = [
            {k: v for k, v in item.items() if k != 'id'}
            if isinstance(item, dict) and 'id' in item
            else item
            for item in payload
        ]
        return _original_conn_update(self, href, new_payload)
    return _original_conn_update(self, href, payload)


Connection._update = _patched_conn_update
print("✅ 已安装 InstanceId bug 修复补丁（payload id → URL path）")

# ============================================================
# Step 1: 连接 Session
# ============================================================
session = SessionAssistant(
    IpAddress='127.0.0.1', RestPort=11009,
    UserName=None, Password=None,
    VerifyCertificates=False,
    LogLevel=SessionAssistant.LOGLEVEL_INFO,
    ClearConfig=True,
)
ixnetwork = session.Ixnetwork

# ============================================================
# Step 2: Map + Connect（IgnoreLinkUp=True 让脚本能继续）
# ============================================================
port_map = session.PortMapAssistant()
port_map.Map('192.168.27.10', 2, 2, Name='Tx')
port_map.Map('192.168.27.10', 2, 3, Name='Rx')
port_map.Connect(ForceOwnership=True, IgnoreLinkUp=True)

tx = ixnetwork.Vport.find(Name='Tx')
rx = ixnetwork.Vport.find(Name='Rx')
print(f"✅ 连接完成: Tx={tx.ConnectionState}, Rx={rx.ConnectionState}")

# ============================================================
# Step 3: 设 L1Config（NovusHundredGigLan）
#作用：IxNetwork 的 L1Config.CurrentType 返回的是小驼峰字符串（如 novusHundredGigLan）
#，但访问子对象时需要用大驼峰属性名（如 NovusHundredGigLan）。这个字典做大小写转换。
# ============================================================
#方法1，通过字典map映射的方式
# CTYPE_MAP = {
#     "tenFortyHundredGigLan": "TenFortyHundredGigLan",
#     "novusHundredGigLan": "NovusHundredGigLan",
#     "novus5GTenTwentyFiveGigLan": "Novus5GTenTwentyFiveGigLan",
#     "uhdOneHundredGigLan": "UhdOneHundredGigLan",
#     "aresOneFourHundredGigLan": "AresOneFourHundredGigLan",
#     "aresOneEightHundredGigLanQddC": "AresOneEightHundredGigLanQddC",
#     "aresOne1600G": "AresOne1600G",
# }
#
#
# def get_l1(vport):
#     ctype = vport.L1Config.CurrentType
#     prop = CTYPE_MAP.get(ctype, ctype)
#     return getattr(vport.L1Config, prop)

import re
def get_l1(vport):
    portType = vport.L1Config.CurrentType
    capitalizedCardType = re.sub('([a-zA-Z])', lambda x: x.groups()[0].upper(), portType, 1)
    return getattr(vport.L1Config, capitalizedCardType)


# 这些属性就是 GUI 上端口 Physical Port Properties 页面的勾选项
with BatchUpdate(ixnetwork):
    for vp in (tx, rx):
        l1 = get_l1(vp)                 #等价于  l1 = vport.L1Config.NovusHundredGigLan 基于此修改端口的属性
        l1.Speed = "speed100g"
        l1.SelectedSpeeds = ["speed100g"]
        l1.Loopback = False
        l1.IeeeL1Defaults = False
        l1.EnabledFlowControl = False
        l1.LaserOn = True
        l1.EnableAutoNegotiation = True
        l1.EnableRsFec = True            # 勾选 RS-FEC
        l1.EnableRsFecStats = False
        l1.TxIgnoreRxLinkFaults = False

# 验证
for name, vp in (("Tx", tx), ("Rx", rx)):
    l1 = get_l1(vp)
    print(f"✅ L1Config [{name}]: Speed={l1.Speed}, "
          f"FlowCtrl={l1.EnabledFlowControl}, "
          f"IEEE={l1.IeeeL1Defaults}, "
          f"RsFec={l1.EnableRsFec}")

# ============================================================
# Step 4: 建流量
# ============================================================
# --- 创建 TrafficItem ---
traffic_item = ixnetwork.Traffic.TrafficItem.add(
    Name='Raw Traffic', TrafficType='raw',
)
traffic_item.EndpointSet.add(
    Sources=tx.Protocols.find(),
    Destinations=rx.Protocols.find(),
)

cfg = traffic_item.ConfigElement.find()[0]
cfg.FrameRate.update(Type='percentLineRate', Rate=50)       # 50% 线速
cfg.FrameSize.update(Type='random',RandomMax=1500,RandomMin=64)
# cfg.FrameSize.FixedSize = 128                               # 帧大小 128 字节


cfg.TransmissionControl.update(Type='fixedFrameCount', FrameCount=10000)  # 发 10000 帧

# --- Ethernet 字段（monkey-patch 已修复，直接用原写法）---
# 官方写法：用 TrafficItem.find() 重新获取对象
ethernetStackObj = ixnetwork.Traffic.TrafficItem.find(
    Name='Raw Traffic'
).ConfigElement.find()[0].Stack.find(StackTypeId='ethernet$')

# 目的 MAC（递增）
ethernetDstField = ethernetStackObj.Field.find(DisplayName='Destination MAC Address')
ethernetDstField.ValueType = 'increment'
ethernetDstField.StartValue = "00:0c:29:68:05:1E"
ethernetDstField.StepValue = "00:00:00:00:00:00"
ethernetDstField.CountValue = 1

# 源 MAC（递增）
ethernetSrcField = ethernetStackObj.Field.find(DisplayName='Source MAC Address')
ethernetSrcField.ValueType = 'increment'
ethernetSrcField.StartValue = "00:0c:29:68:05:14"
ethernetSrcField.StepValue = "00:00:00:00:00:00"
ethernetSrcField.CountValue = 1


# --- 添加 IPv4 协议头（官方写法：ProtocolTemplate + Append）---
def createPacketHeader(trafficItemObj, packetHeaderToAdd=None, appendToStack=None):
    """
    用 ProtocolTemplate + Append 方法添加协议头。
    这是官方 createTrafficItemAddPacketHeader.py 示例的标准写法。

    参数：
        trafficItemObj: TrafficItem 对象
        packetHeaderToAdd: 要添加的协议头 StackTypeId（如 'ipv4'）
        appendToStack: 追加到哪个 Stack 之后（如 'ethernet$'）
    返回：
        新添加 Stack 的 Field 对象
    """
    configElement = trafficItemObj.ConfigElement.find()[0]

    # 1. 获取协议模板
    packetHeaderProtocolTemplate = ixnetwork.Traffic.ProtocolTemplate.find(
        StackTypeId=packetHeaderToAdd
    )

    # 2. 找到要追加的位置
    appendToStackObj = configElement.Stack.find(StackTypeId=appendToStack)

    # 3. 用 Append 方法添加
    appendToStackObj.Append(Arg2=packetHeaderProtocolTemplate)

    # 4. 获取新添加的 Stack
    packetHeaderStackObj = configElement.Stack.find(StackTypeId=packetHeaderToAdd)

    # 5. 返回 Field 对象
    return packetHeaderStackObj.Field


# 添加 IPv4（追加到 Ethernet 之后）
ipv4FieldObj = createPacketHeader(
    traffic_item,
    packetHeaderToAdd='ipv4',
    appendToStack='ethernet$',
)

# 源 IP（递增）
ipv4SrcField = ipv4FieldObj.find(DisplayName='Source Address')
ipv4SrcField.ValueType = 'increment'
ipv4SrcField.StartValue = '1.1.1.1'
ipv4SrcField.StepValue = '0.0.0.1'
ipv4SrcField.CountValue = 1

# 目的 IP（列表）
ipv4DstField = ipv4FieldObj.find(DisplayName='Destination Address')
ipv4DstField.ValueType = 'valueList'
ipv4DstField.ValueList = ['1.1.1.2', '1.1.1.3', '1.1.1.4', '1.1.1.5']

# 添加 TCP（追加到 IPv4 之后）
tcpFieldObj = createPacketHeader(
    traffic_item,
    packetHeaderToAdd='tcp',
    appendToStack='ipv4',
)

# 源端口（递增）
tcpSrcPortField = tcpFieldObj.find(DisplayName='TCP-Source-Port')
tcpSrcPortField.ValueType = 'increment'
tcpSrcPortField.StartValue = '1024'
tcpSrcPortField.StepValue = '1'
tcpSrcPortField.CountValue = 1

# 目的端口（列表）
tcpDstPortField = tcpFieldObj.find(DisplayName='TCP-Dest-Port')
tcpDstPortField.ValueType = 'valueList'
tcpDstPortField.ValueList = ['80', '443', '8080', '22']

print("✅ 所有流量字段配置完成")

# ============================================================
# Step 5: Apply + Start
# ============================================================
ixnetwork.Traffic.Apply()
print("✅ Traffic Apply 完成")

try:
    ixnetwork.Traffic.StartStatelessTrafficBlocking()
    print("✅ Traffic 启动成功")
except Exception as e:
    print(f"⚠️ Start 失败: {e}")

time.sleep(10)  # 等几秒让计数器积累

# ============================================================
# Step 6: 读 Port Statistics
# ============================================================
print("\n📊 Port Statistics 摘要:")
stats = session.StatViewAssistant('Port Statistics', Timeout=10)
for row in stats.Rows:
    print(f"  [{row['Port Name']:2s}] "
          f"Link={row['Link State']:10s} "
          f"LineSpeed={row['Line Speed']:10s} "
          f"TxFrames={row['Frames Tx.']:>15} "
          f"RxValid={row['Valid Frames Rx.']:>15}")

# ============================================================
# Step 7: 收尾
# ============================================================
try:
    ixnetwork.Traffic.StopStatelessTrafficBlocking()
    print("\n✅ 测试停止")
except Exception:
    pass

print("\n🎯 测试结束")
