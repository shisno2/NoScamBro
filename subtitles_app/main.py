import sys
import os
import ssl

# Set Hugging Face cache to D: drive if available to preserve C: drive space
if os.path.exists("D:\\"):
    os.environ["HF_HOME"] = "D:\\huggingface_cache"

# Bypass SSL issues for model downloading
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

os.environ["PYTHONHTTPSVERIFY"] = "0"
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

try:
    import urllib3
    urllib3.disable_warnings()
except Exception:
    pass

try:
    import httpx
    _orig_httpx = httpx.Client.__init__
    def _patched_httpx(self, *args, **kwargs):
        kwargs["verify"] = False
        return _orig_httpx(self, *args, **kwargs)
    httpx.Client.__init__ = _patched_httpx
except Exception:
    pass

try:
    import requests
    _orig_req = requests.Session.__init__
    def _patched_req(self, *args, **kwargs):
        _orig_req(self, *args, **kwargs)
        self.verify = False
    requests.Session.__init__ = _patched_req
except Exception:
    pass

# Ensure current directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

if __name__ == "__main__":
    from gui import main
    main()
