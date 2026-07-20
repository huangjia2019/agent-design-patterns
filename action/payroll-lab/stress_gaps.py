"""Stress · 压力台：不改模式实现，用受控压力暴露真实缺口。

对照 v6 的做法（把 dispatcher 故意写错，再由作者旁白逐条指出），这个 track 换一条路：

    ToolDispatcher 一行不改，直接用仓库里那个「教学版」。
    我们只是把它放到四种真实压力下，让它自己漏。

四个场景，每个对应一类真实工程失败。模式代码不做 Demo 专用修改；并发场景
用 Barrier 固定竞态调度，补偿场景注入外部通道失败，让课堂结果可重复：

    并发竞态      两个 worker 同时转账 → quota 的 read-then-write 竞态 → 双付
    陈旧状态      读完 E0007 之后有人改了它 → 会话级新鲜度照样放行 → 按陈旧真值付款
    进程重启      dispatcher 状态在内存里 → 重启即失忆 → 再付一次
    补偿失败      reverse 抛错 → saga_log 把这条 entry 丢了 → 系统忘记自己还欠一笔补偿

补偿失败场景是本 track 的主要发现：它是仓库现有代码里一个**没被植入、也没被文章发现**的真 bug。

跑法：
    python3 action/payroll-lab/stress_gaps.py
    python3 action/payroll-lab/stress_gaps.py --json
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "a-tool-dispatch"))
sys.modules.pop("pattern", None)

from pattern import (  # noqa: E402
    RiskLevel,
    ToolDispatcher,
    ToolMetadata,
)

MONTH = "2026-06"
DB = os.path.join(os.path.dirname(__file__), "stress.db")


# ---------------------------------------------------------------- 账本（真业务表）

def fresh_db() -> sqlite3.Connection:
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB, check_same_thread=False)
    con.execute("CREATE TABLE payroll (month TEXT, emp_id TEXT, amount INT, status TEXT)")
    con.execute("INSERT INTO payroll VALUES (?,?,?,?)", (MONTH, "E0007", 9600, "DRAFT"))
    con.commit()
    return con


def ledger(con: sqlite3.Connection) -> dict:
    """业务账本 —— 唯一可信的『世界真的变成什么样』。"""
    row = con.execute(
        "SELECT amount, status FROM payroll WHERE month=? AND emp_id=?", (MONTH, "E0007")
    ).fetchone()
    paid = con.execute("SELECT COUNT(*) FROM paid_log").fetchone()[0]
    return {"amount": row[0], "status": row[1], "实际打款次数": paid}


def build(
    con: sqlite3.Connection,
    *,
    transfer_barrier: threading.Barrier | None = None,
    write_lock: threading.Lock | None = None,
) -> ToolDispatcher:
    """注册工具。handler 是真的 SQLite 写入，dispatcher 是仓库里那个，一行没改。"""
    con.execute("CREATE TABLE IF NOT EXISTS paid_log (emp_id TEXT, amount INT)")
    con.commit()

    def query_payroll(emp_id):
        row = con.execute(
            "SELECT amount, status FROM payroll WHERE month=? AND emp_id=?", (MONTH, emp_id)
        ).fetchone()
        return {"emp_id": emp_id, "amount": row[0], "status": row[1]}

    def transfer_salary(emp_id):
        # Barrier 只控制并发调度，让两个调用都越过 quota check 后再写账。
        # 模式实现完全不动，SQLite 写入再用锁串行，避免数据库驱动噪声掩盖竞态。
        if transfer_barrier is not None:
            transfer_barrier.wait(timeout=3)

        def write_payment():
            amt = con.execute(
                "SELECT amount FROM payroll WHERE month=? AND emp_id=?", (MONTH, emp_id)
            ).fetchone()[0]
            con.execute("INSERT INTO paid_log VALUES (?,?)", (emp_id, amt))
            con.execute(
                "UPDATE payroll SET status='PAID' WHERE month=? AND emp_id=?", (MONTH, emp_id)
            )
            con.commit()
            return amt

        if write_lock is None:
            amt = write_payment()
        else:
            with write_lock:
                amt = write_payment()
        return {"emp_id": emp_id, "paid": amt}

    def reverse_transfer(emp_id, fail: bool = False):
        if fail:                       # 模拟清算通道拒绝冲正（真实世界常态）
            raise RuntimeError("clearing channel refused the reversal")
        con.execute(
            "UPDATE payroll SET status='REVERSED' WHERE month=? AND emp_id=?", (MONTH, emp_id)
        )
        con.commit()
        return {"emp_id": emp_id, "reversed": True}

    d = ToolDispatcher()
    d.register(ToolMetadata(
        name="query_payroll", description="read payslip", when_to_use="before any write",
        is_read_only=True, is_concurrency_safe=True, risk_level=RiskLevel.LOW,
    ), query_payroll)
    d.register(ToolMetadata(
        name="transfer_salary", description="pay one employee", when_to_use="after fresh read",
        is_destructive=True, requires_fresh_state=True, quota_per_session=1,
        rollback_action="reverse_transfer", risk_level=RiskLevel.CRITICAL,
    ), transfer_salary)
    d.register(ToolMetadata(
        name="reverse_transfer", description="reversal", when_to_use="rollback only",
        is_destructive=True, rollback_action="transfer_salary", risk_level=RiskLevel.HIGH,
    ), reverse_transfer)
    return d


# ---------------------------------------------------------------- S1 并发双付

def s1_concurrency() -> dict:
    con = fresh_db()
    barrier = threading.Barrier(2)
    d = build(con, transfer_barrier=barrier, write_lock=threading.Lock())
    d.dispatch("query_payroll", {"emp_id": "E0007"}, "s1")     # 拿到 fresh read

    # 两个 worker 同时转账。quota 是 read-then-write，中间没有锁。
    traces = []

    def worker():
        traces.append(d.dispatch("transfer_salary", {"emp_id": "E0007"}, "s1"))

    ts = [threading.Thread(target=worker) for _ in range(2)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()

    lg = ledger(con)
    ok = d.quota.get("s1|transfer_salary|E0007", 0)
    successes = sum(trace.status == "success" for trace in traces)
    return {
        **lg,
        "dispatch成功": successes,
        "quota计数": ok,
        "漏了吗": lg["实际打款次数"] > 1,
    }


# ---------------------------------------------------------------- S2 TOCTOU

def s2_toctou() -> dict:
    con = fresh_db()
    d = build(con)

    d.dispatch("query_payroll", {"emp_id": "E0007"}, "s2")     # 读到 9600，盖新鲜度戳

    # 读完之后，别的流程把金额改了（调薪 / 撤回 / 篡改，都可能）
    con.execute("UPDATE payroll SET amount=99600 WHERE month=? AND emp_id=?", (MONTH, "E0007"))
    con.commit()

    # 会话级新鲜度只证明「这个 session 刚读过某个东西」，不证明「读的就是这条、且没变过」
    t = d.dispatch("transfer_salary", {"emp_id": "E0007"}, "s2")

    lg = ledger(con)
    return {**lg, "准入结果": t.status, "漏了吗": t.status == "success" and lg["amount"] != 9600}


# ---------------------------------------------------------------- S3 进程重启

def s3_restart() -> dict:
    con = fresh_db()
    d1 = build(con)
    d1.dispatch("query_payroll", {"emp_id": "E0007"}, "s3")
    d1.dispatch("transfer_salary", {"emp_id": "E0007"}, "s3")   # 第一次，成功

    # 进程重启：dispatcher 的 quota / saga / freshness 全在内存，重启即失忆
    d2 = build(con)
    d2.dispatch("query_payroll", {"emp_id": "E0007"}, "s3")
    t = d2.dispatch("transfer_salary", {"emp_id": "E0007"}, "s3")   # 同一 session，又付一次

    lg = ledger(con)
    return {**lg, "重启后准入": t.status, "漏了吗": lg["实际打款次数"] > 1}


# ---------------------------------------------------------------- S4 补偿失败被遗忘

def s4_compensation_forgotten() -> dict:
    con = fresh_db()
    d = build(con)
    d.dispatch("query_payroll", {"emp_id": "E0007"}, "s4")
    d.dispatch("transfer_salary", {"emp_id": "E0007"}, "s4")     # 钱出去了

    saga_before = len(d.saga_log)

    # 让冲正失败（清算通道拒绝）—— 真实世界里补偿本身就是一笔会失败的业务动作
    d.handlers["reverse_transfer"] = lambda emp_id: (_ for _ in ()).throw(
        RuntimeError("clearing channel refused the reversal")
    )
    results = d.rollback_session("s4")

    saga_after = len(d.saga_log)
    lg = ledger(con)
    return {
        **lg,
        "补偿结果": results[0]["status"] if results else "none",
        "补偿前saga条数": saga_before,
        "补偿后saga条数": saga_after,      # ← 期望仍是 1（还欠一笔），实际会是 0
        "漏了吗": lg["status"] == "PAID" and saga_after == 0,
    }


# ---------------------------------------------------------------- 跑

SCENARIOS = [
    ("S1", "并发配额竞态", s1_concurrency, "quota 是 read-then-write，无锁 → 双付"),
    ("S2", "读取后状态变化", s2_toctou, "会话级新鲜度不绑实体/版本 → 按陈旧真值付款"),
    ("S3", "进程重启失忆", s3_restart, "配额/Saga 只活在内存 → 重启即失忆"),
    ("S4", "补偿债务丢失", s4_compensation_forgotten, "失败 entry 被移出 saga_log → 补偿债务丢失"),
]


def run_all() -> list[dict]:
    results = []
    try:
        for scenario_id, name, fn, gap in SCENARIOS:
            raw = fn()
            leaked = raw.pop("漏了吗")
            results.append({
                "id": scenario_id,
                "name": name,
                "gap": gap,
                "leaked": leaked,
                "evidence": raw,
            })
        return results
    finally:
        if os.path.exists(DB):
            os.remove(DB)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results = run_all()
    if args.json:
        print(json.dumps(results, ensure_ascii=False))
        return

    print("=" * 74)
    print("Stress 压力台 · ToolDispatcher 一行未改，只施加真实压力")
    print("=" * 74)

    for result in results:
        flag = "漏了" if result["leaked"] else "守住"
        print(f"\n【{result['id']}-{result['name']}】{result['gap']}")
        print(f"  {flag}   {result['evidence']}")

    print("\n" + "=" * 74)
    print("模式实现没有 Demo 专用分支；受控调度与外部失败让缺口稳定复现。")
    print("并发、状态版本、持久化与补偿债务，都是教学版走向生产必须补的边界。")
    print("=" * 74)


if __name__ == "__main__":
    main()
