三种方式最终都会调用 Claude 模型 API，区别不在“用不用 Claude”，而在于：

> Agent 循环、工具执行、上下文管理和权限控制由谁负责。

## 核心对比

| 对比项 | Claude Agent SDK | Anthropic SDK + Tool Runner | Anthropic SDK + 手动 Agent Loop |
|---|---|---|---|
| npm 包 | `@anthropic-ai/claude-agent-sdk` | `@anthropic-ai/sdk` | `@anthropic-ai/sdk` |
| 定位 | 完整 Agent Runtime | 自动工具循环助手 | Claude API 客户端 |
| 模型调用 | SDK负责 | SDK负责 | SDK负责通信，你控制调用时机 |
| Agent Loop | SDK内置 | Tool Runner内置 | 自己实现 |
| 文件/Shell能力 | 可复用内置 Coding Agent 工具 | 工具需要自己提供 | 工具需要自己提供 |
| Tool Call解析 | SDK处理 | SDK处理 | 自己解析 |
| Tool Result回传 | SDK处理 | SDK处理 | 自己构造并回传 |
| 会话历史 | SDK管理为主 | Tool Runner管理当前循环 | 自己管理 |
| 权限确认 | 使用SDK的权限与Hooks | 不适合复杂人工审批 | 完全自定义 |
| 事件协议 | 受SDK事件约束 | 需要封装SDK结果 | 完全自定义 |
| 上下文压缩 | SDK能力为主 | 需要在外围补充 | 完全自定义 |
| 重试和网络错误 | SDK处理较多 | SDK处理 | 基础HTTP重试由SDK提供，Agent重试自己实现 |
| 可替换其他模型 | 较困难 | 中等 | 最容易 |
| 控制力 | 中 | 中高 | 最高 |
| 开发工作量 | 最小 | 中等 | 最大 |
| 是否是真正自研Runtime | 否 | 部分 | 是 |
| 适合阶段 | 快速原型、能力对照 | Agent MVP | 长期核心能力 |

## 方式一：Claude Agent SDK

### 原理

```text
你的平台
→ Claude Agent SDK
→ Claude Code Agent Runtime
→ Claude模型
→ 内置Read/Edit/Bash等工具
→ SDK继续循环
→ 返回结果
```

你调用的是一个已经具备 Coding Agent 能力的 Runtime：

```ts
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const event of query({
  prompt: "创建一个贪吃蛇游戏",
  options: {
    cwd: workspacePath,
  },
})) {
  // 接收消息、Tool Call和最终结果
}
```

你主要负责：

- 提供 Prompt；
- 指定 Workspace；
- 配置允许的工具；
- 监听事件；
- 将结果转成平台事件；
- 配置权限和 Hooks。

SDK主要负责：

- 请求 Claude；
- Agent 循环；
- Tool Call；
- 文件和 Shell 工具；
- 会话；
- Tool Result回传；
- 继续请求模型。

Claude Agent SDK 是原 Claude Code SDK 的后续名称，本质上允许在自己的进程里复用 Claude Code 的 Agent 能力。[Agent SDK迁移说明](https://platform.claude.com/docs/es/agent-sdk/migration-guide)

### 优缺点

优点：

- 最快获得强大的 Coding Agent；
- 不需要自己实现读写文件、Shell和循环；
- 适合作为 OpenGame 的替代方案快速验证效果。

缺点：

- Agent行为较多由 SDK决定；
- 事件、工具和会话模型受SDK约束；
- 底层行为变化可能受SDK升级影响；
- 仍不是你们自己掌控的Runtime。

适合：

```text
ClaudeAgentSdkAdapter
```

但不适合作为长期自研核心的唯一实现。

---

## 方式二：Anthropic SDK + Tool Runner

### 原理

```text
你的程序定义工具
→ Tool Runner请求Claude
→ Claude返回tool_use
→ Tool Runner调用你的工具函数
→ Tool Runner自动回传tool_result
→ Claude继续生成
→ 返回最终结果
```

例如：

```ts
const finalMessage = await anthropic.beta.messages.toolRunner({
  model,
  messages,
  tools: [
    readFileTool,
    writeFileTool,
    buildGameTool,
  ],
});
```

你负责：

- 定义工具Schema；
- 实现工具函数；
- 提供System Prompt；
- 提供初始消息；
- 管理Workspace安全；
- 处理最终结果。

Tool Runner负责：

- 识别 `tool_use`；
- 调用对应工具；
- 包装错误；
- 构造 `tool_result`；
- 将结果发回Claude；
- 重复循环直到模型结束。

官方将 Tool Runner 定位为自动管理工具循环、结果格式和类型校验的SDK辅助能力，目前属于 beta。[Tool Runner文档](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner)

### 优缺点

优点：

- 比 Agent SDK 更容易使用自己的游戏工具；
- 比手动实现循环简单；
- 很适合快速实现一个 Game Agent MVP；
- 可以使用 Zod 定义类型安全的工具。

缺点：

- 循环仍由 Tool Runner控制；
- 复杂权限、暂停恢复、成本控制不够灵活；
- 自定义事件和逐步持久化需要外围封装；
- 官方建议复杂人工审批和条件执行使用手动循环。

适合：

```text
ClaudeGameAgent MVP
```

例如快速验证：

```text
Claude
→ write_file
→ build_game
→ inspect_browser
→ 修复
```

---

## 方式三：Anthropic SDK + 手动 Agent Loop

### 原理

```text
你的Runtime请求Claude
→ Claude返回文本或tool_use
→ 你的Runtime解析
→ 你的权限层判断
→ 你的Tool Registry执行
→ 你的Runtime构造tool_result
→ 再次请求Claude
→ 直到你判断任务完成
```

核心循环由你实现：

```ts
while (true) {
  const response = await anthropic.messages.create({
    model,
    system,
    messages,
    tools,
  });

  messages.push({
    role: "assistant",
    content: response.content,
  });

  const toolCalls = response.content.filter(
    block => block.type === "tool_use"
  );

  if (toolCalls.length === 0) {
    return response;
  }

  const results = [];

  for (const call of toolCalls) {
    const permission = await policy.check(call);

    if (!permission.allowed) {
      results.push(toolDenied(call));
      continue;
    }

    const result = await toolRegistry.execute(
      call.name,
      call.input
    );

    results.push({
      type: "tool_result",
      tool_use_id: call.id,
      content: result,
    });
  }

  messages.push({
    role: "user",
    content: results,
  });
}
```

Claude只决定：

```text
是否调用工具
调用哪个工具
工具参数是什么
下一步如何处理结果
```

你决定：

```text
工具是否存在
是否允许执行
具体怎么执行
是否并行
是否需要用户确认
结果截断方式
何时重试
何时压缩上下文
何时停止
是否进入验证修复循环
```

Anthropic官方说明，客户端工具需要应用程序自己执行，并通过 `tool_result` 将结果返回模型。[Tool Use原理](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works)

### 优缺点

优点：

- 完全掌控Agent Runtime；
- 可以实现自己的权限、事件、Session；
- 可以替换Claude为其他模型；
- 可以针对游戏开发设计专用循环；
- 最适合建立长期技术壁垒。

缺点：

- 需要自己处理大量工程问题；
- 容易出现孤立Tool Call、循环失控、重复修改；
- 需要完善的Benchmark验证改动；
- 开发成本最高。

适合长期实现：

```text
NativeClaudeGameAgent
```

## 同一个任务在三种方式中的区别

任务：

```text
创建一个贪吃蛇游戏并确认方向键有效
```

### Claude Agent SDK

```text
你调用query()
→ SDK规划
→ SDK读写文件
→ SDK运行命令
→ SDK继续调用Claude
→ 返回结果
```

你主要观察过程。

### Tool Runner

```text
你提供write_file、build_game、verify_game
→ Tool Runner调用Claude
→ 自动运行这些工具
→ 自动把结果交回Claude
→ 返回最终结果
```

工具是你的，循环是SDK的。

### 手动 Agent Loop

```text
你请求Claude
→ 自己收到write_file调用
→ 检查路径和权限
→ 自己执行写入
→ 记录file_changed事件
→ 回传结果
→ 收到build_game调用
→ 自己启动Sandbox
→ 回传构建结果
→ 收到verify_game调用
→ 自己控制浏览器
→ 判断是否继续修复
```

工具和循环都是你的。

## 最适合你们的选择

建议不要一步跳到最复杂的手动Runtime：

| 阶段 | 实现 |
|---|---|
| V1 | `OpenGameAdapter` |
| V1.5 | `ClaudeAgentSdkAdapter`，快速判断Claude Coding Agent效果 |
| V2 MVP | `ClaudeToolRunnerAdapter`，开始使用自己的游戏工具 |
| V2核心 | `NativeClaudeGameAgent`，迁移到手动Agent Loop |

其中最关键的一句话是：

```text
Claude Agent SDK：工具和循环主要是SDK的
Tool Runner：工具是你的，循环主要是SDK的
手动 Agent Loop：工具和循环都是你的
```

如果长期目标是形成自己的 Game Coding Agent，最终应落到第三种；但第二种很适合作为第三种之前的低成本验证版本。