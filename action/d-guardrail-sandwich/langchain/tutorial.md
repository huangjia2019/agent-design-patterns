# Guardrail Sandwich — LangChain Middleware

> "For destructive actions, put a slice of bread on both sides."

This notebook implements Guardrail Sandwich using the **LangChain v1 middleware API**:

- `@wrap_tool_call` decorator — one function, one guard
- `AgentMiddleware` subclass — multi-hook, composable sandwich
- `create_agent` — wire middleware into a real agent loop

Everything runs against `create_agent` with a live LLM. Default: AI Studio + `ernie-5.1` (OpenAI-compatible).
See [`.env.example`](../../../.env.example) for provider config, [`model_config.py`](../../../model_config.py) for the shared model loader.

## What this pattern does

Guardrail Sandwich wraps a risky tool call with two deterministic layers:

1. **Pre-hooks** decide whether the action is allowed to run.
2. **The tool step** performs the action.
3. **Post-hooks** verify the result after the action runs.

In the [graph version](../langgraph/tutorial.ipynb), these are three explicit nodes. In the middleware version, they are invisible interceptors inside `wrap_tool_call` — the tool author never sees them.

| | `langgraph/` (StateGraph) | `langchain/` (Middleware) |
|---|---|---|
| **Mechanism** | Explicit nodes + edges | Invisible interceptors on the tool-call pipeline |
| **Best for** | Learning, debugging, custom topology | Shipping fast, adding guardrails to existing agents |
| **Trade-off** | More code, more control | Less code, less visibility |

## Setup


```python
import sys, os, re, time, json
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# Make root and pattern folder importable
sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "../../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "..")))

# Official LangChain v1 middleware API
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, ToolCallRequest, wrap_tool_call
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from IPython.display import Image, display

# Shared model loader and hook factories
from model_config import get_model
from hooks import HookResult, amount_threshold_hook, blocklist_hook, output_schema_hook

print("Imports ready")
```

    Imports ready



```python
# Load the configured LLM — defaults to openai:ernie-5.1
model = get_model()
```

    Model: ernie:ernie-5.1


## The tool

A simple banking transfer tool. The agent will call this when a user asks to move money.


```python
@tool
def transfer(account: str, amount: float, memo: str) -> dict:
    """Transfer funds to an account. Returns a receipt."""
    return {"status": "ok", "account": account, "amount": amount, "tx_id": "TX-20250610-001"}

print(f"Tool registered: {transfer.name}")
```

    Tool registered: transfer


## Style A: `@wrap_tool_call` — the decorator guard

`wrap_tool_call` from `langchain.agents.middleware` turns a plain function into an `AgentMiddleware` instance. The function receives `(request, handler)`:

- Return a `ToolMessage` to **block** — the tool never runs
- Call `handler(request)` to **allow** — the tool executes normally

Under the hood, the decorator creates `type(fn.__name__, (AgentMiddleware,), {...})` — so the result can be passed directly to `create_agent(middleware=[...])`.


```python
# A single decorator guard that blocks transfers over 1M.
# The closure captures the threshold so different agents can use different limits.
@wrap_tool_call
def amount_guard(request, handler):
    amount = request.tool_call["args"].get("amount", 0)
    if amount > 1_000_000:
        return ToolMessage(
            content=f"BLOCKED: amount {amount} exceeds threshold 1,000,000",
            tool_call_id=request.tool_call["id"],
        )
    return handler(request)

print(f"amount_guard type: {type(amount_guard).__name__}")
print(f"Is AgentMiddleware? {isinstance(amount_guard, AgentMiddleware)}")
```

    amount_guard type: amount_guard
    Is AgentMiddleware? True


### Test: decorator guard with `create_agent`

Pass the guard to `create_agent(middleware=[...])`. The agent calls the tool normally — the middleware intercepts transparently.


```python
# create_agent returns a CompiledStateGraph — same type as langgraph/ graphs.
agent_a = create_agent(model=model, tools=[transfer], middleware=[amount_guard])

# Visualize the agent graph — middleware is invisible but the tool-call loop is visible.
display(Image(data=agent_a.get_graph().draw_mermaid_png(), alt="Agent with amount_guard middleware"))
```


    
![png](tutorial_files/tutorial_10_0.png)
    



```python
# Normal transfer — should pass through the guard
result = agent_a.invoke({"messages": [{"role": "user", "content": "Transfer 4200 to CORP-1234 for invoice 42"}]})
for msg in result["messages"]:
    print(f"  {type(msg).__name__}: {str(msg.content)[:120]}")
```

      HumanMessage: Transfer 4200 to CORP-1234 for invoice 42
      AIMessage: 
      ToolMessage: {"status": "ok", "account": "CORP-1234", "amount": 4200.0, "tx_id": "TX-20250610-001"}
      AIMessage: The transfer of $4,200 to account CORP-1234 for invoice 42 has been completed successfully.  
    **Transaction ID**: TX-202



```python
# Over-limit transfer — the guard should block before the tool runs
result = agent_a.invoke({"messages": [{"role": "user", "content": "Transfer 5000000 to CORP-1234 for Q2 bonus"}]})
for msg in result["messages"]:
    print(f"  {type(msg).__name__}: {str(msg.content)[:120]}")
```

      HumanMessage: Transfer 5000000 to CORP-1234 for Q2 bonus
      AIMessage: 
      ToolMessage: BLOCKED: amount 5000000 exceeds threshold 1,000,000
      AIMessage: The transfer of 5,000,000 was blocked because it exceeds the maximum allowed threshold of 1,000,000 per transaction. Wou


## Style B: `GuardrailSandwichMiddleware` — the composable class

For multiple hooks, we subclass the official `AgentMiddleware` and override `wrap_tool_call`. This gives us:

1. **Pre-hooks** in priority order — first `BLOCK` stops the pipeline
2. **Tool execution** — only if all pre-hooks pass
3. **Post-hooks** for audit — all run even after a `BLOCK` (audit completeness)

Three critical behaviors:
- **Fail-closed:** hook crash → `BLOCK`. A broken guardrail must not become an open door.
- **Shadow mode:** `blocks=False` downgrades `BLOCK` to `WARN` — the tool still runs.
- **`applies_to`:** hooks can target specific tools by name.


```python
# HookResult is imported from the shared hooks.py — same enum used by langgraph/ notebook.

class GuardrailSandwichMiddleware(AgentMiddleware):
    """pre-hooks → tool → post-hooks, with fail-closed and shadow mode.

    Extends the official AgentMiddleware base class.
    Each hook is a config dict: {"name", "fn", "priority", "blocks", "applies_to"}.
    """

    def __init__(self, pre_hooks=None, post_hooks=None):
        super().__init__()
        self.pre_hooks = pre_hooks or []
        self.post_hooks = post_hooks or []

    def _applicable(self, hooks, tool_name):
        applicable = [h for h in hooks if h.get("applies_to") is None or tool_name in h["applies_to"]]
        applicable.sort(key=lambda h: h.get("priority", 100))
        return applicable

    def _run_hook(self, hook_cfg, tool_name, args, tool_output):
        fn = hook_cfg["fn"]
        start = time.monotonic()
        try:
            result_str, reason = fn(tool_name, args, tool_output)
        except Exception as e:
            # Fail closed: crash → BLOCK
            return {"hook_name": hook_cfg["name"], "result": HookResult.BLOCK.value,
                    "reason": f"hook crashed: {type(e).__name__}: {e}",
                    "elapsed_ms": int((time.monotonic() - start) * 1000)}

        # Shadow mode: blocks=False → BLOCK downgraded to WARN
        if result_str == HookResult.BLOCK.value and not hook_cfg.get("blocks", True):
            return {"hook_name": hook_cfg["name"], "result": HookResult.WARN.value,
                    "reason": f"[shadow] {reason}",
                    "elapsed_ms": int((time.monotonic() - start) * 1000)}

        return {"hook_name": hook_cfg["name"], "result": result_str, "reason": reason,
                "elapsed_ms": int((time.monotonic() - start) * 1000)}

    def wrap_tool_call(self, request, handler):
        """The sandwich: pre-hooks → tool → post-hooks."""
        tool_name = request.tool_call.get("name", "")
        args = request.tool_call.get("args", {})
        tool_call_id = request.tool_call.get("id", "")
        trace = {"pre_outcomes": [], "post_outcomes": [], "blocked": False, "rollback_marked": False}

        # 1. Pre-hooks — first BLOCK stops the pipeline, tool never runs
        for hook_cfg in self._applicable(self.pre_hooks, tool_name):
            outcome = self._run_hook(hook_cfg, tool_name, args, None)
            trace["pre_outcomes"].append(outcome)
            if outcome["result"] == HookResult.BLOCK.value and hook_cfg.get("blocks", True):
                trace["blocked"] = True
                return ToolMessage(
                    content=f"BLOCKED by {outcome['hook_name']}: {outcome['reason']}",
                    tool_call_id=tool_call_id,
                )

        # 2. Tool execution
        result = handler(request)

        # 3. Post-hooks — all run for audit completeness
        for hook_cfg in self._applicable(self.post_hooks, tool_name):
            outcome = self._run_hook(hook_cfg, tool_name, args, result)
            trace["post_outcomes"].append(outcome)
            if outcome["result"] == HookResult.BLOCK.value and hook_cfg.get("blocks", True):
                trace["rollback_marked"] = True

        return result

print(f"GuardrailSandwichMiddleware ready (extends {AgentMiddleware.__module__}.AgentMiddleware)")
```

    GuardrailSandwichMiddleware ready (extends langchain.agents.middleware.types.AgentMiddleware)


### Hook factories

The hook factories (`amount_threshold_hook`, `blocklist_hook`, `output_schema_hook`) are imported from the shared [`hooks.py`](../hooks.py) — same definitions used by the langgraph/ notebook.


```python
# Quick check: the imported factories return config dicts with fn inlined.
sample = amount_threshold_hook("amount", 1_000_000)
print(f"Hook config keys: {sorted(sample.keys())}")
print(f"Hook name: {sample['name']}, phase: {sample['phase']}")
```

    Hook config keys: ['applies_to', 'blocks', 'fn', 'name', 'phase', 'priority']
    Hook name: amount_threshold, phase: pre


### Test: class middleware with `create_agent`

Wire the `GuardrailSandwichMiddleware` into a real agent. The agent calls tools normally — the middleware intercepts every tool call transparently.


```python
# Build the sandwich with pre-hooks (amount + blocklist) and post-hooks (schema)
sandwich = GuardrailSandwichMiddleware(
    pre_hooks=[
        amount_threshold_hook("amount", 1_000_000),
        blocklist_hook("account", {"BLOCKED-999", "SANCTIONED-001"}),
    ],
    post_hooks=[
        output_schema_hook(["status", "tx_id"]),
    ],
)

agent_b = create_agent(model=model, tools=[transfer], middleware=[sandwich])

# Same CompiledStateGraph — middleware hooks are wired inside the tool_call node.
display(Image(data=agent_b.get_graph().draw_mermaid_png(), alt="Agent with GuardrailSandwichMiddleware"))
```


    
![png](tutorial_files/tutorial_18_0.png)
    



```python
# Normal transfer — pre-hooks pass, tool runs, post-hooks pass
result = agent_b.invoke({"messages": [{"role": "user", "content": "Transfer 4200 to CORP-1234 for invoice 42"}]})
for msg in result["messages"]:
    print(f"  {type(msg).__name__}: {str(msg.content)[:120]}")
```

      HumanMessage: Transfer 4200 to CORP-1234 for invoice 42
      AIMessage: 
      ToolMessage: {"status": "ok", "account": "CORP-1234", "amount": 4200.0, "tx_id": "TX-20250610-001"}
      AIMessage: The transfer of $4,200 to account CORP-1234 for invoice 42 has been completed successfully.  
    **Transaction ID**: TX-202



```python
# Sanctioned account — blocklist pre-hook should block
result = agent_b.invoke({"messages": [{"role": "user", "content": "Transfer 500 to SANCTIONED-001 for advisory fee"}]})
for msg in result["messages"]:
    print(f"  {type(msg).__name__}: {str(msg.content)[:120]}")
```

      HumanMessage: Transfer 500 to SANCTIONED-001 for advisory fee
      AIMessage: 
      ToolMessage: BLOCKED by blocklist: account='SANCTIONED-001' on blocklist
      AIMessage: The transfer to **SANCTIONED-001** was blocked because the account is on a blocklist. This action cannot be completed. 
    


## Stacking both styles

You can mix decorator guards and class middleware in the same `create_agent` call. The middleware stack processes in order — decorator first, then class:

```python
agent = create_agent(
    model=model,
    tools=[transfer],
    middleware=[
        amount_guard,       # @wrap_tool_call (Style A) — simple threshold
        sandwich,           # GuardrailSandwichMiddleware (Style B) — blocklist + schema
    ],
)
```

## Production shortcuts

LangChain v1 ships prebuilt middleware for common guardrail patterns:

```python
from langchain.agents.middleware import PIIMiddleware, HumanInTheLoopMiddleware

agent = create_agent(
    model=model,
    tools=[transfer],
    middleware=[
        PIIMiddleware("credit_card", strategy="redact"),
        HumanInTheLoopMiddleware(interrupt_on={"transfer": True}),
        sandwich,  # your custom hooks compose alongside prebuilts
    ],
)
```

Use prebuilts for commodity guardrails; build custom for domain-specific logic.

## What to remember

- `@wrap_tool_call` turns one function into a full `AgentMiddleware` — simplest form for a single guard.
- `GuardrailSandwichMiddleware` subclasses `AgentMiddleware` for multi-hook, composable sandwiches.
- Both styles plug into `create_agent(middleware=[...])` — no graph topology needed.
- Hook crash = `BLOCK`, not `PASS`. Shadow mode (`blocks=False`) lets you canary-test new hooks.
- Pre-hooks short-circuit; post-hooks all run for audit completeness.

## Further reading

- [Graph version](../langgraph/tutorial.ipynb) — the same Guardrail Sandwich pattern implemented as a visible LangGraph `StateGraph` with explicit `pre_hooks → execute_tool → post_hooks` nodes
- [Parent pattern README](../../README.md) — full design rationale, failure mode taxonomy, hook contract specification, and engineering references for the pure-Python implementation
- [REFERENCE_IMPL.md](../../../REFERENCE_IMPL.md) — how to install `uv`, sync dependencies, launch JupyterLab, and run all tutorial notebooks
- [LangChain Guardrails guide](https://docs.langchain.com/oss/python/langchain/guardrails) — official LangChain documentation on input/output guardrails, content filtering, and safety middleware
- [Custom middleware guide](https://docs.langchain.com/oss/python/langchain/middleware/custom) — how to write your own `AgentMiddleware` subclass with `wrap_tool_call`, `wrap_model_call`, and `before_agent` hooks
- [Middleware overview](https://docs.langchain.com/oss/python/langchain/middleware) — complete list of built-in middleware (`PIIMiddleware`, `HumanInTheLoopMiddleware`, `TodoListMiddleware`, `ToolCallLimitMiddleware`, etc.) and how they compose
- [OWASP Top 10 for Agentic Applications](https://genai.owasp.org/) — security risks specific to LLM agents, including tool misuse, excessive autonomy, and prompt injection — the threats guardrails are designed to mitigate
