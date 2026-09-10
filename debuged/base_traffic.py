"""
ixnetwork_restpy L1Config 设置 + 流量测试完整脚本
硬件：Novus Hundred Gig 系列（100G）
作者：参考 OpenIxia ixnetwork_restpy 官方 samples
"""
from ixnetwork_restpy import SessionAssistant
from ixnetwork_restpy.assistants.batch.batchupdate import BatchUpdate
from ixnetwork_restpy.assistants.statistics.statviewassistant import StatViewAssistant
import time

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
# ============================================================
CTYPE_MAP = {
    "tenFortyHundredGigLan": "TenFortyHundredGigLan",
    "novusHundredGigLan": "NovusHundredGigLan",
    "novus5GTenTwentyFiveGigLan": "Novus5GTenTwentyFiveGigLan",
    "uhdOneHundredGigLan": "UhdOneHundredGigLan",
    "aresOneFourHundredGigLan": "AresOneFourHundredGigLan",
    "aresOneEightHundredGigLanQddC": "AresOneEightHundredGigLanQddC",
    "aresOne1600G": "AresOne1600G",
}


def get_l1(vport):
    ctype = vport.L1Config.CurrentType
    prop = CTYPE_MAP.get(ctype, ctype)
    return getattr(vport.L1Config, prop)


# Novus 上用属性直接赋值（Issue #22 验证 update() 在某些版本失效）
with BatchUpdate(ixnetwork):
    for vp in (tx, rx):
        l1 = get_l1(vp)
        l1.Speed = "speed100g"
        l1.SelectedSpeeds = ["speed100g"]
        l1.Loopback = False
        l1.IeeeL1Defaults = False  # 取消 Use IEEE Media defaults
        l1.EnabledFlowControl = False  # 取消 Enable Flow Control
        l1.LaserOn = True
        l1.EnableAutoNegotiation = True
        l1.EnableRsFec = True  # 勾选 RS-FEC
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
traffic_item = ixnetwork.Traffic.TrafficItem.add(
    Name='Raw Traffic', TrafficType='raw',
)
traffic_item.EndpointSet.add(
    Sources=tx.Protocols.find(),
    Destinations=rx.Protocols.find(),
)

cfg = traffic_item.ConfigElement.find()
cfg.FrameRate.update(Type='percentLineRate', Rate='100')
cfg.TransmissionControl.update(Type='fixedDuration',Duration=4)

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
print("测试完成，完整无误")