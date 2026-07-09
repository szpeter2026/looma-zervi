# 鸿蒙适配技术验证清单

> **版本：** 1.0 · **日期：** 2026-07-07  
> **状态：** 🔍 待验证  
> **用途：** 验证技术可行性，为正式开发做准备

---

## 1. 环境搭建验证

### 1.1 开发工具安装
- [ ] **DevEco Studio**：下载并安装最新版
  - 版本：建议 4.0+
  - 安装路径：无中文和空格
  - 组件：Node.js、HarmonyOS SDK、模拟器

- [ ] **Node.js 环境**
  - 版本：16.x 或 18.x
  - 验证：`node --version`、`npm --version`

- [ ] **Git 配置**
  - 验证：`git --version`
  - 配置：用户名、邮箱、SSH密钥

### 1.2 项目创建验证
- [ ] **创建新项目**
  - 项目类型：Empty Ability（API 9+）
  - 模板：Empty Ability Template
  - 项目名称：LoomaHarmonyTest
  - 包名：com.looma.harmony.test

- [ ] **项目结构验证**
  ```bash
  LoomaHarmonyTest/
  ├── entry/
  │   ├── src/main/
  │   │   ├── ets/
  │   │   │   ├── entryability/
  │   │   │   ├── pages/
  │   │   │   └── utils/
  │   │   ├── resources/
  │   │   └── module.json5
  ├── build/
  └── oh-package.json5
  ```

- [ ] **编译运行验证**
  - 编译：Build → Build Hap(s)
  - 运行：Run 'entry'
  - 预期：在模拟器中看到 "Hello World"

---

## 2. TypeScript/ArkTS 兼容性验证

### 2.1 shared-core 基础兼容性
- [ ] **复制 shared-core 到鸿蒙项目**
  ```bash
  # 从现有项目复制
  cp -r frontend/packages/shared-core harmony/entry/src/main/ets/shared-core
  ```

- [ ] **验证 TypeScript 编译**
  - 修改 `tsconfig.json` 配置
  - 编译检查：`npm run build` 或 `tsc --noEmit`
  - 预期：无编译错误（允许少量警告）

### 2.2 关键模块兼容性测试
- [ ] **数据模型模块** (`src/types/`)
  ```typescript
  // 测试文件：test-types.ets
  import { User, GameProfile, QuizAnswer } from '../shared-core/src/types'
  
  // 验证类型定义
  const user: User = {
    id: 'test-id',
    email: 'test@example.com',
    tier: 'free'
  }
  
  console.log('TypeScript类型验证通过:', user)
  ```

- [ ] **工具函数模块** (`src/utils/`)
  ```typescript
  // 测试文件：test-utils.ets
  import { formatDate, validateEmail } from '../shared-core/src/utils'
  
  const date = formatDate(new Date())
  const isValid = validateEmail('test@example.com')
  
  console.log('工具函数验证通过:', { date, isValid })
  ```

- [ ] **API 接口模块** (`src/api/`)
  ```typescript
  // 测试文件：test-api-types.ets
  import { ApiResponse, AskRequest, AuthRequest } from '../shared-core/src/api/types'
  
  const askReq: AskRequest = {
    question: '测试问题',
    context: '测试上下文'
  }
  
  console.log('API接口类型验证通过:', askReq)
  ```

---

## 3. 平台API适配验证

### 3.1 网络请求适配
- [ ] **创建网络适配器原型**
  ```typescript
  // platform-adapter.ets
  export interface NetworkAdapter {
    request(url: string, options: RequestOptions): Promise<Response>
    get(url: string, params?: Record<string, any>): Promise<Response>
    post(url: string, data?: any): Promise<Response>
  }
  
  // harmony-network.ets
  import http from '@ohos.net.http'
  
  export class HarmonyNetworkAdapter implements NetworkAdapter {
    async request(url: string, options: RequestOptions): Promise<Response> {
      const httpRequest = http.createHttp()
      return new Promise((resolve, reject) => {
        httpRequest.request(url, {
          method: options.method === 'GET' ? http.RequestMethod.GET : http.RequestMethod.POST,
          header: options.headers,
          extraData: options.body
        }, (err, data) => {
          if (err) reject(err)
          else resolve({
            ok: data.responseCode === 200,
            status: data.responseCode,
            json: () => Promise.resolve(JSON.parse(data.result as string))
          })
        })
      })
    }
  }
  ```

- [ ] **测试网络请求**
  ```typescript
  // test-network.ets
  const adapter = new HarmonyNetworkAdapter()
  const response = await adapter.get('https://jsonplaceholder.typicode.com/todos/1')
  const data = await response.json()
  
  console.log('网络请求验证通过:', data)
  ```

### 3.2 存储适配验证
- [ ] **创建存储适配器**
  ```typescript
  // storage-adapter.ets
  export interface StorageAdapter {
    get(key: string): Promise<any>
    set(key: string, value: any): Promise<void>
    remove(key: string): Promise<void>
    clear(): Promise<void>
  }
  
  // harmony-storage.ets
  import preferences from '@ohos.data.preferences'
  
  export class HarmonyStorageAdapter implements StorageAdapter {
    private pref: preferences.Preferences | null = null
    
    async init(): Promise<void> {
      const context = getContext(this)
      this.pref = await preferences.getPreferences(context, 'looma_storage')
    }
    
    async get(key: string): Promise<any> {
      if (!this.pref) await this.init()
      return this.pref?.get(key, '')
    }
    
    async set(key: string, value: any): Promise<void> {
      if (!this.pref) await this.init()
      await this.pref?.put(key, value)
      await this.pref?.flush()
    }
  }
  ```

- [ ] **测试存储功能**
  ```typescript
  // test-storage.ets
  const storage = new HarmonyStorageAdapter()
  await storage.set('test_key', 'test_value')
  const value = await storage.get('test_key')
  
  console.log('存储功能验证通过:', value === 'test_value')
  ```

---

## 4. 认证流程验证

### 4.1 华为帐号登录研究
- [ ] **查阅官方文档**
  - [华为帐号服务文档](https://developer.huawei.com/consumer/cn/doc/development/HMSCore-Guides/introduction-0000001050048870)
  - OAuth 2.0 授权流程
  - 获取用户信息接口

- [ ] **创建开发者账号**
  - 注册华为开发者账号
  - 创建应用，获取 App ID
  - 配置 OAuth 回调地址

- [ ] **后端认证接口验证**
  ```typescript
  // 验证现有后端是否支持多认证提供商
  // 检查 backend/src/api/auth/wechat_auth.py
  
  // 需要确认：
  // 1. 是否已有通用认证接口
  // 2. 是否支持华为OAuth
  // 3. 用户数据映射方案
  ```

### 4.2 认证适配器原型
- [ ] **设计认证接口**
  ```typescript
  // auth-adapter.ets
  export interface AuthAdapter {
    login(): Promise<AuthResult>
    logout(): Promise<void>
    getCurrentUser(): Promise<User | null>
    isAuthenticated(): Promise<boolean>
  }
  
  export interface AuthResult {
    success: boolean
    token?: string
    user?: User
    error?: string
  }
  ```

- [ ] **华为认证实现（占位）**
  ```typescript
  // harmony-auth.ets
  export class HarmonyAuthAdapter implements AuthAdapter {
    async login(): Promise<AuthResult> {
      // TODO: 实现华为帐号登录
      // 1. 调用华为登录SDK
      // 2. 获取授权码
      // 3. 调用后端接口交换token
      
      return {
        success: false,
        error: '华为登录暂未实现'
      }
    }
  }
  ```

---

## 5. UI框架验证

### 5.1 ArkUI 基础组件验证
- [ ] **创建基础组件示例**
  ```typescript
  // components/looma-button.ets
  @Component
  export struct LoomaButton {
    @Prop text: string = ''
    @Prop type: 'primary' | 'secondary' = 'primary'
    @Prop disabled: boolean = false
    @Emit onClick: () => void = () => {}
    
    build() {
      Button(this.text)
        .type(ButtonType.Capsule)
        .backgroundColor(this.getBackgroundColor())
        .enabled(!this.disabled)
        .onClick(() => this.onClick())
    }
    
    private getBackgroundColor(): ResourceColor {
      return this.type === 'primary' ? '#007AFF' : '#F2F2F7'
    }
  }
  ```

- [ ] **测试组件使用**
  ```typescript
  // test-components.ets
  @Entry
  @Component
  struct TestPage {
    build() {
      Column({ space: 20 }) {
        LoomaButton({ text: '主要按钮', type: 'primary' })
        LoomaButton({ text: '次要按钮', type: 'secondary' })
        LoomaButton({ text: '禁用按钮', disabled: true })
      }
      .width('100%')
      .height('100%')
      .justifyContent(FlexAlign.Center)
    }
  }
  ```

### 5.2 页面布局验证
- [ ] **创建简单页面布局**
  ```typescript
  // pages/login-page.ets
  @Entry
  @Component
  struct LoginPage {
    @State username: string = ''
    @State password: string = ''
    
    build() {
      Column({ space: 20 }) {
        // 标题
        Text('Looma 登录')
          .fontSize(24)
          .fontWeight(FontWeight.Bold)
        
        // 输入框
        TextInput({ placeholder: '用户名/邮箱' })
          .width('80%')
          .onChange((value: string) => {
            this.username = value
          })
        
        TextInput({ placeholder: '密码', type: InputType.Password })
          .width('80%')
          .onChange((value: string) => {
            this.password = value
          })
        
        // 登录按钮
        LoomaButton({ 
          text: '登录',
          type: 'primary',
          disabled: !this.username || !this.password
        })
      }
      .width('100%')
      .height('100%')
      .justifyContent(FlexAlign.Center)
    }
  }
  ```

---

## 6. 构建与部署验证

### 6.1 构建配置验证
- [ ] **检查构建配置文件**
  - `build-profile.json5`：构建配置
  - `oh-package.json5`：依赖管理
  - `module.json5`：模块配置

- [ ] **添加依赖包**
  ```json5
  // oh-package.json5
  {
    "license": "ISC",
    "devDependencies": {
      "@types/node": "^20.0.0",
      "typescript": "^5.0.0"
    },
    "dependencies": {
      "@ohos/net.http": "^1.0.0",
      "@ohos/data.preferences": "^1.0.0"
    }
  }
  ```

### 6.2 打包验证
- [ ] **生成 HAP 包**
  ```bash
  # 在 DevEco Studio 中
  Build → Build Hap(s) → Release
  
  # 或在命令行
  npm run build
  ```

- [ ] **验证包结构**
  ```
  build/outputs/default/
  ├── entry-default-unsigned.hap
  ├── entry-default-signed.hap
  └── jsbundle/
  ```

- [ ] **安装测试**
  ```bash
  # 使用 hdc 工具安装到设备
  hdc install entry-default-signed.hap
  
  # 验证安装
  hdc shell bm dump -a | grep looma
  ```

---

## 7. 测试验证

### 7.1 单元测试验证
- [ ] **设置测试框架**
  ```json5
  // oh-package.json5
  {
    "scripts": {
      "test": "hdc shell aa test -p com.looma.harmony.test -s unittest"
    }
  }
  ```

- [ ] **编写简单测试**
  ```typescript
  // test/unit/test-utils.test.ets
  import { describe, it, expect } from '@ohos/hypium'
  import { validateEmail } from '../../shared-core/src/utils'
  
  @Suite
  class UtilsTest {
    @Test
    validateEmailTest() {
      expect(validateEmail('test@example.com')).assertTrue()
      expect(validateEmail('invalid-email')).assertFalse()
    }
  }
  ```

### 7.2 功能测试验证
- [ ] **创建端到端测试**
  ```typescript
  // test/e2e/login-flow.test.ets
  import { by, device, element, expect } from 'detox-harmony'
  
  describe('登录流程', () => {
    beforeEach(async () => {
      await device.reloadReactNative()
    })
    
    it('应该显示登录页面', async () => {
      await expect(element(by.text('Looma 登录'))).toBeVisible()
    })
    
    it('应该可以输入用户名密码', async () => {
      await element(by.placeholder('用户名/邮箱')).typeText('test@example.com')
      await element(by.placeholder('密码')).typeText('password123')
      
      await expect(element(by.text('登录'))).toBeVisible()
    })
  })
  ```

---

## 8. 验证结果汇总

### 8.1 通过标准
- [ ] **环境搭建**：DevEco Studio 正常运行 Hello World
- [ ] **TypeScript兼容**：shared-core 核心模块编译通过
- [ ] **网络请求**：能够成功调用外部API
- [ ] **本地存储**：能够读写本地数据
- [ ] **UI组件**：能够创建和使用自定义组件
- [ ] **构建部署**：能够生成和安装 HAP 包
- [ ] **测试框架**：能够运行单元测试

### 8.2 风险评估
| 验证项 | 通过 | 部分通过 | 未通过 | 风险等级 |
|--------|------|----------|--------|----------|
| TypeScript兼容性 | ☐ | ☐ | ☐ | 高 |
| 网络请求适配 | ☐ | ☐ | ☐ | 中 |
| 华为认证集成 | ☐ | ☐ | ☐ | 高 |
| UI框架迁移 | ☐ | ☐ | ☐ | 中 |
| 构建部署流程 | ☐ | ☐ | ☐ | 低 |

### 8.3 建议与下一步
**如果全部通过**：
- 开始正式开发，按执行计划推进
- 重点关注华为认证集成细节

**如果部分通过**：
- 针对未通过项进行深入调研
- 考虑替代方案或调整技术栈
- 重新评估项目可行性

**如果大部分未通过**：
- 暂停项目，重新评估技术选型
- 考虑其他跨平台方案
- 或者专注于微信小程序优化

---

## 📋 验证记录

| 日期 | 验证人 | 验证项目 | 结果 | 备注 |
|------|--------|----------|------|------|
| | | 环境搭建 | ☐ | |
| | | TypeScript兼容 | ☐ | |
| | | 网络请求 | ☐ | |
| | | 存储适配 | ☐ | |
| | | UI组件 | ☐ | |
| | | 构建部署 | ☐ | |
| | | 测试框架 | ☐ | |

**总体结论**：☐ 建议继续 ☐ 需要调整 ☐ 建议暂停

---

**文档状态**：🔍 待验证 · 📋 可操作 · ⚠️ 高风险项需重点关注

**完成验证后**：填写验证记录，更新风险评估，制定下一步计划。