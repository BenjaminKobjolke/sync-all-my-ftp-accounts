"""Notepad++ NppFTP profiles (NppFTP.xml)."""

import xml.etree.ElementTree as ET
from pathlib import Path

from ftp_account_readers import is_nppftp_available, read_nppftp
from ftp_account_readers.helpers import unique_name
from ftp_account_readers.nppftp_password import encrypt

from ftp_sync import constants as c
from ftp_sync.backup import BackupCoordinator
from ftp_sync.models import AppKind, FtpAccount, FtpProtocol
from ftp_sync.stores.xml_file import child, write_root

_PROTOCOL_TO_NPP = {
    FtpProtocol.FTP: c.NPP_SECURITY_FTP,
    FtpProtocol.FTPS: c.NPP_SECURITY_FTPES,
    FtpProtocol.SFTP: c.NPP_SECURITY_SFTP,
}

# Attribute defaults NppFTP writes for a new profile (copied from a profile it created).
_PROFILE_DEFAULTS = {
    "askPassword": "0",
    "timeout": "30",
    "transferMode": "0",
    "connectionMode": "0",
    "dataPortMin": "10000",
    "dataPortMax": "32000",
    "listParams": "",
    "keyFile": "",
    "passphrase": "",
    "askPassphrase": "0",
    "useAgent": "0",
    "acceptedMethods": "1",
}


class NppFtpStore:
    kind = AppKind.NPPFTP

    def __init__(self, path: Path, backup: BackupCoordinator) -> None:
        self._path = path
        self._backup = backup

    def is_available(self) -> bool:
        return is_nppftp_available(self._path)

    def supports(self, protocol: FtpProtocol) -> bool:
        return True

    def load(self) -> list[FtpAccount]:
        return read_nppftp(self._path)

    def add(self, account: FtpAccount) -> None:
        self._backup.backup_file(self._path)
        tree = ET.parse(self._path)
        profiles = child(tree.getroot(), c.NPP_PROFILES)
        taken = {
            p.get("name", "")
            for p in profiles.findall(c.NPP_PROFILE)
            if p.get("parent", "") == account.folder
        }
        attributes = {
            "name": unique_name(account.name, taken),
            "parent": account.folder,
            "hostname": account.host,
            "port": str(account.port),
            "username": account.user,
            "password": encrypt(account.password),
            "securityMode": str(_PROTOCOL_TO_NPP[account.protocol]),
            "initialDir": account.remote_dir,
        }
        profile = ET.SubElement(profiles, c.NPP_PROFILE, {**attributes, **_PROFILE_DEFAULTS})
        ET.SubElement(profile, "Cache")
        ET.SubElement(profile, "FileTypes", asciiTypes="", binaryTypes="")
        write_root(tree, self._path, "    ")


