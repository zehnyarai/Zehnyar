"""تنظیم محیط تست: پایگاه داده و فایل رتبه‌ها در پوشه‌ی موقت، بدون لمس data/app.db."""
import os
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_tmp = tempfile.mkdtemp(prefix="rz-test-")
os.environ["DATABASE_PATH"] = str(pathlib.Path(_tmp) / "test.db")
os.environ["CUTOFFS_PATH"] = str(pathlib.Path(_tmp) / "cutoffs.csv")
os.environ["APP_ENV"] = "development"
os.environ["ADMIN_PASSWORD"] = "test-pass"
os.environ["PUBLIC_BASE_URL"] = "http://testserver"
os.environ["FREE_RESULTS_LIMIT"] = "5"
os.environ.pop("ZARINPAL_MERCHANT_ID", None)
os.environ.pop("ALLOW_MOCK_PAYMENTS", None)

from app.db import init_db  # noqa: E402  (پس از تنظیم متغیرهای محیطی)

init_db()
