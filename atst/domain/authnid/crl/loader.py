from glob import glob
from itertools import zip_longest

from OpenSSL import crypto, SSL
from sqlalchemy.dialects.postgresql import insert

from atst.models import CRL
from atst.database import db


# from https://docs.python.org/3/library/itertools.html#itertools-recipes
def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


class Loader:
    def __init__(self, crl_dir):
        self.crl_dir = crl_dir

    def _parse_crl(self, crl_location):
        with open(crl_location, "rb") as crl_file:
            return crypto.load_crl(crypto.FILETYPE_ASN1, crl_file.read())

    def _get_serial_numbers(self, crl):
        revoked = crl.get_revoked()
        if revoked is None:
            return []
        else:
            return [(rev.get_serial().decode(),) for rev in revoked]

    # try this method: https://stackoverflow.com/a/13949654
    # use STDIN: https://www.citusdata.com/blog/2017/11/08/faster-bulk-loading-in-postgresql-with-copy/
    def _load_to_database(self, issuer, nums):
        stmnt = insert(CRL).values(nums).on_conflict_do_nothing()
        db.session.execute(stmnt)

    # do we need serial number with reference to the CA?
    def _load_crl(self, crl_location):
        crl = self._parse_crl(crl_location)
        nums = self._get_serial_numbers(crl)
        issuer = crl.get_issuer().hash()
        print(f"issuer: {crl.get_issuer()}, count: {len(nums)}")
        for chunk in grouper(nums, 1_000):
            chunk = [x for x in chunk if x is not None]
            self._load_to_database(issuer, chunk)

        db.session.commit()

    def load(self):
        for crl_location in glob(f"{self.crl_dir}/*.crl"):
            self._load_crl(crl_location)
