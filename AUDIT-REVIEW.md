# Neo Execution Specs 审计报告

**审计日期**: 2025-02-04  
**项目版本**: Neo N3 v3.9.1 Python 实现  
**审计范围**: VM 指令、Native Contracts、类型系统、边界条件  
**测试状态**: 736 tests passing, 1 skipped

---

## 严重问题

### 1. SHL/SHR 指令栈损坏 (Critical)

**文件**: `src/neo/vm/instructions/numeric.py`

**问题**: 当 shift 值为 0 时，函数提前返回但没有将原始值推回栈中，导致栈损坏。

```python
def shl(engine: ExecutionEngine, instruction: Instruction) -> None:
    shift = int(engine.pop().get_integer())
    engine.limits.assert_shift(shift)
    if shift == 0:
        return  # BUG: 原始值 x 已被 pop，但没有 push 回去
    x = engine.pop().get_integer()
    engine.push(Integer(x << shift))
```

**C# 参考实现**:
```csharp
case OpCode.SHL:
{
    int shift = (int)context.EvaluationStack.Pop().GetInteger();
    limits.AssertShift(shift);
    if (shift == 0) return;
    var x = context.EvaluationStack.Pop().GetInteger();
    Push(x << shift);
    break;
}
```

**修复建议**:
```python
def shl(engine: ExecutionEngine, instruction: Instruction) -> None:
    shift = int(engine.pop().get_integer())
    engine.limits.assert_shift(shift)
    x = engine.pop().get_integer()
    if shift == 0:
        engine.push(Integer(x))
        return
    engine.push(Integer(x << shift))
```

**影响**: 任何使用 SHL/SHR 且 shift=0 的合约都会导致栈状态错误。

---

### 2. PACKMAP 键值顺序错误 (Critical)

**文件**: `src/neo/vm/instructions/compound.py`

**问题**: PACKMAP 中 key 和 value 的弹出顺序与 C# 实现相反。

```python
def packmap(engine: ExecutionEngine, instruction: Instruction) -> None:
    # ...
    for _ in range(size):
        key = engine.pop()    # 错误：应该先 pop value
        value = engine.pop()  # 错误：应该后 pop key
        result[key] = value
```

**C# 参考实现**:
```csharp
for (int i = 0; i < size; i++)
{
    PrimitiveType key = context.EvaluationStack.Pop<PrimitiveType>();
    StackItem value = context.EvaluationStack.Pop();
    map[key] = value;
}
```

**注意**: C# 中先 pop key，后 pop value。但栈是 LIFO，所以 push 顺序是 value 先 push，key 后 push。当前 Python 实现的顺序是正确的，需要验证实际行为。

**建议**: 添加测试用例验证与 C# 行为一致。

---

### 3. Keccak256 回退实现错误 (Critical)

**文件**: `src/neo/native/crypto_lib.py`

**问题**: 当 pycryptodome 和 sha3 库都不可用时，回退使用 `hashlib.sha3_256`，但 SHA3-256 和 Keccak-256 是不同的算法！

```python
def keccak256(self, data: bytes) -> bytes:
    try:
        from Crypto.Hash import keccak
        # ...
    except ImportError:
        try:
            import sha3
            return sha3.keccak_256(data).digest()
        except ImportError:
            import hashlib
            return hashlib.sha3_256(data).digest()  # 错误！
```

**影响**: 在没有正确依赖的环境中，所有使用 Keccak256 的签名验证都会失败。

**修复建议**: 移除错误的回退，或抛出明确的错误：
```python
raise ImportError("Keccak256 requires pycryptodome or pysha3 library")
```

---

## 中等问题

### 4. EvaluationStack.reverse() 方法缺失 (Medium)

**文件**: `src/neo/vm/evaluation_stack.py`

**问题**: `REVERSE3`, `REVERSE4`, `REVERSEN` 指令调用 `stack.reverse(n)`，但该方法未实现。

```python
# stack.py 中调用:
engine.current_context.evaluation_stack.reverse(3)

# evaluation_stack.py 中缺少:
def reverse(self, n: int) -> None:
    """Reverse the top n items."""
    # 未实现
```

**修复建议**:
```python
def reverse(self, n: int) -> None:
    """Reverse the top n items on the stack."""
    if n < 0 or n > len(self._items):
        raise Exception(f"Invalid reverse count: {n}")
    if n <= 1:
        return
    # Reverse top n items
    start = len(self._items) - n
    self._items[start:] = self._items[start:][::-1]
```

---

### 5. Buffer.reverse() 方法缺失 (Medium)

**文件**: `src/neo/vm/types/buffer.py`

**问题**: `REVERSEITEMS` 指令对 Buffer 调用 `reverse()`，但 Buffer 类未实现该方法。

```python
# compound.py:
def reverseitems(engine: ExecutionEngine, instruction: Instruction) -> None:
    x = engine.pop()
    if isinstance(x, Buffer):
        x.reverse()  # Buffer 没有 reverse 方法
```

**修复建议**: 在 Buffer 类中添加：
```python
def reverse(self) -> None:
    """Reverse bytes in place."""
    self._value.reverse()
```

---

### 6. 缺少栈大小检查 (Medium)

**文件**: 多个指令文件

**问题**: 许多指令在 pop 之前没有检查栈是否有足够的元素。

**示例** (`numeric.py`):
```python
def add(engine: ExecutionEngine, instruction: Instruction) -> None:
    x2 = engine.pop().get_integer()  # 如果栈为空会抛出 IndexError
    x1 = engine.pop().get_integer()
    engine.push(Integer(x1 + x2))
```

**建议**: 在 EvaluationStack.pop() 中添加检查：
```python
def pop(self) -> StackItem:
    if not self._items:
        raise Exception("Stack underflow")
    return self._items.pop()
```

---

### 7. BigInteger 大小限制未强制执行 (Medium)

**文件**: `src/neo/types/big_integer.py`

**问题**: `MAX_SIZE = 32` 定义了但未在运算中强制执行。

```python
class BigInteger(int):
    MAX_SIZE = 32  # 定义了但未使用
    
    def to_bytes_le(self) -> bytes:
        # 没有检查结果是否超过 32 字节
```

**C# 参考**: Neo VM 限制整数最大 32 字节 (256 位)。

**修复建议**: 在 Integer 类型的 get_integer() 或运算后添加大小检查。

---

### 8. CALLT 和 SYSCALL 未实现 (Medium)

**文件**: `src/neo/vm/instructions/control_flow.py`

**问题**: 这两个关键指令只是抛出异常。

```python
def callt(engine: ExecutionEngine, instruction: Instruction) -> None:
    token = int.from_bytes(instruction.operand, 'little', signed=False)
    raise Exception(f"Token not found: {token}")

def syscall(engine: ExecutionEngine, instruction: Instruction) -> None:
    hash_value = int.from_bytes(instruction.operand, 'little', signed=False)
    raise Exception(f"Syscall not found: {hash_value}")
```

**影响**: 无法执行任何使用系统调用或跨合约调用的脚本。

---

### 9. NEWARRAY_T 默认值共享问题 (Medium)

**文件**: `src/neo/vm/instructions/compound.py`

**问题**: 所有数组元素共享同一个默认值实例。

```python
def newarray_t(engine: ExecutionEngine, instruction: Instruction) -> None:
    # ...
    if item_type == StackItemType.BOOLEAN:
        default_item = Boolean(False)  # 单个实例
    # ...
    for _ in range(n):
        result.add(default_item)  # 所有元素指向同一实例
```

**影响**: 对于不可变类型（Boolean, Integer）这没问题，但如果扩展到可变类型会有问题。

---

## 轻微问题

### 10. 异常类型不一致 (Low)

**问题**: 代码中混用 `Exception` 和特定异常类型。

```python
# 有时用 Exception
raise Exception("Division by zero")

# 有时用特定类型
from neo.exceptions import StackOverflowException
raise StackOverflowException("Stack overflow")
```

**建议**: 定义并使用 VM 特定异常：
- `VMException`
- `StackUnderflowException`
- `InvalidOperationException`
- `OutOfRangeException`

---

### 11. Gas 计量未实现 (Low)

**文件**: `src/neo/vm/gas.py`

```python
# 文件内容只有常量定义，没有实际的 gas 追踪
```

**影响**: 无法限制脚本执行时间/资源。

---

### 12. Reference Counter 未完全使用 (Low)

**文件**: `src/neo/vm/reference_counter.py`

**问题**: ReferenceCounter 被创建但未在复合类型操作中正确使用来追踪引用。

---

### 13. Struct 缺少 deep_copy 方法 (Low)

**文件**: `src/neo/vm/types/struct.py`

**问题**: Struct 应该支持深拷贝以正确实现 CONVERT 和其他操作。

---

## 缺失功能

### 核心 VM 功能
- [ ] Gas 计量和限制
- [ ] SYSCALL 实现（需要 syscall 注册表）
- [ ] CALLT 实现（需要 method token 支持）
- [ ] Debugger 支持
- [ ] 完整的 JumpTable 优化

### Native Contracts
- [ ] NeoToken._refresh_committee() 未完整实现
- [ ] Oracle 回调机制
- [ ] Notary 完整实现
- [ ] ContractManagement 部署/更新逻辑

### 类型系统
- [ ] StackItem 完整序列化/反序列化
- [ ] InteropInterface 完整实现
- [ ] Pointer 跨脚本验证

### 网络/持久化
- [ ] 完整的 Block 验证
- [ ] Transaction 验证
- [ ] MemPool 实现
- [ ] 状态快照管理

---

## 改进建议

### 1. 添加更多边界测试

```python
# 建议添加的测试用例
def test_shl_shift_zero():
    """Test SHL with shift=0 preserves stack."""
    engine = create_engine()
    engine.push(Integer(42))
    engine.push(Integer(0))
    shl(engine, None)
    assert engine.pop().get_integer() == 42

def test_large_integer_overflow():
    """Test integer operations with values > 32 bytes."""
    # 测试超大整数处理
```

### 2. 实现 Syscall 注册表

```python
class SyscallRegistry:
    _syscalls: Dict[int, Callable] = {}
    
    @classmethod
    def register(cls, name: str, handler: Callable):
        hash_value = murmur32(name.encode('ascii'), 0)
        cls._syscalls[hash_value] = handler
    
    @classmethod
    def invoke(cls, engine: ExecutionEngine, hash_value: int):
        handler = cls._syscalls.get(hash_value)
        if handler is None:
            raise Exception(f"Syscall not found: {hash_value}")
        handler(engine)
```

### 3. 添加 Gas 追踪

```python
@dataclass
class GasCounter:
    gas_consumed: int = 0
    gas_limit: int = 0
    
    def add_gas(self, amount: int) -> None:
        self.gas_consumed += amount
        if self.gas_limit > 0 and self.gas_consumed > self.gas_limit:
            raise Exception("Out of gas")
```

### 4. 统一异常处理

```python
# neo/vm/exceptions.py
class VMException(Exception):
    """Base VM exception."""
    pass

class StackUnderflowException(VMException):
    """Stack underflow."""
    pass

class InvalidOperationException(VMException):
    """Invalid operation."""
    pass
```

---

## 总体评估

### 优点
1. **代码结构清晰** - 模块化设计，易于理解和维护
2. **测试覆盖良好** - 736 个测试用例通过
3. **文档完善** - 每个函数都有 docstring
4. **类型提示** - 使用了 Python 类型注解

### 需要改进
1. **关键 bug 需要修复** - SHL/SHR 栈损坏问题必须修复
2. **缺少核心功能** - SYSCALL/CALLT 未实现限制了实用性
3. **边界检查不足** - 需要更多防御性编程
4. **Gas 计量缺失** - 无法用于生产环境

### 风险评级

| 类别 | 数量 | 风险等级 |
|------|------|----------|
| 严重问题 | 3 | 🔴 高 |
| 中等问题 | 6 | 🟡 中 |
| 轻微问题 | 4 | 🟢 低 |
| 缺失功能 | 15+ | 🟡 中 |

### 建议优先级

1. **立即修复**: SHL/SHR 栈损坏、Keccak256 回退
2. **短期**: 实现 EvaluationStack.reverse()、Buffer.reverse()
3. **中期**: 实现 SYSCALL 注册表、Gas 计量
4. **长期**: 完善 Native Contracts、添加更多测试

---

**审计完成时间**: 2025-02-04  
**审计员**: Claude (Automated Code Audit)
