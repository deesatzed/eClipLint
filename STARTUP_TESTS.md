# Startup tests

## 1) Pure Python repair (LLM)
Copy:
```python
x=1
 if x>0:
print(x)
```
Run:
```bash
./run_clipfix.sh
```
Paste: should become valid indented Python.

## 2) Bash heredoc containing Python
Copy:
```bash
PYTHONPATH=. python - <<'PY'
x=1
 if x>0:
print(x)
PY
```
Run:
```bash
./run_clipfix.sh
```
Paste: bash wrapper unchanged; python fixed inside.

## 3) JSON
Copy:
```json
{"a":1,"b":2}
```
Run:
```bash
./run_clipfix.sh --no-llm
```
Paste: pretty JSON.
