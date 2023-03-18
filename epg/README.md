## python packages
```bash
pip3 install orjson gremlinpython networkx loguru
```

## Examples
```python
python3 epg/gen_epg_info.py --gremlin-url ws://172.17.0.10:8182/gremlin --tx 0x0742b138a78ad9bd5d0b55221d514637313bc64c40272ca98c8d0417a519e2e4 --graphml /exported-graphs/0x0742b138a78ad9bd5d0b55221d514637313bc64c40272ca98c8d0417a519e2e4.xml -o frontend/tmp
```