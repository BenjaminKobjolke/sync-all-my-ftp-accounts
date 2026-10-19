"""String and numeric constants shared across modules."""

FTP_DEFAULT_PORT = 21
SFTP_DEFAULT_PORT = 22

APP_LABELS = {
    "winscp": "WinSCP",
    "filezilla": "FileZilla",
    "nppftp": "Notepad++ (NppFTP)",
    "fman": "fman",
}

FOLDER_SEPARATOR = "/"

# Environment variables read by Settings
ENV_APPDATA = "APPDATA"
ENV_FILEZILLA_PATH = "FTP_SYNC_FILEZILLA_PATH"
ENV_NPPFTP_PATH = "FTP_SYNC_NPPFTP_PATH"
ENV_FMAN_PATH = "FTP_SYNC_FMAN_PATH"
ENV_WINSCP_KEY = "FTP_SYNC_WINSCP_KEY"
ENV_BACKUP_DIR = "FTP_SYNC_BACKUP_DIR"
ENV_LOG_LEVEL = "FTP_SYNC_LOG_LEVEL"

# Default store locations, relative to %APPDATA% (registry key relative to HKCU)
FILEZILLA_RELATIVE_PATH = r"FileZilla\sitemanager.xml"
NPPFTP_RELATIVE_PATH = r"Notepad++\plugins\config\NppFTP\NppFTP.xml"
FMAN_RELATIVE_PATH = r"fman\Plugins\User\Settings\FTP Bookmarks (Windows).json"
WINSCP_SESSIONS_KEY = r"Software\Martin Prikryl\WinSCP 2\Sessions"
DEFAULT_BACKUP_DIR = "backups"

# WinSCP registry values
WINSCP_HOST = "HostName"
WINSCP_PORT = "PortNumber"
WINSCP_USER = "UserName"
WINSCP_PASSWORD = "Password"
WINSCP_FS_PROTOCOL = "FSProtocol"
WINSCP_FTPS = "Ftps"
WINSCP_REMOTE_DIR = "RemoteDirectory"
WINSCP_FS_SFTP = 2
WINSCP_FS_FTP = 5
WINSCP_FTPS_NONE = 0
WINSCP_FTPS_EXPLICIT = 3
WINSCP_DEFAULT_SETTINGS_SESSION = "Default Settings"

# FileZilla sitemanager.xml
FZ_SERVERS = "Servers"
FZ_FOLDER = "Folder"
FZ_SERVER = "Server"
FZ_HOST = "Host"
FZ_PORT = "Port"
FZ_PROTOCOL = "Protocol"
FZ_TYPE = "Type"
FZ_USER = "User"
FZ_PASS = "Pass"
FZ_LOGONTYPE = "Logontype"
FZ_NAME = "Name"
FZ_REMOTE_DIR = "RemoteDir"
FZ_PROTOCOL_FTP = 0
FZ_PROTOCOL_SFTP = 1
FZ_PROTOCOL_FTPS_IMPLICIT = 3
FZ_PROTOCOL_FTPS_EXPLICIT = 4
FZ_LOGONTYPE_NORMAL = 1

# NppFTP.xml
NPP_PROFILES = "Profiles"
NPP_PROFILE = "Profile"
NPP_SECURITY_FTP = 0
NPP_SECURITY_FTPS = 1
NPP_SECURITY_FTPES = 2
NPP_SECURITY_SFTP = 3
NPP_DEFAULT_KEY = b"NppFTP00"

# fman bookmarks
FMAN_SCHEMES = {"ftp", "ftps"}
FMAN_DEFAULT_PATH = "/"
