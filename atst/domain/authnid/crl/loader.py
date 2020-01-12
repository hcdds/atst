from glob import glob
from io import StringIO
from itertools import zip_longest

from OpenSSL import crypto, SSL
from sqlalchemy.dialects.postgresql import insert

from atst.models import CRL
from atst.database import db


CHUNK_SIZE = 10_000


# from https://docs.python.org/3/library/itertools.html#itertools-recipes
def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


# adapted from https://github.com/jmcarp/sqlalchemy-postgres-copy/blob/master/postgres_copy/__init__.py#L43-L81
def postgres_copy_from(source, dest, connection, columns=(), **flags):
    """Import a table from a file. For flags, see the PostgreSQL documentation
    at http://www.postgresql.org/docs/9.5/static/sql-copy.html.
    Examples: ::
        with open('/path/to/file.tsv') as fp:
            copy_from(fp, MyTable, conn)
        with open('/path/to/file.csv') as fp:
            copy_from(fp, MyModel, engine, format='csv')
    :param source: Source file pointer, in read mode
    :param dest: SQLAlchemy model or table
    :param engine_or_conn: SQLAlchemy engine, connection, or raw_connection
    :param columns: Optional tuple of columns
    :param **flags: Options passed through to COPY
    If an existing connection is passed to `engine_or_conn`, it is the caller's
    responsibility to commit and close.
    The `columns` flag can be set to a tuple of strings to specify the column
    order. Passing `header` alone will not handle out of order columns, it simply tells
    postgres to ignore the first line of `source`.
    """

    return connection


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
            return [rev.get_serial().decode() for rev in revoked]

    # try this method: https://stackoverflow.com/a/13949654
    # use STDIN: https://www.citusdata.com/blog/2017/11/08/faster-bulk-loading-in-postgresql-with-copy/
    def _load_to_database(self, cursor, issuer, nums):
        str_io = self._to_csv_io(nums)
        copy = "COPY {} FROM STDIN WITH CSV".format("tmp_crls")
        cursor.copy_expert(copy, str_io)

    def _to_csv_io(self, data):
        data = [x for x in data if x is not None]
        data = "\n".join(data).strip()
        data_io = StringIO()
        data_io.write(data)
        data_io.seek(0)
        return data_io

    # do we need serial number with reference to the CA?
    def _load_crl(self, cursor, crl_location):
        crl = self._parse_crl(crl_location)
        nums = self._get_serial_numbers(crl)
        issuer = crl.get_issuer().hash()
        print(f"issuer: {crl.get_issuer()}, count: {len(nums)}")
        for chunk in grouper(nums, CHUNK_SIZE):
            self._load_to_database(cursor, issuer, chunk)

    def load(self):
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
CREATE TEMP TABLE tmp_crls
ON COMMIT DROP
AS
SELECT *
FROM crls
WITH NO DATA;
        """
        )
        for crl_location in glob(f"{self.crl_dir}/*.crl"):
            self._load_crl(cursor, crl_location)

        cursor.execute(
            """
INSERT INTO crls
SELECT *
FROM tmp_crls
ON CONFLICT DO NOTHING
"""
        )
        conn.commit()
        cursor.close()
        conn.close()
