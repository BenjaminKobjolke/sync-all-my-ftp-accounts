"""FileZilla site manager (sitemanager.xml). Passwords are plain base64."""

import base64
import xml.etree.ElementTree as ET
from pathlib import Path

from ftp_sync import constants as c
from ftp_sync.backup import BackupCoordinator
from ftp_sync.models import AppKind, FtpAccount, FtpProtocol
from ftp_sync.stores.account_store import join_folder, parse_port, unique_name
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
        return self._path.is_file()

    def supports(self, protocol: FtpProtocol) -> bool:
        return True

    def load(self) -> list[FtpAccount]:
        servers = ET.parse(self._path).getroot().find(c.FZ_SERVERS)
        return [] if servers is None else list(_walk(servers, ""))

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


def _walk(element: ET.Element, folder: str) -> list[FtpAccount]:
    accounts: list[FtpAccount] = []
    for node in element:
        if node.tag == c.FZ_FOLDER:
            accounts += _walk(node, join_folder(folder, (node.text or "").strip()))
        elif node.tag == c.FZ_SERVER and node.findtext(c.FZ_HOST):
            accounts.append(_parse_server(node, folder))
    return accounts


def _parse_server(node: ET.Element, folder: str) -> FtpAccount:
    protocol = _protocol(node.findtext(c.FZ_PROTOCOL, ""))
    host = node.findtext(c.FZ_HOST, "")
    pass_node = node.find(c.FZ_PASS)
    password = ""
    if pass_node is not None and pass_node.text:
        password = pass_node.text
        if pass_node.get("encoding") == "base64":
            password = base64.b64decode(password).decode("utf-8")
    return FtpAccount(
        name=node.findtext(c.FZ_NAME) or host,
        host=host,
        user=node.findtext(c.FZ_USER, ""),
        password=password,
        port=parse_port(node.findtext(c.FZ_PORT), protocol),
        protocol=protocol,
        folder=folder,
        remote_dir=decode_remote_dir(node.findtext(c.FZ_REMOTE_DIR, "")),
    )


def _protocol(value: str) -> FtpProtocol:
    if value == str(c.FZ_PROTOCOL_SFTP):
        return FtpProtocol.SFTP
    if value in (str(c.FZ_PROTOCOL_FTPS_IMPLICIT), str(c.FZ_PROTOCOL_FTPS_EXPLICIT)):
        return FtpProtocol.FTPS
    return FtpProtocol.FTP


def _folder(parent: ET.Element, name: str) -> ET.Element:
    for folder in parent.findall(c.FZ_FOLDER):
        if (folder.text or "").strip() == name:
            return folder
    folder = ET.SubElement(parent, c.FZ_FOLDER, expanded="1")
    folder.text = name
    return folder


def decode_remote_dir(value: str) -> str:
    """FileZilla CServerPath: '<type> <prefix-len> [<len> <segment>]...', e.g. '1 0 3 www'."""
    parts = value.split(" ", 2)
    if len(parts) < 3:
        return ""
    rest, segments = parts[2], []
    try:
        while rest:
            length_text, rest = rest.split(" ", 1)
            length = int(length_text)
            segments.append(rest[:length])
            rest = rest[length + 1 :]
    except ValueError:
        return ""
    return "/" + "/".join(segments)


def encode_remote_dir(path: str) -> str:
    segments = [s for s in path.split("/") if s]
    if not segments:
        return ""
    return "1 0 " + " ".join(f"{len(s)} {s}" for s in segments)
