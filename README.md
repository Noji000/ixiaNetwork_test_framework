# RestPy 完整学习指南

> Python 知识清单 + 对象树与参数查找手册

***

## 第一部分：Python 知识清单（按优先级分层）

### 一、必须掌握的基础（★★★★★）

| 知识点         | 为什么需要          | RestPy 典型用法                                     |
| ----------- | -------------- | ----------------------------------------------- |
| 变量与基本数据类型   | 存储 IP、端口、AS 号等 | `api_server = '192.168.1.100'`                  |
| import 导入模块 | 导入 RestPy 库    | `from ixnetwork_restpy import SessionAssistant` |
| 函数定义与调用     | 封装重复代码         | `def create_topo():`                            |
| 对象与点号链式调用   | RestPy 的核心写法   | `ixnetwork.Topology.add().DeviceGroup.add()`    |
| 列表（List）    | 端口列表、多设备       | `portList = [[ip, 1, 1], [ip, 1, 2]]`           |
| 字典（Dict）    | 处理返回数据、JSON 配置 | 统计结果、配置文件                                       |
| print 与调试   | 查看对象、排查错误      | `print(bgp)` / `print(dir(obj))`                |
| 注释          | 写可读脚本          | `# 分配端口`                                        |

> **重点中的重点**：面向对象（OOP）基础 —— 理解"对象"、"属性"、"方法"的区别，以及 `对象.属性` 和 `对象.方法()` 的不同。

### 二、强烈推荐掌握（★★★★）

| 知识点               | 作用           | 示例                                    |
| ----------------- | ------------ | ------------------------------------- |
| 异常处理 `try-except` | 捕获连接失败、端口抢占等 | 官方示例几乎都有                              |
| `time.sleep()`    | 等待协议起来、流量跑一段 | `time.sleep(15)`                      |
| 字符串格式化            | 打印信息、动态命名    | `f"Topo_{i}"`                         |
| 条件判断 `if-else`    | 判断协议状态、统计结果  | 检查 BGP 是否 up                          |
| 循环 `for / while`  | 批量创建设备       | 创建 10 台设备                             |
| 列表推导式 / `.find()` | 快速筛选对象       | `ixnetwork.Vport.find(Name='^Tx')`    |
| 函数参数（默认/关键字）      | 封装可复用配置函数    | `def create_bgp(..., local_as=65001)` |

### 三、进阶提升（★★★）

| 知识点          | 用途                       |
| ------------ | ------------------------ |
| 类（Class）编写   | 把测试逻辑封装成自己的类             |
| 文件读写         | 读取配置文件、保存结果              |
| JSON 处理      | 加载/修改 JSON 配置（`json` 模块） |
| 模块与包         | 拆分多个 `.py` 文件            |
| pytest 基础    | 做自动化测试框架                 |
| 日志 `logging` | 替代 print，方便排查            |
| 正则表达式        | `.find()` 时用正则匹配名称       |

### 四、RestPy 特有但属于 Python 用法的知识

**1. 链式调用（Method Chaining）**

```python
topology.DeviceGroup.add().Ethernet.add().Ipv4.add()
```

原理：方法 `return self`，返回对象自身，可以继续调用。

**2. 动态属性访问**

```python
bgp.DutIp.Single('1.1.1.2')
bgp.Type.Single('external')
```

**3.** **`.find()`** **过滤器**

```python
ixnetwork.Vport.find(Name='^Tx')          # 正则匹配
ixnetwork.Topology.find()[0]              # 取第一个
```

**4. 对象自省（Introspection）**

```python
help(对象)     # 查看所有属性和方法
dir(对象)      # 查看属性列表
print(对象)    # 打印主要属性值
```

***

## 第二部分：对象树与参数查找手册

### 一、对象树结构（层级关系）怎么找？

对象树就是 `Topology → DeviceGroup → Ethernet → Ipv4 → BgpIpv4Peer` 这种父子层级。

#### 方法 1：IxNetwork API Browser（最推荐）

1. 打开 IxNetwork GUI
2. 菜单：**File → Tools → IxNetwork API Browser**
3. 左边是完整对象树（层级结构）
4. 点开节点，右边显示子对象和属性

#### 方法 2：代码里直接打印

```python
ixnetwork = session.Ixnetwork

# 查看根下有哪些一级对象
print(dir(ixnetwork))

# 查看 Topology 下有什么
print(dir(ixnetwork.Topology))

# 查看具体对象的子对象
topo = ixnetwork.Topology.find()[0]
print(dir(topo))
print(dir(topo.DeviceGroup))
```

#### 方法 3：官方在线文档

```
https://openixia.github.io/ixnetwork_restpy/#/reference
```

***

### 二、功能参数（属性/方法参数）怎么找？

#### 方法 1：API Browser

- 选中对象（如 `bgpIpv4Peer`）

- 右边列出所有属性和当前值

- 点击属性名旁的 value 链接可直接修改并查看参数类型

#### 方法 2：Python 内置帮助（最实用）

```python
from ixnetwork_restpy import SessionAssistant

# 拿到对象
bgp = ixnetwork.Topology.find()[0] \
    .DeviceGroup.find()[0] \
    .Ethernet.find()[0] \
    .Ipv4.find()[0] \
    .BgpIpv4Peer.find()[0]

# 查看所有属性和方法
help(bgp)

# 只看属性列表
print(bgp.__dict__)
print(dir(bgp))
```

#### 方法 3：直接打印对象

```python
print(bgp)          # 打印主要属性值
print(bgp.DutIp)    # 查看具体属性
```

#### 方法 4：官方示例脚本

```
https://github.com/OpenIxia/IxNetwork/tree/master/RestPy/SampleScripts
```

重点关注 `bgpNgpf.py`、`loadConfigFile.py`。

***

### 三、实战快速查找流程

```
1. API Browser 找对象路径（确定层级结构）
        ↓
2. 代码里用点号一层层写到那个对象
        ↓
3. help(对象) 或 print(dir(对象)) 查看所有参数
        ↓
4. 参考官方示例脚本看别人怎么写
        ↓
5. 不确定参数时，API Browser 手动改值看 REST 属性名
```

***

### 四、常见对象参数速查表

| 对象                | 常用参数                                            |
| ----------------- | ----------------------------------------------- |
| **Topology**      | `Name`, `Ports`                                 |
| **DeviceGroup**   | `Name`, `Multiplier`                            |
| **Ethernet**      | `Mac`, `EnableVlans`                            |
| **Ipv4**          | `Address`, `GatewayIp`, `Prefix`                |
| **BgpIpv4Peer**   | `DutIp`, `Type`, `LocalAs2Bytes`, `As2Bytes`    |
| **TrafficItem**   | `Name`, `TrafficType`, `BiDirectional`          |
| **ConfigElement** | `FrameRate`, `FrameSize`, `TransmissionControl` |

***

## 第三部分：推荐学习顺序

### 阶段一：Python 基础（1-2 周）

- 变量、数据类型、列表、字典

- `if / for / while`

- 函数定义

- 简单面向对象概念（类、对象、属性、方法）

### 阶段二：立刻开始写 RestPy（边学边练）

- 按入门教程把脚本跑通

- 遇到不会的语法再回头补

### 阶段三：重点补强

- 面向对象（RestPy 的灵魂）

- `try-except`

- 函数封装

### 阶段四：进阶

- `help()` + API Browser 自己查参数

- 学习 pytest，把脚本变成测试用例

***

## 第四部分：学习资源

| 资源          | 链接                                                                       |
| ----------- | ------------------------------------------------------------------------ |
| Python 基础   | 廖雪峰 Python 教程（免费）或《Python 编程：从入门到实践》前 10 章                               |
| 面向对象        | 专门找"Python 类与对象"章节                                                       |
| RestPy 在线文档 | `https://openixia.github.io/ixnetwork_restpy/#/reference`                |
| 官方示例脚本      | `https://github.com/OpenIxia/IxNetwork/tree/master/RestPy/SampleScripts` |
| 查参数神器       | `help(对象)` + API Browser                                                 |

***

> **总结**：RestPy 对 Python 的要求不高，最核心的是"面向对象的点号写法"和基本控制流。对象树结构优先用 API Browser，参数/属性优先用 `help(对象)`。把面向对象搞明白，配合官方示例，进步会非常快。

