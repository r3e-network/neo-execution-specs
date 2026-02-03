# Neo Execution Specs 审计报告

**审计日期**: 2025-02-04  
**项目版本**: Neo N3 v3.9.1 Python 实现  
**审计范围**: VM 指令、Native Contracts、类型系统、边界条件  
**测试状态**: 828 tests passing, 1 skipped

---

## 修复状态摘要

| 问题 | 严重程度 | 状态 |
|------|----------|------|
| SHL/SHR 栈损坏 | Critical | ✅ 已修复 |
| Keccak256 回退错误 | Critical | ✅ 已修复 |
| PACKMAP 键值顺序 | Critical | ✅ 已验证正确 |
| EvaluationStack.reverse() | Medium | ✅ 已实现 |
| Buffer.reverse() | Medium | ✅ 已实现 |
| 栈下溢检查 | Medium | ✅ 已添加 |
| BigInteger 大小限制 | Medium | ⏳ 待处理 |
| CALLT/SYSCALL | Medium | ⏳ 待处理 (需要更大改动) |

---

## 严重问题

### 1. SHL/SHR 指令栈损坏 (Critical) ✅ 已修复

**文件**: `src/neo/vm/instructions/numeric.py`

**问题**: 当 shift 值为 0 时，函数提前返回但没有将原始值推回栈中，导致栈损坏。

**修复**: 现在先 pop 两个值，再检查 shift=0，确保栈状态正确。

**已添加测试**: `tests/vm/test_numeric_ops.py::test_shl_shift_zero`, `test_shr_shift_zero`

---

### 2. PACKMAP 键值顺序 (Critical) ✅ 已验证正确

**文件**: `src/neo/vm/instructions/compound.py`

**原问题**: 怀疑 PACKMAP 中 key 和 value 的弹出顺序与 C# 实现相反。

**验证结果**: 经过测试验证，当前实现是正确的。C# 中先 pop key，后 pop value，Python 实现与此一致。

**已添加测试**: `tests/vm/test_compound_ops.py::TestPackMap`

---

### 3. Keccak256 回退实现错误 (Critical) ✅ 已修复

**文件**: `src/neo/native/crypto_lib.py`

**问题**: 回退使用 `hashlib.sha3_256`，但 SHA3-256 和 Keccak-256 是不同的算法！

**修复**: 移除错误的回退，现在会抛出明确的 ImportError 提示安装 pycryptodome。

---

## 中等问题

### 4. EvaluationStack.reverse() 方法缺失 (Medium) ✅ 已实现

**文件**: `src/neo/vm/evaluation_stack.py`

**修复**: 已实现 `reverse(n)` 方法，支持 REVERSE3, REVERSE4, REVERSEN 指令。

**已添加测试**: `tests/vm/test_evaluation_stack_extended.py`

---

### 5. Buffer.reverse() 方法缺失 (Medium) ✅ 已实现

**文件**: `src/neo/vm/types/buffer.py`

**修复**: 已实现 `reverse()` 方法，支持 REVERSEITEMS 指令对 Buffer 的操作。

**已添加测试**: `tests/vm/test_buffer.py`

---

### 6. 缺少栈大小检查 (Medium) ✅ 已添加

**文件**: `src/neo/vm/evaluation_stack.py`

**修复**: `pop()` 方法现在会检查栈是否为空，空栈时抛出 "Stack underflow" 异常。

**已添加测试**: `tests/vm/test_evaluation_stack_extended.py::test_pop_empty_stack_raises`

---

### 7. BigInteger 大小限制未强制执行 (Medium) ⏳ 待处理

**文件**: `src/neo/types/big_integer.py`

**问题**: `MAX_SIZE = 32` 定义了但未在运算中强制执行。

**C# 参考**: Neo VM 限制整数最大 32 字节 (256 位)。

---

### 8. CALLT 和 SYSCALL 未实现 (Medium) ⏳ 待处理

**文件**: `src/neo/vm/instructions/control_flow.py`

**问题**: 这两个关键指令只是抛出异常，需要实现 syscall 注册表。

---

### 9. NEWARRAY_T 默认值共享问题 (Medium)

**文件**: `src/neo/vm/instructions/compound.py`

**问题**: 所有数组元素共享同一个默认值实例。对于不可变类型没问题。

---

## 轻微问题

### 10. 异常类型不一致 (Low)

**问题**: 代码中混用 `Exception` 和特定异常类型。

### 11. Gas 计量未实现 (Low)

**文件**: `src/neo/vm/gas.py` - 只有常量定义，没有实际的 gas 追踪。

### 12. Reference Counter 未完全使用 (Low)

### 13. Struct 缺少 deep_copy 方法 (Low)

---

## 缺失功能

### 核心 VM 功能
- [ ] Gas 计量和限制
- [ ] SYSCALL 实现（需要 syscall 注册表）
- [ ] CALLT 实现（需要 method token 支持）

### Native Contracts
- [ ] NeoToken._refresh_committee() 未完整实现
- [ ] Oracle 回调机制
- [ ] ContractManagement 部署/更新逻辑

---

## 总体评估

### 修复后风险评级

| 类别 | 原数量 | 已修复 | 剩余 |
|------|--------|--------|------|
| 严重问题 | 3 | 3 | 0 |
| 中等问题 | 6 | 3 | 3 |
| 轻微问题 | 4 | 0 | 4 |

**所有严重问题已修复！**

---

**审计完成时间**: 2025-02-04  
**修复完成时间**: 2025-02-04  
**审计员**: Claude (Automated Code Audit)
