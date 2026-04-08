# 历史对话涉及的 Java / JSP / JS 文件清单

生成时间：2026-04-09

说明：

- 这份清单基于当前 `txt/` 历史对话提取整理。
- 我没有把所有零碎命中都直接列出来，而是做了去噪，只保留反复出现、讨论较多、明显有业务价值的类和文件。
- 重点偏向 Seeyon 相关内容，因为历史讨论里这部分占比最高。

## 一、Java 类清单

### 1. 登录、会话、在线状态

- `MainController.java`
  - 用途：登录主入口控制器之一，处理登录流程、跳转和相关请求。
  - 典型场景：登录入口分析、主页面跳转、认证前后处理。

- `OnlineRecorder.java`
  - 用途：在线状态记录。
  - 典型场景：用户上线、在线状态同步、在线记录分析。

- `OnlineManagerImpl.java`
  - 用途：在线用户管理实现。
  - 典型场景：用户在线状态维护、在线会话分析、上下线逻辑。

- `CurrentUserToSeeyonApp.java`
  - 用途：当前用户和 Seeyon 应用上下文转换。
  - 典型场景：登录态、当前用户识别、应用层上下文绑定。

- `LoginTokenManagerImpl.java`
  - 用途：登录 token 管理。
  - 典型场景：token 获取、token 生命周期、移动端登录态排查。

- `M3LoginResource.java`
  - 用途：M3/移动端登录资源入口。
  - 典型场景：移动端登录、认证链路排查。

- `SSOLoginServlet.java`
  - 用途：SSO 登录入口。
  - 典型场景：单点登录、SSO 跳转与认证。

- `SSOTicketLoginAuthentication.java`
  - 用途：SSO ticket 认证实现。
  - 典型场景：SSO 票据校验、单点登录认证。

- `SSOTicketManager.java`
  - 用途：SSO ticket 管理。
  - 典型场景：票据分发、票据校验、SSO 状态流转。

- `LoginControlImpl.java`
  - 用途：登录控制实现。
  - 典型场景：登录流程控制、登录限制、会话管理。

- `SessionExpiringMap.java`
  - 用途：带过期能力的 session 映射。
  - 典型场景：session 生命周期、过期控制、登录态问题。

- `MapSession.java`
  - 用途：session 数据结构封装。
  - 典型场景：session 存储、会话对象管理。

- `CTPSessionRepository.java`
  - 用途：CTP session 仓储。
  - 典型场景：session 持久化、会话管理实现。

### 2. 组织架构与用户权限

- `OrgManager.java`
  - 用途：组织架构读取标准入口。
  - 典型场景：根据成员、部门、岗位、单位取组织对象；权限判断；组织范围计算。

- `OrgManagerImpl.java`
  - 用途：`OrgManager` 的实现类。
  - 典型场景：组织架构能力实现、缓存读取、组织查询。

- `OrgManagerDirectImpl.java`
  - 用途：组织数据更底层的直接实现。
  - 典型场景：组织数据更新、双表同步、`orgmember/orgrelation` 设计分析。

- `OrgHelper.java`
  - 用途：组织架构静态辅助入口。
  - 典型场景：无法直接注入 `OrgManager` 时快速获取组织管理器。

### 3. 公文、流程、文号

- `GovdocManagerImpl.java`
  - 用途：公文核心业务管理实现。
  - 典型场景：`transFinishWorkItemPublic`、已阅逻辑、流程节点处理。

- `ColPubManagerImpl.java`
  - 用途：协同/公文公共管理逻辑。
  - 典型场景：公文公共逻辑、流程状态联动。

- `ColManagerImpl.java`
  - 用途：协同管理实现。
  - 典型场景：协同流程、公文/协同公共流程分析。

- `WorkflowApiManager.java`
  - 用途：工作流 API 能力入口。
  - 典型场景：流程发起、流程推进、业务调用工作流。

- `WorkflowInnerApiManagerImpl.java`
  - 用途：工作流内部 API 实现。
  - 典型场景：流程引擎内部调用链分析。

- `ProcessManager.java`
  - 用途：流程管理。
  - 典型场景：流程节点处理、流程对象管理。

- `GovdocMarkRecord.java`
  - 用途：公文文号记录实体。
  - 典型场景：文号当前记录、文号状态分析。

- `GovdocMarkManagerImpl.java`
  - 用途：文号管理实现。
  - 典型场景：文号生成、保存、历史记录联动。

- `EdocSummary.java`
  - 用途：公文摘要领域对象。
  - 典型场景：截止时间、文号、业务上下文承载。

- `EdocHelper.java`
  - 用途：公文辅助工具。
  - 典型场景：edoc 公共辅助逻辑。

### 4. 表单、CAP4、移动端

- `FormDataController.java`
  - 用途：表单数据入口控制器/服务入口。
  - 典型场景：表单数据获取、移动端/H5 表单报错分析。

- `ConcreteSessionFormDataRedisManagerImpl.java`
  - 用途：表单 session + Redis 缓存实现。
  - 典型场景：表单缓存、会话态表单数据丢失排查。

- `FormBean.java`
  - 用途：CAP4 表单定义对象。
  - 典型场景：表单结构理解、CAP4 表单建模。

- `FormManager.java`
  - 用途：表单管理。
  - 典型场景：表单业务处理、表单定义管理。

- `FormApi4Cap4Impl.java`
  - 用途：CAP4 表单 API 实现。
  - 典型场景：CAP4 集成、表单开放能力调用。

- `IndexForMobileController.java`
  - 用途：移动端控制器。
  - 典型场景：`getToken`、`mobileAllSendDone`、移动端登录和业务入口分析。

### 5. 菜单、权限、门户

- `MenuManager.java`
  - 用途：菜单管理接口。
  - 典型场景：菜单读取、权限菜单分析。

- `MenuManagerImpl.java`
  - 用途：菜单管理实现。
  - 典型场景：菜单权限、菜单缓存、菜单加载流程。

- `MenuController.java`
  - 用途：菜单相关控制器。
  - 典型场景：菜单配置后台页面逻辑。

- `PrivMenu.java`
  - 用途：菜单实体。
  - 典型场景：菜单定义、资源挂接、导航配置。

- `PrivRoleMenu.java`
  - 用途：角色与菜单关系实体。
  - 典型场景：权限继承、菜单授权、角色菜单映射。

- `PrivilegeCache.java`
  - 用途：权限缓存。
  - 典型场景：菜单权限缓存、权限加速。

- `PortalMenuManager.java`
  - 用途：门户菜单管理。
  - 典型场景：门户导航菜单、门户菜单配置。

### 6. 日志、性能、缓存、基础设施

- `CtpLogFactory.java`
  - 用途：日志工厂。
  - 典型场景：统一获取日志对象、日志体系整理。

- `Log4JConfigurator.java`
  - 用途：日志配置管理。
  - 典型场景：日志文件、Appender、格式配置。

- `LogTool.java`
  - 用途：日志工具类。
  - 典型场景：统一日志调用方式。

- `ThirdPartyLogger.java`
  - 用途：第三方开发日志统一出口。
  - 典型场景：扩展日志文件、不影响原体系。

- `SystemOutRedirector.java`
  - 用途：把 `System.out` 纳入日志体系。
  - 典型场景：历史代码日志治理。

- `M3StatisticResource.java`
  - 用途：性能统计 REST 资源。
  - 典型场景：前端性能统计上报、页面耗时采集。

- `UserPerformanceLog.java`
  - 用途：性能日志对象。
  - 典型场景：性能数据结构建模。

- `UserPerformanceLogDao.java` / `UserPerformanceLogDaoImpl.java`
  - 用途：性能日志 DAO。
  - 典型场景：性能日志落库。

- `UserPerformanceLogManager.java` / `UserPerformanceLogManagerImpl.java`
  - 用途：性能日志管理层。
  - 典型场景：性能日志业务处理。

- `FePerformanceManagerImpl.java`
  - 用途：前端性能管理实现。
  - 典型场景：性能统计、性能治理。

- `RedisUtils.java`
  - 用途：Redis 工具类。
  - 典型场景：缓存处理、Redis 操作封装。

- `RedisAccessJedis.java`
  - 用途：Jedis 访问封装。
  - 典型场景：Redis 访问实现。

- `AppContext.java`
  - 用途：应用上下文入口。
  - 典型场景：运行时取 Bean、上下文对象获取。

## 二、JSP 文件清单

### 1. 登录、主页、心跳

- `index.jsp`
  - 用途：系统首页或入口页。
  - 典型场景：登录后入口、首页跳转。

- `login.jsp`
  - 用途：登录页。
  - 典型场景：认证入口、登录界面问题。

- `main.jsp`
  - 用途：主框架页。
  - 典型场景：登录后主容器、页面框架。

- `sessionHeartbeat.jsp`
  - 用途：session 心跳维持页面。
  - 典型场景：会话保活、心跳机制、登录失效排查。

### 2. 公文与协同

- `newEdoc.jsp`
  - 用途：新建公文页面。
  - 典型场景：公文创建、表单新建入口。

- `newGovdoc.jsp`
  - 用途：新建公文页面。
  - 典型场景：govdoc 新建、流程发起。

- `edocHeader.jsp`
  - 用途：公文头部区域。
  - 典型场景：公文页面结构、头部字段显示。

- `govdocBody.jsp`
  - 用途：公文正文相关 JSP。
  - 典型场景：公文正文展示、表单正文联动。

- `stepBackToDialog.jsp`
  - 用途：回退/指定回退相关对话框。
  - 典型场景：流程回退、指定回退界面。

- `settingSpecifiesReturn.jsp`
  - 用途：指定回退设置页面。
  - 典型场景：流程退回、指定返回配置。

### 3. 门户、菜单、权限

- `menuList.jsp`
  - 用途：菜单列表页。
  - 典型场景：菜单配置、菜单管理。

- `menuNew.jsp`
  - 用途：菜单新建页。
  - 典型场景：新建菜单资源。

- `menuVersion.jsp`
  - 用途：菜单版本页。
  - 典型场景：菜单版本差异、版本配置。

- `resourceTree.jsp`
  - 用途：资源树页面。
  - 典型场景：资源树、菜单资源绑定。

- `sysMenuSortSetting.jsp`
  - 用途：系统菜单排序配置页。
  - 典型场景：门户/系统菜单排序。

- `navigationMenu.jsp`
  - 用途：导航菜单页面。
  - 典型场景：门户导航展示。

- `portletSelector.jsp`
  - 用途：Portlet 选择器。
  - 典型场景：门户版块选择、门户定制。

- `sectionPropertySetting.jsp`
  - 用途：栏目属性设置页。
  - 典型场景：门户栏目配置。

### 4. 其他高频页面

- `upload.jsp`
  - 用途：上传页面。
  - 典型场景：文件上传、附件上传。

- `common_header.jsp`
  - 用途：公共头部。
  - 典型场景：公共布局、头部资源引入。

- `header_js.jsp`
  - 用途：头部 JS 引入页。
  - 典型场景：公共脚本装配。

- `bulIndex.jsp`
  - 用途：公告首页。
  - 典型场景：公告模块展示。

- `edocTopicAIP.jsp`
  - 用途：公文相关主题/AIP 页面。
  - 典型场景：公文专题页面。

## 三、JS 文件清单

### 1. 公共框架与基础脚本

- `V3X.js`
  - 用途：Seeyon 常见公共前端脚本。
  - 典型场景：前端基础能力、公共方法、老前端框架能力。

- `front_common.js`
  - 用途：门户前端公共脚本。
  - 典型场景：门户页面、布局、前端通用逻辑。

- `jquery.comp-debug.js`
  - 用途：前端组件调试版脚本。
  - 典型场景：组件行为分析、前端调试。

- `jquery.comp.js`
  - 用途：前端组件正式版脚本。
  - 典型场景：基础 UI 组件。

### 2. 在线消息、心跳、登录

- `onlinemessage.js`
  - 用途：在线消息脚本。
  - 典型场景：在线通知、在线消息、消息提醒。

- `sessionHeartbeat.js`
  - 用途：session 心跳相关脚本。
  - 典型场景：会话保活、心跳检测。

- `login.js`
  - 用途：登录相关脚本。
  - 典型场景：前端登录动作、登录页交互。

- `lightweightsso.js`
  - 用途：轻量级 SSO 相关脚本。
  - 典型场景：轻量单点登录前端处理。

- `colsso.js`
  - 用途：协同/SSO 相关脚本。
  - 典型场景：单点登录与协同页面联动。

### 3. 公文与协同前端

- `newEdoc.js`
  - 用途：新建公文前端逻辑。
  - 典型场景：公文创建、表单初始化、页面交互。

- `newGovdoc.js`
  - 用途：新建 govdoc 前端逻辑。
  - 典型场景：新建公文页面交互。

- `edoc.js`
  - 用途：公文模块前端脚本。
  - 典型场景：公文页面行为、表单交互。

- `edocHeader.js`
  - 用途：公文头部前端逻辑。
  - 典型场景：头部区域交互、字段展示。

- `settingSpecifiesReturn.js`
  - 用途：指定回退设置前端脚本。
  - 典型场景：流程回退设置页面。

- `stepBackToDialog.js`
  - 用途：回退对话框脚本。
  - 典型场景：流程退回交互。

### 4. 门户与菜单前端

- `section.js`
  - 用途：栏目/版块脚本。
  - 典型场景：门户栏目、版块展示。

- `portalSectionHander.js`
  - 用途：门户版块处理脚本。
  - 典型场景：门户版块操作与管理。

- `bulIndex.js`
  - 用途：公告首页脚本。
  - 典型场景：公告展示页逻辑。

- `bulEdit.js`
  - 用途：公告编辑脚本。
  - 典型场景：公告编辑。

- `bulView.js`
  - 用途：公告查看脚本。
  - 典型场景：公告详情查看。

### 5. Office、上传与附件

- `createOcx.js`
  - 用途：Office/OCX 相关前端脚本。
  - 典型场景：本地控件、Office 集成。

- `upload.js`
  - 用途：上传脚本。
  - 典型场景：附件上传、文件上传。

- `baseOffice.js`
  - 用途：Office 基础脚本。
  - 典型场景：Office 控件交互。

### 6. 其他说明

- 历史对话里还出现了很多通用或非 Seeyon 文件，例如：
  - `index.js`
  - `api.js`
  - `machines.js`
  - `config.js`
  - `response.js`
- 这些里有一部分来自其他项目、CLI 工具、示例代码或对话上下文，不适合和 Seeyon 主体文件混在一起记忆。
- 所以这份清单优先保留了 Seeyon 相关和明确有业务价值的项。

## 四、怎么复习这份清单

### 路线 A：想搞懂 Seeyon 后端

1. 先看登录与组织架构：
  - `MainController.java`
  - `CurrentUserToSeeyonApp.java`
  - `OrgManager.java`
2. 再看流程与公文：
  - `GovdocManagerImpl.java`
  - `WorkflowApiManager.java`
  - `ProcessManager.java`
3. 最后看文号与表单：
  - `GovdocMarkManagerImpl.java`
  - `EdocSummary.java`
  - `FormDataController.java`

### 路线 B：想搞懂前端页面

1. 公共脚本：
  - `V3X.js`
  - `front_common.js`
2. 在线与登录：
  - `onlinemessage.js`
  - `sessionHeartbeat.js`
  - `login.js`
3. 公文页面：
  - `newEdoc.jsp`
  - `newEdoc.js`
  - `govdocBody.jsp`
  - `newGovdoc.jsp`

### 路线 C：想搞懂菜单与权限

1. `MenuManager.java`
2. `MenuManagerImpl.java`
3. `PrivMenu.java`
4. `PrivRoleMenu.java`
5. `PrivilegeCache.java`
6. `menuList.jsp` / `menuNew.jsp` / `resourceTree.jsp`

## 五、总结

- Java 类里，历史对话最集中的是：
  - 登录与会话
  - 组织架构
  - 公文流程
  - 文号
  - 表单缓存
  - 菜单权限
  - 日志与性能

- JSP 里，历史对话最集中的是：
  - 登录页
  - 公文页面
  - 门户菜单配置页
  - 上传页

- JS 里，历史对话最集中的是：
  - `V3X.js`
  - `front_common.js`
  - `onlinemessage.js`
  - `newEdoc.js`
  - `newGovdoc.js`
  - `createOcx.js`
  - `sessionHeartbeat.js`

