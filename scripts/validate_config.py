"""Load a rendered MapProxy configuration the way production does and ask it for its
capabilities.

Runs inside the swi-mapproxy image (see .github/workflows/validate-config.yml). Production
starts uwsgi with ``make_wsgi_app('/mapproxy/config/mapproxy.yaml')``; if that call fails,
MapProxy does not start. The WMS and WMTS capabilities documents are built from the
layers, caches and grids, so asking for them checks that those references resolve. No
upstream service and no Redis server is contacted.

Limit: MapProxy only builds the caches and sources that a layer uses, so an unused one is
not checked.

Usage: validate_config.py RENDERED_MAPPROXY_YAML
"""

import sys

from mapproxy.wsgiapp import make_wsgi_app
from werkzeug.test import Client

CHECKS = (
    ("WMS capabilities", "/service?REQUEST=GetCapabilities&SERVICE=WMS"),
    ("WMTS capabilities", "/wmts/1.0.0/WMTSCapabilities.xml"),
)


def main(path):
    client = Client(make_wsgi_app(path, ignore_config_warnings=False))
    failed = False
    for name, url in CHECKS:
        response = client.get(url)
        ok = response.status_code == 200 and response.data.lstrip().startswith(b"<")
        print(f"{'OK  ' if ok else 'FAIL'} {name} ({response.status_code}, {len(response.data)} bytes)")
        failed = failed or not ok
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
