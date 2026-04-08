# Seeyon 项目类与方法复习手册

生成时间：2026-04-09

说明：这份手册是基于当前 `txt/` 中已经归档的问题内容提炼出的 Seeyon 相关类、方法、接口和对象清单，目的是方便复习学习，不是对 `seeyon8.0` 源码仓库的一次完整静态扫描。因此这里更适合做“学习地图”和“复习提纲”，而不是绝对完整的源码索引。

## 一、怎么用这份手册

- 先看“核心类与方法”，这些是你后续复习 Seeyon 时最值得优先反复看的部分。
- 再看“非核心但常见”，这些类通常是基础设施、辅助组件、日志、缓存或支撑层。
- 如果你要继续深挖源码，建议按“接口入口 -> Controller/Manager -> 领域对象/表 -> 辅助类”的顺序读。
- 如果你要排查问题，优先看“使用场景”和“复习提示”，不要一上来就陷进实现细节。

## 二、复习优先级

### 第一层：最核心，必须先熟

1. `GovdocManagerImpl.transFinishWorkItemPublic`
2. `rest/bpm/process/start`
3. `WorkTimeSetController.setCurrencyWorkTime`
4. `FormDataController`
5. `ConcreteSessionFormDataRedisManagerImpl`
6. `IndexForMobileController.getToken`
7. 文号相关对象链：`GovdocMarkManagerImpl` / `GovdocMarkHelper` / `EdocMarkUtil` / `EdocMarkDefinitionManagerImpl`

### 第二层：高频支撑，最好熟

1. `WorkflowApiManager`
2. `GovdocPubManagerImpl`
3. `EdocSummaryManagerImpl`
4. `EdocManagerImpl`
5. `M3StatisticResource.reportPerformance`
6. `CtpLogFactory`
7. `FormApi4Cap4Impl`

### 第三层：辅助理解，可按需看

1. `Log4JConfigurator`
2. `LogTool`
3. `ThirdPartyLogger`
4. `SystemOutRedirector`
5. `GlobalCache` / `Cache` / `SeeyonGlobalCache` / `AbstractCache`
6. `RedisOpt` / `PipelineRedisOpt`
7. `BaseController` / `BasePO` / `AppContext`

## 三、之前讨论过的 Seeyon 主题总梳理

这一部分不是按类拆，而是按“之前反复讨论过的主题”来归纳，方便你从问题域回到代码域。

### 1. 公文流转与工作流处理

- 重点问题：
  - `GovdocManagerImpl.transFinishWorkItemPublic` 到底哪些逻辑是真正核心
  - 哪些代码是在推进工作流
  - 哪些代码只是修改表状态
  - 哪些代码是外围通知、日志、事件
- 对应核心对象：
  - `GovdocManagerImpl`
  - `WorkflowApiManager`
  - `GovdocPubManagerImpl`
  - `EdocSummaryManagerImpl`
- 复习重点：
  - 公文处理动作和工作流动作不要混看
  - “已阅”“办结”“提交”这几种动作的语义差别要看清
  - 业务状态、流程状态、数据状态往往不是同一层

### 2. BPM 接口与外部发起流程

- 重点问题：
  - `rest/bpm/process/start` 如何使用
  - 它的核心实现类是什么
  - 还有哪些类似接口
- 对应核心对象：
  - `POST /rest/bpm/process/start`
  - `WorkflowApiManager`
- 复习重点：
  - 先看接口契约，再看实现入口
  - 外部发起流程和内部业务按钮触发流程，入口不同但最终会汇入流程引擎

### 3. 文号生成、文号历史与节点权限

- 重点问题：
  - `newflowtype` 的语义
  - 哪些表单、哪些节点会生成文号
  - 文号重复的原因
  - 文号定义、文号记录、文号历史之间的区别
- 对应核心对象：
  - `GovdocMarkManagerImpl`
  - `GovdocMarkHelper`
  - `EdocMarkUtil`
  - `EdocMarkDefinitionManagerImpl`
  - `GOVDOC_MARK_RECORD`
  - `EDOC_MARK_HISTORY`
  - `EDOC_MARK_DEFINITION`
- 复习重点：
  - 文号定义层、权限层、运行时记录层、历史层一定要分开
  - 节点权限里“可编辑/只读/隐藏”直接影响文号是否能生成或显示
  - 表单字段命名也有约定：`docMark`、`docMark2`、`serialNo`、`signMark`

### 4. 表单、CAP4、Formtalk 导入与缓存问题

- 重点问题：
  - xsn 文件导入表单原理
  - CAP4 的设计与实现
  - 移动端/H5 访问表单时为什么会报“表单不存在/内存中表单数据不存在”
- 对应核心对象：
  - `FormDataController`
  - `ConcreteSessionFormDataRedisManagerImpl`
  - `FormApi4Cap4Impl`
  - `FormtalkImportController`
  - `FormtalkEventManagerImpl`
  - `FormtalkTrans2CAP4Impl`
- 复习重点：
  - 表单定义、表单数据、表单缓存是三层
  - CAP4 是能力平台层，Formtalk 更像导入/转换链路
  - 表单页面异常常常不是页面问题，而是缓存与上下文问题

### 5. 登录、会话、下线与用户识别

- 重点问题：
  - “您的帐号在另一地点登录，您被迫下线”提示的代码来源
  - 与服务器失去连接时为什么会被迫下线
  - 根据什么值判断是同一个用户
  - token、session、cookie 三者的关系
- 对应核心对象：
  - `IndexForMobileController.getToken`
  - `OrgManager`
  - `CurrentUserToSeeyonApp`
  - `orgmember`
  - `orgrelation`
- 复习重点：
  - 先确认用户身份对象，再确认会话对象，再确认连接状态
  - “用户是谁”和“当前会话是否有效”是两个不同问题

### 5.1 OrgManager 与组织架构读取方法

- 重点问题：
  - `OrgManager` 常用哪些方法
  - 什么时候用 `getMemberById`，什么时候用 `getDepartmentById`
  - 什么时候应该优先走组织缓存而不是直接查表
  - `orgmember` 和 `orgrelation` 的职责如何区分
- 对应核心对象：
  - `OrgManager`
  - `OrgManagerImpl`
  - `OrgManagerDirectImpl`
  - `OrgHelper`
  - `orgmember`
  - `orgrelation`
- 复习重点：
  - `OrgManager` 是组织架构读取标准入口
  - `OrgManagerDirectImpl` 更偏底层更新和双表同步，不是日常读取首选
  - 读组织对象时优先用 `OrgManager`，不要业务代码里到处自己查表
  - 组织模型问题要同时理解“成员实体”和“关系实体”两层

### 6. 工作日、截止时间与业务规则配置

- 重点问题：
  - `setCurrencyWorkTime` 如何实时设置工作日
  - `summary.getDeadlineDatetime()` 为什么可能需要返回 `null`
  - 2099 年后、3000 年这类极端时间规则如何配置
- 对应核心对象：
  - `WorkTimeSetController.setCurrencyWorkTime`
  - `EdocSummary.getDeadlineDatetime()`
- 复习重点：
  - 时间问题不要只看日期计算代码，要同时看配置入口和默认规则
  - 运行时接口修改规则和静态配置不是一回事

### 7. 日志体系与性能统计

- 重点问题：
  - Seeyon 日志输出混乱如何治理
  - `System.out` 如何统一收敛到日志体系
  - 前端性能统计接口如何设计
- 对应核心对象：
  - `CtpLogFactory`
  - `Log4JConfigurator`
  - `LogTool`
  - `ThirdPartyLogger`
  - `SystemOutRedirector`
  - `M3StatisticResource.reportPerformance`
- 复习重点：
  - 日志体系要先统一入口，再谈分类和落地文件
  - 性能统计接口要同时考虑校验、日志模型、扩展字段和后续查询
## 四、核心类与方法

### 1. `com.seeyon.apps.govdoc.manager.impl.GovdocManagerImpl`

- 核心级别：核心
- 关注方法：`transFinishWorkItemPublic(GovdocDealVO dealVo, ColHandleType handleType)`
- 使用场景：
  - 公文处理节点提交
  - “已阅”操作分析
  - 流程完成、状态变更、工作流协同处理
- 方法定位：
  - 这是公文处理链路里的关键方法之一，问题归档中多次围绕它展开“哪些逻辑是真正核心”“哪些只是外部调用”“哪些只改表状态”等分析。
- 用法理解：
  - 输入通常是当前处理上下文 `dealVo` 和处理类型 `handleType`
  - 方法内部一般会同时涉及：
    - 工作流推进
    - 公文业务状态修改
    - 相关表更新
    - 事件/外部接口触发
- 复习时重点看什么：
  - 哪些代码是真正驱动流程继续向前的
  - 哪些代码只是补充业务状态
  - 哪些代码是外围通知、扩展、日志、事件
- 为什么它是核心：
  - 因为它处于“业务动作 -> 工作流状态 -> 数据状态”三者交汇点，是理解公文流转的主入口之一。

### 2. `POST /rest/bpm/process/start`

- 核心级别：核心
- 对象类型：接口入口
- 使用场景：
  - 发起 BPM 流程
  - 外部系统通过 REST 启动流程
  - Postman、代码、HTTP 客户端调用
- 用法理解：
  - 归档里明确提到这是 Seeyon BPM 模块核心接口之一
  - 典型方式是 `POST /rest/bpm/process/start`
  - 归档示例里出现了 `HttpPost("http://localhost:8080/seeyon/rest/bpm/process/start")`
- 复习时重点看什么：
  - 接口路径和调用方式
  - 对应的核心实现类和类似接口
  - 接口背后如何进入 BPM 模块
- 为什么它是核心：
  - 因为它代表“外部请求如何进入流程引擎”的标准入口，理解它相当于理解 BPM 对外能力的一个核心切面。

### 3. `WorkTimeSetController.setCurrencyWorkTime`

- 核心级别：核心
- 使用场景：
  - 实时设置工作日
  - 解决 2099/3000 年这类边界年份配置问题
  - 通过接口动态修改工作日规则
- 接口路径：
  - `/seeyon/worktimeset.do?method=setCurrencyWorkTime`
- 典型用法：
  - 可通过浏览器、Postman、`fetch`、`curl` 调用
  - 归档中明确提到它支持实时设置工作日
- 复习时重点看什么：
  - 为什么要走接口而不是只改数据库
  - 工作日配置如何影响截止时间、流程时间计算
  - 接口参数和工作日数据格式
- 为什么它是核心：
  - 因为它直接连接“业务规则配置”和“系统运行时行为”，是典型的配置影响业务逻辑的入口。

### 4. `com.seeyon.ctp.form.service.FormDataController`

- 核心级别：核心
- 使用场景：
  - 表单数据获取
  - 移动端/H5 表单访问
  - 表单缓存失效或“表单不存在/内存中表单数据不存在”问题定位
- 用法理解：
  - 它更像表单数据的服务入口或控制器入口，负责把请求导向表单数据处理链
  - 在归档问题中，它与表单缓存和移动端表单问题一起出现
- 复习时重点看什么：
  - 表单数据是如何取的
  - 请求进来之后是直接读数据库，还是优先读缓存
  - 与 Redis 表单缓存管理器的关系
- 为什么它是核心：
  - 因为它在表单访问问题里属于“入口层”，理解入口层才能往下追数据丢失、缓存失效、移动端报错。

### 5. `ConcreteSessionFormDataRedisManagerImpl`

- 核心级别：核心
- 使用场景：
  - 表单数据 Redis 缓存
  - 会话内表单数据存取
  - 移动端/H5 表单临时数据丢失排查
- 归档中明确关注的内容：
  - 缓存配置
  - 存储机制
  - 获取机制
- 用法理解：
  - 它是表单数据缓存层的重要实现类
  - 常见问题是：
    - 为什么缓存里没有数据
    - 为什么 session 还在但表单数据失效
    - 为什么移动端更容易触发表单数据不存在
- 复习时重点看什么：
  - key 是怎么生成的
  - 缓存存取生命周期
  - 与 `FormDataController` 的调用关系
- 为什么它是核心：
  - 因为很多“表单打不开”“移动端表单异常”本质上不是表层页面问题，而是缓存/会话数据取不到。

### 6. `src/com/seeyon/ctp/rest/resources/IndexForMobileController.java`

- 核心级别：核心
- 关注方法：
  - `getToken`
  - `mobileAllSendDone`
- 使用场景：
  - 移动端登录与 token 获取
  - 移动端待办/已办或发送相关业务
- 归档里出现的关注点：
  - `getToken` 日志打印耗时 6 秒
  - `mobileAllSendDone` 的业务逻辑、函数调用关系、代码分析
- 用法理解：
  - `getToken` 是典型的移动端认证与令牌分发入口
  - `mobileAllSendDone` 更偏移动端业务操作处理
- 复习时重点看什么：
  - token 从哪里生成
  - 登录态和 token 的关系
  - 移动端接口和普通 Web 入口有何差异
- 为什么它是核心：
  - 因为它是“移动端入口层”的高频对象，关系到认证、接口性能和移动端业务入口。

### 7. 文号链路核心对象

#### 7.1 `GovdocMarkManagerImpl`

- 核心级别：核心
- 使用场景：
  - 公文文号生成与管理
  - 文号使用状态判断
  - 与公文流程状态联动
- 复习重点：
  - 文号何时生成
  - 文号何时占用、何时入历史
  - 与流程节点处理的关系

#### 7.2 `GovdocMarkHelper`

- 核心级别：核心
- 使用场景：
  - 文号处理辅助逻辑
  - 文号记录、文号状态辅助计算
- 复习重点：
  - 它通常不是主入口，但经常是主流程方法中的重要辅助逻辑

#### 7.3 `EdocMarkUtil`

- 核心级别：核心
- 使用场景：
  - 文号工具逻辑
  - 文号格式处理、使用判断、辅助转换
- 复习重点：
  - 与业务 Manager 的边界
  - 它是工具层，不要把它当业务入口

#### 7.4 `EdocMarkDefinitionManagerImpl`

- 核心级别：核心
- 使用场景：
  - 文号定义管理
  - 文号规则配置和定义层逻辑
- 复习重点：
  - “文号定义”和“文号使用记录”是两个层次，不要混看

## 五、核心表/对象联动

虽然你这次主要问的是类和方法，但 Seeyon 里很多类只有结合表和领域对象一起看才容易懂，所以这里单独列出来。

### 1. `GOVDOC_MARK_RECORD`

- 核心级别：核心数据对象
- 关联类：
  - `GovdocMarkRecord`
  - `GovdocMarkHelper`
  - `GovdocMarkManagerImpl`
- 使用场景：
  - 记录公文文号当前记录与使用状态
- 复习重点：
  - 它更偏“当前记录/主记录”
  - 与 `EDOC_MARK_HISTORY` 的职责区别

### 2. `EDOC_MARK_HISTORY`

- 核心级别：核心数据对象
- 关联类：
  - `EdocMarkHistory`
  - `EdocMarkHistoryManagerImpl`
- 使用场景：
  - 文号历史使用记录
  - 已完成/已使用文号追踪
- 复习重点：
  - 适合用来判断文号历史使用情况
  - 不能简单等同于当前生效记录

### 3. `EDOC_MARK` / `EDOC_MARK_DEFINITION` / `EDOC_MARK_RESERVE`

- 核心级别：核心数据对象
- 使用场景：
  - 文号定义
  - 文号保留
  - 文号规则管理
- 复习重点：
  - 复习时要把“定义”“保留”“记录”“历史”四种角色分开

### 4. `EdocSummary`

- 核心级别：核心领域对象
- 使用场景：
  - 公文摘要、流程上下文
  - 截止时间、文号、业务属性等核心信息承载
- 相关方法/字段：
  - `summary.getDeadlineDatetime()`
- 复习重点：
  - 这是很多业务规则判断的承载对象，不只是一个普通实体类

### 5. `orgmember` / `orgrelation`

- 核心级别：核心组织模型
- 使用场景：
  - 组织模型
  - 人员与组织关系
- 复习重点：
  - 为什么两个表会有重复字段
  - 一个更偏成员实体，一个更偏关系表达
  - 后续要理解用户识别、权限、组织树，必须把这两个表的职责区分开

## 六、非核心但高频出现的类与方法

### 0. `OrgManager`

- 核心级别：高频支撑，但非常重要
- 使用场景：
  - 根据成员 ID 获取人员对象
  - 根据部门 ID 获取部门对象
  - 根据登录名获取成员
  - 根据角色、岗位、部门、单位取人
  - 判断成员是否属于某个部门、某个部门树、某个域
- 为什么重要：
  - 它是 Seeyon 组织架构读取的标准入口之一
  - 归档中明确提到它内部会利用组织缓存，因此日常读取比直接查 `orgmember` / `orgrelation` 更合适
- 常见获取方式：
  - Spring 注入：`private OrgManager orgManager;`
  - 运行时获取：`(OrgManager) AppContext.getBean("orgManager")`
  - 静态辅助获取：`OrgHelper.getOrgManager()`

### 0.1 `OrgManager` 高频方法

- `getMemberById(Long memberId)`
  - 场景：根据人员 ID 取成员对象
  - 用法：显示姓名、取人员属性、流程中根据 memberId 反查人
  - 备注：归档中出现频率很高

- `getDepartmentById(Long deptId)`
  - 场景：根据部门 ID 取部门对象
  - 用法：显示部门名、查部门归属、组织匹配

- `getMemberByLoginName(String loginName)`
  - 场景：登录态识别、按登录名反查用户
  - 用法：登录、认证、token 相关逻辑

- `getMembersByIds(Collection<Long> memberIds)`
  - 场景：批量取人
  - 用法：替代循环里的 N 次 `getMemberById`
  - 复习重点：这是典型性能优化点

- `getMembersByDepartment(Long deptId)`
  - 场景：查部门下成员
  - 用法：组织统计、选人、部门范围处理

- `getMembersByDeptAndLevel(...)`
  - 场景：按部门和层级查成员
  - 用法：上下级层级筛选、组织树范围处理

- `getMemberRoles()` / `getMemberRolesForSet(...)`
  - 场景：查成员角色
  - 用法：菜单权限、角色判断、权限收敛

- `getMemberPostByMemberIdAndRole(...)`
  - 场景：按成员和角色取岗位关系
  - 用法：组织匹配、流程选人、角色岗位联动

- `getMemberPostByDeptAndRole(...)`
  - 场景：按部门和角色取岗位关系
  - 用法：部门范围权限和选人

- `getMemberPostByAccountAndRole(...)`
  - 场景：按单位和角色取岗位关系
  - 用法：单位级权限计算

- `getMemberPostByPost(...)`
  - 场景：根据岗位查成员岗位关系
  - 用法：岗位选人、岗位权限扩展

- `getDepartmentsByUser(Long userId)`
  - 场景：获取用户所属部门
  - 用法：一人多部门、部门归属分析

- `getChildDepartments(Long deptId, boolean recursive)`
  - 场景：获取子部门
  - 用法：部门树遍历、组织范围扩展

- `getPostById(Long postId)`
  - 场景：岗位 ID 反查岗位对象
  - 用法：岗位名称展示、岗位权限判断

- `getAllAccounts()`
  - 场景：遍历全部单位
  - 用法：多单位统计、全局组织分析

- `getAllUserDomainIDs(Long userId)`
  - 场景：取用户可见组织域
  - 用法：域范围控制、权限判断
  - 备注：归档里专门讨论过它返回不完整的问题

- `isInDepartment(...)`
  - 场景：判断成员是否属于某部门或部门树
  - 用法：权限判断、组织匹配、范围控制

- `isInDepartmentPathOf(parentDeptId, childDeptId)`
  - 场景：判断部门层级关系
  - 用法：组织树路径和上下级关系判断

- `getTeamsByMember(memberId, accountId)`
  - 场景：获取成员所属团队
  - 用法：团队维度权限和组织扩展

### 0.2 `OrgManager` 与 `orgmember` / `orgrelation` 的关系

- `OrgManager`
  - 更偏读取入口和组织能力封装
  - 日常业务层优先通过它取组织数据
- `orgmember`
  - 更偏成员实体数据
  - 适合表达“这个人本身是什么”
- `orgrelation`
  - 更偏关系实体数据
  - 适合表达“这个人和部门/岗位/单位是什么关系”
- 复习结论：
  - 日常业务读取优先 `OrgManager`
  - 组织模型设计分析时再回到底层两张表

### 1. `WorkflowApiManager`

- 核心级别：高频支撑
- 使用场景：
  - 工作流 API 调用
  - 外部系统或业务层调用工作流能力
- 为什么不是最核心：
  - 它很重要，但更多是“工作流能力调用层”，不是某个具体业务场景的总入口

### 2. `GovdocPubManagerImpl`

- 核心级别：高频支撑
- 使用场景：
  - 公文发布、公文公共逻辑
  - 某些文号、权限、公文状态相关处理
- 复习重点：
  - 和 `GovdocManagerImpl` 的职责边界

### 3. `EdocSummaryManagerImpl`

- 核心级别：高频支撑
- 使用场景：
  - 公文摘要对象处理
  - 摘要数据持久化与业务封装
- 复习重点：
  - 不是流程主入口，但经常是流程主入口依赖的业务管理层

### 4. `EdocManagerImpl`

- 核心级别：高频支撑
- 使用场景：
  - edoc 模块综合管理
  - 公文相关业务处理
- 复习重点：
  - 看它与 govdoc 相关 manager 的关系

### 5. `M3StatisticResource.reportPerformance`

- 核心级别：高频支撑
- 使用场景：
  - 前端性能统计上报
  - 页面加载、请求耗时等性能指标记录
- 用法理解：
  - 更偏监控/性能收集，不属于 Seeyon 最核心业务链，但对排障和前端性能治理很有价值

### 6. `CtpLogFactory`

- 核心级别：高频支撑
- 使用场景：
  - 日志工厂
  - 日志对象获取
- 复习重点：
  - Seeyon 日志体系入口之一
  - 适合和 `Log4JConfigurator`、`LogTool` 一起看

### 7. `FormApi4Cap4Impl`

- 核心级别：高频支撑
- 使用场景：
  - CAP4 表单 API
  - 表单建模与数据集成
- 复习重点：
  - 适合作为 CAP4 表单二开和集成入口去看

## 七、基础设施/辅助类

### 日志相关

- `Log4JConfigurator`
  - 用途：日志配置管理
  - 场景：统一日志输出策略、日志框架配置

- `LogTool`
  - 用途：日志工具类
  - 场景：统一日志调用方式

- `ThirdPartyLogger`
  - 用途：第三方开发日志统一出口
  - 场景：不影响原日志体系前提下增加单独日志输出

- `SystemOutRedirector`
  - 用途：把 `System.out` 重定向进日志体系
  - 场景：历史代码 `System.out.println` 太多，想统一纳入日志管理

### 缓存相关

- `GlobalCache`
- `Cache`
- `SeeyonGlobalCache`
- `AbstractCache`
- `CacheFactory`
- `CacheAccessable`
- `RedisOpt`
- `PipelineRedisOpt`
- `RedisHandler`

这些类的共同复习方法：

- 先看抽象接口和工厂
- 再看具体 Redis 实现
- 最后回到业务层看缓存是怎么被调用的

### 基础框架相关

- `BaseController`
  - 控制层基类
- `BasePO`
  - 持久化对象基类
- `AppContext`
  - Spring/应用上下文与 Bean 获取

这些不是业务核心，但如果你要读 Seeyon 框架代码，迟早会遇到。

## 八、Seeyon 相关规范与方法论

这一部分是补你提到的“规范什么的”，不只是代码规范，也包括阅读、设计、排查和配置规范。

### 1. 类职责规范

- Controller：
  - 负责接请求、收参数、做基础校验、返回响应
  - 不要把主要业务逻辑堆在 Controller
- Manager / Service：
  - 负责业务编排
  - 真正的流程推进、状态修改、权限判断通常应在这一层
- Helper / Util：
  - 负责辅助逻辑、工具计算、格式转换
  - 不要把主业务入口藏进工具类
- PO / Domain：
  - 负责承载数据
  - 不要让实体类背过多业务流程逻辑

### 2. 方法阅读规范

- 读一个方法时，不要只看方法体，要同时看：
  - 入参对象代表什么业务上下文
  - 方法是否改状态
  - 方法是否调了工作流/外部接口
  - 方法是否只是在组装数据
- 对大方法建议按四类拆：
  - 主流程逻辑
  - 数据更新逻辑
  - 外围通知/事件逻辑
  - 日志/防御性逻辑

### 3. 接口设计规范

- 先明确接口是谁调用
- 再明确接口是同步操作还是异步触发
- 参数尽量表达业务语义，不只是技术字段
- 返回值要能表达成功、失败和失败原因
- 如果接口会影响流程或业务规则，必须补上调用示例和参数说明

### 4. 文号与表单配置规范

- 文号字段命名要稳定：
  - 发文：`docMark`
  - 联合发文：`docMark2`
  - 收文：`serialNo`
  - 签报：`signMark`
- 文号生成节点权限建议清晰区分：
  - 可编辑：允许生成或修改
  - 只读：允许查看，不允许改
  - 隐藏：节点不展示
- 配置检查顺序建议固定：
  - 表单字段是否存在
  - 字段是否绑定文号定义
  - 节点是否有字段权限
  - 用户是否有文号使用权限
  - 文号定义是否已发布

### 5. 缓存与会话排查规范

- 遇到“数据不存在”时，不要直接判断是数据库没数据
- 建议按这个顺序查：
  - 请求入口是否正确
  - session 是否有效
  - Redis key 是否存在
  - 缓存是否过期
  - 回源数据库逻辑是否正常
- 移动端/H5 问题要单独看：
  - 终端环境
  - token/session 关系
  - 页面上下文是否丢失

### 5.1 尽量不用数据库查询的高效方法

这部分是之前讨论过、也很适合你后面反复用的一套思路：很多 Seeyon 问题一上来不一定要直接查库，先利用缓存、上下文对象、运行时状态去判断，通常更快，也更接近真实执行链路。

- 适用场景：
  - 表单页面报错
  - 移动端/H5 表单打不开
  - token/session 异常
  - 文号、流程、用户上下文已在运行链路中可拿到
  - 想先快速定位，不想一开始就写 SQL

- 为什么这种方式高效：
  - 运行时缓存更接近真实请求现场
  - 很多问题本质是“上下文没拿到”，不是“数据库没数据”
  - 先看缓存和上下文，能更快判断是入口问题、会话问题、缓存问题还是持久层问题

- 推荐顺序：
  1. 先看请求入口对象
  2. 再看 session / token / 当前用户
  3. 再看缓存 key 和缓存值
  4. 最后才回源数据库核实

- 常见可优先利用的对象：
  - `OrgManager`
    - 适合优先读取成员、部门、单位、角色、岗位等组织对象
    - 在很多场景下比直接查 `orgmember` / `orgrelation` 更快、更贴近业务代码
  - `OrgHelper.getOrgManager()`
    - 适合在无法直接注入依赖时快速拿到组织管理器
  - `ConcreteSessionFormDataRedisManagerImpl`
    - 适合先判断表单数据是否还在缓存里
  - `FormDataController`
    - 适合判断请求是否正确进入表单处理链
  - `IndexForMobileController.getToken`
    - 适合判断移动端 token 获取和认证链路
  - `AppContext`
    - 适合获取当前上下文 Bean、用户、环境信息
  - `GlobalCache` / `SeeyonGlobalCache` / `CacheFactory`
    - 适合判断全局缓存或组件缓存是否已命中
  - Redis 相关实现：
    - `RedisOpt`
    - `PipelineRedisOpt`
    - `RedisHandler`
    - 适合看缓存底层是否真的写入、取出、过期

- 在 Seeyon 里什么情况下先查缓存比查库更合理：
  - 根据 memberId、deptId、loginName 拿组织对象时
    - 优先走 `OrgManager`
  - 页面刚提交完就报“数据不存在”
    - 这时优先怀疑 session/缓存，不优先怀疑数据库
  - 移动端/H5 页面中断后重新进入异常
    - 这时优先怀疑 token、session、上下文续接
  - 表单临时态数据丢失
    - 这时优先看 Redis/会话缓存
  - 某些规则、权限、上下文在运行时已经装载
    - 这时优先看内存对象和缓存对象，不一定要先查底表

- 典型方法论：
  - 组织架构问题：
    - 先看 `OrgManager`
    - 再看 `OrgHelper.getOrgManager()`
    - 最后才分析 `orgmember` / `orgrelation`
  - 表单问题：
    - 先看 `FormDataController`
    - 再看 `ConcreteSessionFormDataRedisManagerImpl`
    - 再判断是否需要查表单定义表或业务数据表
  - 登录/下线问题：
    - 先看 token/session/current user
    - 再看 `orgmember` / `orgrelation` 这类组织模型数据
  - 工作流/公文处理问题：
    - 先看方法入参对象，比如 `GovdocDealVO`
    - 再看流程处理中已经带入的 summary、handleType、上下文状态
    - 最后才查历史表、记录表
  - 文号问题：
    - 先看当前流程上下文、节点权限、表单字段绑定
    - 再查 `GOVDOC_MARK_RECORD` / `EDOC_MARK_HISTORY`

- 这种方法的好处：
  - 更接近代码真实执行路径
  - 更适合快速排查线上现象
  - 可以减少大量低价值 SQL 试探
  - 更容易区分“没取到”和“根本没有”

- 风险和边界：
  - 缓存只能说明“当前运行态看到什么”，不能永远替代数据库
  - 如果问题涉及最终一致性、历史记录、统计分析，还是必须回到数据库
  - 如果缓存已过期、已污染、已失效，只看缓存会误判

- 实战判断准则：
  - 先查缓存：
    - 当前请求现场问题
    - 临时态数据问题
    - 会话态问题
    - 移动端上下文问题
  - 先查数据库：
    - 历史记录问题
    - 统计报表问题
    - 文号重复、历史追踪、全量分析
    - 需要确认最终落库结果的问题

- 一句话记忆：
  - 运行时问题先看缓存和上下文，历史和统计问题再看数据库。

### 5.2 OrgManager 使用规范

- 日常读取组织对象优先：
  - `OrgManager`
- 批量读取优先：
  - `getMembersByIds(...)`
  - 不要循环里多次 `getMemberById(...)`
- 推荐获取方式顺序：
  - 优先 Spring 注入
  - 其次 `AppContext.getBean("orgManager")`
  - 再次 `OrgHelper.getOrgManager()`
- 不建议直接查底表的场景：
  - 只想拿用户姓名、部门名称、岗位名称
  - 只想判断成员是否在某部门或某部门树
  - 只想判断用户角色和组织范围
- 需要回到底层表或 Direct 层的场景：
  - 分析 `orgmember` / `orgrelation` 双表设计
  - 排查组织数据更新不一致
  - 研究 `OrgManagerDirectImpl.updateMembers(...)` 这类底层同步逻辑

### 6. 日志规范

- 不建议继续扩散 `System.out.println`
- 方法入口、出口、异常、关键状态变化建议日志分层：
  - DEBUG：方法入口/出口、参数
  - INFO：关键业务动作
  - WARN：可恢复异常、配置异常
  - ERROR：真正失败和影响流程的错误
- 日志必须带业务上下文：
  - 用户
  - 模板/流程/事项 ID
  - 节点
  - 关键参数

### 7. 性能与监控规范

- 前端性能统计接口不要只记录总耗时
- 建议最少拆：
  - 页面加载耗时
  - 请求耗时
  - 渲染耗时
  - 用户/表单/模板信息
- 性能日志最好单独模型化，而不是直接拼普通日志文本

### 8. 复习规范

- 复习一个专题时，至少同时记住三样东西：
  - 入口类/方法
  - 关键表/对象
  - 典型场景
- 不要只背类名，要能说出：
  - 这个类处于哪一层
  - 它解决什么问题
  - 它和谁配合
  - 它为什么算核心或非核心

## 九、按学习目标拆分的阅读路线

### 路线 A：想搞懂公文与流程

1. `GovdocManagerImpl.transFinishWorkItemPublic`
2. `WorkflowApiManager`
3. `GovdocPubManagerImpl`
4. `EdocSummaryManagerImpl`
5. 文号链：`GovdocMarkManagerImpl` / `GovdocMarkHelper` / `EdocMarkUtil`
6. 表：`GOVDOC_MARK_RECORD` / `EDOC_MARK_HISTORY`

### 路线 B：想搞懂移动端登录与表单异常

1. `IndexForMobileController.getToken`
2. `IndexForMobileController.mobileAllSendDone`
3. `FormDataController`
4. `ConcreteSessionFormDataRedisManagerImpl`
5. `summary.getDeadlineDatetime()`

### 路线 C：想搞懂规则配置与接口调用

1. `POST /rest/bpm/process/start`
2. `WorkTimeSetController.setCurrencyWorkTime`
3. `FormApi4Cap4Impl`
4. `orgmember` / `orgrelation`

### 路线 D：想搞懂日志、监控和基础设施

1. `CtpLogFactory`
2. `Log4JConfigurator`
3. `LogTool`
4. `ThirdPartyLogger`
5. `SystemOutRedirector`
6. `M3StatisticResource.reportPerformance`

## 十、核心与非核心的区分方法

判断一个类/方法是不是“核心”，你可以用下面这套标准：

### 核心对象的特征

- 它是入口
- 它决定流程是否继续
- 它决定业务状态是否变化
- 它同时连接多个模块
- 它出问题会直接影响主要业务流程

### 非核心对象的特征

- 它更多是辅助、工具、封装、日志、配置
- 它通常不会单独决定业务主流程
- 它的重要性来自“支撑”，不是“主导”

### 举例

- `transFinishWorkItemPublic`：核心，因为它驱动公文处理主流程
- `setCurrencyWorkTime`：核心，因为它直接改变业务规则的运行时效果
- `CtpLogFactory`：非业务核心，但基础设施层高频支撑
- `LogTool`：非核心，它更偏工具封装

## 十一、复习时最容易犯的错误

- 把工具类当主流程入口看
- 把表记录类当业务逻辑类看
- 只记接口 URL，不记实现层和参数语义
- 只记某个方法名，不记它在整个调用链里的位置
- 只记“修复方案”，不记“为什么会这样设计”

## 十二、最后的复习建议

- 第一轮只记住“入口类、核心方法、关键表”
- 第二轮补“调用链、状态变化、配置入口”
- 第三轮再补“辅助类、工具类、日志类”

如果后续继续扩展这份手册，最值得补充的是：

1. 每个核心类对应的真实源码文件路径
2. 每个核心方法的上下游调用链
3. 每个关键表对应的字段说明
4. 每个接口对应的请求参数和返回结构
