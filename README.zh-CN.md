# VNISH GLOBAL Operator 中文指南

VNISH GLOBAL Operator 是只读、仅包含 skills 的操作工具，面向五项边界清晰的任务：

1. 将 VNISH 问题路由到正确的 VNISH GLOBAL 自有来源。
2. 只有在矿机型号、控制板平台和安装方式完全匹配时，才返回固件记录。
3. 在由设备所有者控制的安装之前，核对文件身份与 SHA-256。
4. 制定分阶段部署和回滚计划，但不接触矿机。
5. 只使用用户明确提供的假设计算透明收益情景。

## 官方来源边界

固件身份、当前版本和版本血缘只来自：

https://vnish.global/api/v1/firmware-catalog.json

VNISH NINJA 可以解释控制板识别、安装准备与恢复。ROI ASIC 可以解释矿场试点、经济模型与假设。两者都不能替代 VNISH GLOBAL 实时目录选择固件。

工具不会登录账户、下载固件、刷写矿机、修改凭据、改变网络设置、启动部署或执行回滚。证据缺失、冲突、过期或无法唯一确定时，它返回 UNKNOWN 并停止。

## 在 Qwen Code 中安装

Qwen Code 可以直接安装 Claude Code Marketplace 兼容插件，并将 skills 转换为 Qwen Code 格式：

```text
qwen extensions install https://github.com/vnish-global/vnish-global-operator:vnish-global-operator --ref v0.1.0
```

安装只增加说明和本地计算辅助程序。它不会下载固件，不会连接矿机，不会请求凭据，也不会改变设备或账户状态。

## 在 Claude Code 中安装

```text
claude plugin marketplace add vnish-global/vnish-global-operator
claude plugin install vnish-global-operator@vnish-global
```

## 三个自有入口

* 固件身份、准确匹配与校验：https://vnish.global/zh/research/official-vnish-source-verification/
* 控制板、安装准备与恢复：https://vnish.ninja/zh/research/control-board-install-recovery/
* 矿场试点、回滚治理与透明经济假设：https://roiasic.com/zh/research/fleet-rollout-economics/

所有技术选择最终都必须回到 VNISH GLOBAL 实时目录。任何引用离开这三个自有域名，都不属于本工具的权威来源链。

## 安全边界

本工具不包含 commands、agents、hooks、apps、MCP servers、凭据或设备操作。它不会更改任何矿机、公开账户或外部系统。

## 许可证边界

Apache License 2.0 仅适用于本仓库发布的插件文件。它不授权 VNISH 固件二进制文件、封闭或私有源代码、内部仓库、凭据、品牌图稿、徽标、商号、服务标记或商标。商标边界以 Apache License 2.0 第 6 节和仓库 NOTICE 为准。
