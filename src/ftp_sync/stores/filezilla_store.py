"""FileZilla site manager (sitemanager.xml). Passwords are plain base64."""

import base64
import xml.etree.ElementTree as ET
from pathlib import Path

from ftp_account_readers import is_filezilla_available, read_filezilla
from ftp_account_readers.helpers import unique_name

from ftp_sync import constants as c
from ftp_sync.backup import BackupCoordinator
from ftp_sync.models import AppKind, FtpAccount, FtpProtocol
from ftp_sync.stores.xml_file import child, write_root

_PROTOCOL_TO_FZ = {
    FtpProtocol.FTP: c.FZ_PROTOCOL_FTP,
    FtpProtocol.FTPS: c.FZ_PROTOCOL_FTPS_EXPLICIT,
    FtpProtocol.SFTP: c.FZ_PROTOCOL_SFTP,
}


class FileZillaStore:
    kind = AppKind.FILEZILLA

    def __init__(self, path: Path, backup: BackupCoordinator) -> None:
        self._path = path
        self._backup = backup

    def is_available(self) -> bool:
        return is_filezilla_available(self._path)

    def supports(self, protocol: FtpProtocol) -> bool:
        return True

    def load(self) -> list[FtpAccount]:
        return read_filezilla(self._path)

    def add(self, account: FtpAccount) -> None:
        self._backup.backup_file(self._path)
        tree = ET.parse(self._path)
        parent = child(tree.getroot(), c.FZ_SERVERS)
        for name in filter(None, account.folder.split(c.FOLDER_SEPARATOR)):
            parent = _folder(parent, name)
        taken = {s.findtext(c.FZ_NAME, "") for s in parent.findall(c.FZ_SERVER)}
        server = ET.SubElement(parent, c.FZ_SERVER)
        fields = [
            (c.FZ_HOST, account.host),
            (c.FZ_PORT, str(account.port)),
            (c.FZ_PROTOCOL, str(_PROTOCOL_TO_FZ[account.protocol])),
            (c.FZ_TYPE, "0"),
            (c.FZ_USER, account.user),
            (c.FZ_PASS, base64.b64encode(account.password.encode("utf-8")).decode("ascii")),
            (c.FZ_LOGONTYPE, str(c.FZ_LOGONTYPE_NORMAL)),
            (c.FZ_NAME, unique_name(account.name, taken)),
            (c.FZ_REMOTE_DIR, encode_remote_dir(account.remote_dir)),
        ]
        for tag, text in fields:
            ET.SubElement(server, tag).text = text
        server.find(c.FZ_PASS).set("encoding", "base64")  # type: ignore[union-attr]
        write_root(tree, self._path, "\t")


def _folder(parent: ET.Element, name: str) -> ET.Element:
    for folder in parent.findall(c.FZ_FOLDER):
        if (folder.text or "").strip() == name:
            return folder
    folder = ET.SubElement(parent, c.FZ_FOLDER, expanded="1")
    folder.text = name
    return folder


def encode_remote_dir(path: str) -> str:
    segments = [s for s in path.split("/") if s]
    if not segments:
        return ""
    return "1 0 " + " ".join(f"{len(s)} {s}" for s in segments)
