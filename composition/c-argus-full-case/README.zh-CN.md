# 完整系统装配（Full System Assembly）

本目录保留了早期 `Argus Full Case` 的路径名称，但当前实现是一套通用的完整系统验收接口。它不复制感知、记忆、推理、行动、反思、协作和治理的模式实现，只负责验证这些模块是否属于同一轮任务、同一份负载和同一条工件版本链。

核心对象：

- `SystemRunContract`：冻结任务目标、负载、选型回执和八模块主模式
- `ModuleReceipt`：绑定模块输入输出、上游回执和可核验证据
- `EndpointEvidence`：绑定最终工件、治理授权与业务端点事实
- `audit_system()`：区分“八个模块局部通过”和“完整系统端到端通过”
- `SystemAssembly`：严格装配器，在接缝断裂时立即拒绝

运行最小示例：

```bash
cd composition/c-argus-full-case
python3 example.py
pytest -q
```

完整薪酬案例：

```bash
cd composition/payroll-lab
python3 capstone_lab.py --mode bound
python3 capstone_lab.py --mode local-only
```

教学边界：摘要链能证明工件身份和交接连续性，不能替代数字签名、持久化事件总线、外部银行回执或生产身份系统。
