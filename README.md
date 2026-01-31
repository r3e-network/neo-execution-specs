# Neo N3 Execution Specs

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A Python reference implementation of the Neo N3 protocol, prioritizing **readability** over performance.

## Overview

This project provides an executable specification for:
- **NeoVM** - Neo Virtual Machine opcodes and execution
- **ApplicationEngine** - Smart contract execution environment
- **Native Contracts** - Built-in system contracts

## Installation

```bash
pip install neo-execution-specs
```

## Development

```bash
# Clone repository
git clone https://github.com/neo-project/neo-execution-specs.git
cd neo-execution-specs

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## Project Structure

```
src/neo/
├── vm/                 # Pure NeoVM layer
├── contract/           # NEF, Manifest
├── smartcontract/      # ApplicationEngine, Syscalls
└── native/             # Native Contracts
```

## License

MIT License - see [LICENSE](LICENSE) for details.
