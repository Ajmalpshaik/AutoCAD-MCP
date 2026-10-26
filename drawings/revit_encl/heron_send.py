"""Send a C# file to the connected Revit through the Heron bridge.

  python heron_send.py read  cs/probe.cs
  python heron_send.py admin cs/fam_x.cs  [key=value ...]
  python heron_send.py write cs/build.cs  [key=value ...]
"""
import json, os, sys, uuid
sys.path.insert(0, r"D:\06_Development\03_Heron\Heron Ai\mcp\client")
os.environ.setdefault("HERON_CLIENT_ID", "ajmal-pc")
import heron_bridge_client as hb

OPS = {"read": "run_fragment_read", "show": "run_fragment_show", "write": "run_fragment_write",
       "publish": "run_fragment_publish", "admin": "run_fragment_admin"}


def send(kind, path, values=None, apply_it=True, timeout=600):
    live, starting, stale, mism = hb.discover()
    if not live:
        raise SystemExit("No live Heron bridge (starting=%d)" % len(starting))
    br = live[0]
    src = open(path, encoding="utf-8").read()
    args = {"name": os.path.splitext(os.path.basename(path))[0], "source": src, "needs": [],
            "values": [{"name": k, "value": v} for k, v in (values or {}).items()]}
    if kind != "read" and apply_it:
        args["apply"] = "true"
    r = br.request(OPS[kind], op_args=args, idempotent=(kind == "read"), response_timeout=timeout)
    br.close()
    return r


if __name__ == "__main__":
    kind, path = sys.argv[1], sys.argv[2]
    vals = dict(a.split("=", 1) for a in sys.argv[3:])
    r = send(kind, path, vals)
    print(json.dumps(r, indent=1)[:6000])
