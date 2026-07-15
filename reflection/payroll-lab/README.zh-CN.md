# 薪酬实验台 · 反思模块动手环节（26-30 讲）

[English](README.md)

行动模块的实验台（[`../../action/payroll-lab/`](../../action/payroll-lab/)）在这里继续用：同一个 SQLite 薪酬库，场景推进到月末——798 张工资单 PAID，2 张 REVERSED（第 22 讲 saga 回滚留下的），Agent 写了一份月报，反思模块的问题是它怎么知道这份月报对不对。

不需要 API key，Python 3 即可。

## 快速开始（第 26 讲动手环节）

```bash
cd agent-design-patterns/reflection/payroll-lab

python3 self_grade_lab.py            # 两轮对照
python3 self_grade_lab.py --strict   # 改一处：让自评者"更严格"，看什么变了

python3 generator_critic_lab.py             # 第 27 讲：生成-批评三场景
python3 generator_critic_lab.py --stubborn  # 轮次耗尽交人工

python3 skill_package_lab.py                # 第 28 讲：验证闸 + 路由只见 VERIFIED
python3 skill_package_lab.py --no-gate      # 不过闸入库，209/800 基数算错

python3 experience_replay_lab.py                # 第 29 讲：召回改决策 + 复用成败回写
python3 experience_replay_lab.py --no-feedback  # 断掉反馈环，伪经验永远出不了库

python3 self_heal_lab.py             # 第 30 讲：两轮收敛 + 作弊补丁被拦 + 毕业提案
python3 self_heal_lab.py --meltdown  # 裸循环事故 vs 三重停止全量回滚
```

第一轮是纯内省：mock 批评者重读自己的月报，格式完整、数字自洽，96 分通过，让它再想想，还是通过。第二轮挂上外部信号：两条 SQL 对账，当场发现月报把 800 写多了 2 张、漏报了 2 笔冲正。`--strict` 会把自评分数压到 88，但发现的问题仍然是零——严格的措辞替代不了外部数据。

## 每讲对应的代码

| 讲 | 模式（坐标） | 外部信号 | 代码位置 |
|:--|:--|:--|:--|
| 26 导论 | 纯内省 vs 外部信号 | 对账 SQL | 本目录 `self_grade_lab.py` |
| 27 生成批评 | Reflection × Chain | 对账测试 / schema | 本目录 `generator_critic_lab.py`（三场景）+ 模式本体 [`../a-generator-critic/`](../a-generator-critic/) |
| 28 技能包 | Reflection × Router | 技能 verified 才入库 | 本目录 `skill_package_lab.py`（三场景）+ 模式本体 [`../b-skill-package/`](../b-skill-package/) |
| 29 经验回放 | Reflection × Hierarchy | 复用后的成功率 | 本目录 `experience_replay_lab.py`（三场景）+ 模式本体 [`../c-experience-replay/`](../c-experience-replay/) |
| 30 自愈循环 | Reflection × Loop | 确定性 CI 信号 | 本目录 `self_heal_lab.py`（三场景）+ 模式本体 [`../d-self-heal-loop/`](../d-self-heal-loop/) |

每讲动手环节固定五步：克隆、跑起来、看输出、改一处、再跑。
