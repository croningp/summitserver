# SummitServer

In-house server for communication with [summit](https://github.com/sustainable-processes/summit) benchmark library (mainly it's `Strategies` module).

## Installation
Install [summit](https://github.com/sustainable-processes/summit) following [installation](https://github.com/sustainable-processes/summit#installation) guidelines. Upon completion, clone current repo and simply install with `pip`:
```python
pip install -e .
```

## Usage
Run module using cli:
```bash
python -m summitserver --host HOST --port PORT
```
where HOST defaults to `dragonsoop2` and PORT to `12111`.

Or import and instantiate `SummitServer` class with `port` attribute and run its `main()` method.

```python
from summitserver import SummitServer

serv = SummitServer(port=12111)

serv.main()
```

Be sure to close server socket when done:

```python
serv.server.close()
```