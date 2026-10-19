import json
from pathlib import Path

import pytest

from ftp_sync.backup import BackupCoordinator
from ftp_sync.models import FtpProtocol
from ftp_sync.stores import nppftp_password
from ftp_sync.stores.account_store import AccountStore
from ftp_sync.stores.filezilla_store import FileZillaStore
from ftp_sync.stores.fman_store import FmanStore
from ftp_sync.stores.nppftp_store import NppFtpStore
from tests.conftest import make_account

FILEZILLA_XML = """<?xml version="1.0"?>
<FileZilla3 version="3.70.6" platform="windows">
\t<Servers>
\t\t<Folder expanded="1">Clients<Server>
\t\t\t\t<Host>a.example</Host><Port>2121</Port><Protocol>4</Protocol><Type>0</Type>
\t\t\t\t<User>alice</User><Pass encoding="base64">c2VjcmV0</Pass><Logontype>1</Logontype>
\t\t\t\t<Name>Site A</Name><RemoteDir>1 0 3 www 4 html</RemoteDir>
\t\t\t</Server>
\t\t</Folder>
\t\t<Server><Host>b.example</Host><Port>22</Port><Protocol>1</Protocol>
\t\t\t<User>bob</User><Name>B</Name></Server>
\t</Servers>
</FileZilla3>
"""

NPPFTP_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<NppFTP defaultCache="x" outputShown="1">
    <Profiles>
        <Profile name="n1" parent="Clients" hostname="n.example" port="21" username="nina"
            password="{password}" securityMode="2" initialDir="/srv">
            <Cache />
            <FileTypes asciiTypes="" binaryTypes="" />
        </Profile>
    </Profiles>
</NppFTP>
"""


@pytest.fixture
def filezilla(tmp_path: Path, backup: BackupCoordinator) -> FileZillaStore:
    path = tmp_path / "sitemanager.xml"
    path.write_text(FILEZILLA_XML, encoding="utf-8")
    return FileZillaStore(path, backup)


@pytest.fixture
def nppftp(tmp_path: Path, backup: BackupCoordinator) -> NppFtpStore:
    path = tmp_path / "NppFTP.xml"
    path.write_text(NPPFTP_XML.format(password=nppftp_password.encrypt("npw")), encoding="utf-8")
    return NppFtpStore(path, backup)


@pytest.fixture
def fman(tmp_path: Path, backup: BackupCoordinator) -> FmanStore:
    path = tmp_path / "bookmarks.json"
    data = {
        "ftp://My Site": ["ftp://fred:f%40pw@f.example:2100", "/pub", "https://web"],
        "ftp://plain": ["ftp://u:p@plain.example", ""],
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    return FmanStore(path, backup)


def test_filezilla_load(filezilla: FileZillaStore) -> None:
    a, b = filezilla.load()
    assert (a.name, a.folder, a.host, a.port, a.user, a.password) == (
        "Site A",
        "Clients",
        "a.example",
        2121,
        "alice",
        "secret",
    )
    assert a.protocol is FtpProtocol.FTPS
    assert a.remote_dir == "/www/html"
    assert (b.protocol, b.password, b.folder, b.remote_dir) == (FtpProtocol.SFTP, "", "", "")


def test_nppftp_load(nppftp: NppFtpStore) -> None:
    (n,) = nppftp.load()
    assert (n.name, n.folder, n.host, n.user, n.password) == (
        "n1",
        "Clients",
        "n.example",
        "nina",
        "npw",
    )
    assert (n.protocol, n.remote_dir) == (FtpProtocol.FTPS, "/srv")


def test_fman_load(fman: FmanStore) -> None:
    site, plain = fman.load()
    assert (site.name, site.host, site.port, site.user, site.password, site.remote_dir) == (
        "My Site",
        "f.example",
        2100,
        "fred",
        "f@pw",
        "/pub",
    )
    assert (plain.port, plain.remote_dir) == (21, "")


def test_fman_rejects_sftp(fman: FmanStore) -> None:
    assert not fman.supports(FtpProtocol.SFTP)
    assert fman.supports(FtpProtocol.FTPS)


@pytest.mark.parametrize("store_name", ["filezilla", "nppftp", "fman"])
@pytest.mark.parametrize("protocol", [FtpProtocol.FTP, FtpProtocol.FTPS])
@pytest.mark.parametrize("password", ["p@ss:w/rd ä", ""])  # "" = All-Inkl source, no password
def test_add_roundtrip_and_backup(
    request: pytest.FixtureRequest,
    tmp_path: Path,
    store_name: str,
    protocol: FtpProtocol,
    password: str,
) -> None:
    store: AccountStore = request.getfixturevalue(store_name)
    account = make_account(
        protocol=protocol, folder="New/Sub", remote_dir="/var/www", port=990, password=password
    )
    before = len(store.load())
    store.add(account)
    store.add(account)  # second add of same name must not overwrite the first
    loaded = store.load()
    assert len(loaded) == before + 2
    added = [a for a in loaded if a.host == account.host]
    assert {a.name for a in added} == {"site", "site (2)"}
    first = added[0]
    assert (first.user, first.password, first.port, first.protocol, first.remote_dir) == (
        account.user,
        account.password,
        990,
        protocol,
        "/var/www",
    )
    if store_name != "fman":
        assert first.folder == "New/Sub"
    assert len(list((tmp_path / "backups").rglob("*.*"))) == 1  # one backup per run


def test_filezilla_add_reuses_existing_folder(filezilla: FileZillaStore) -> None:
    filezilla.add(make_account(folder="Clients"))
    assert {a.folder for a in filezilla.load()} == {"Clients", ""}


def test_missing_file_is_unavailable(tmp_path: Path, backup: BackupCoordinator) -> None:
    assert not FileZillaStore(tmp_path / "nope.xml", backup).is_available()
