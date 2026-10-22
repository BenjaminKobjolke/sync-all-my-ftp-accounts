"""Real deploy tool reading a real PHP config; set FTP_SYNC_TEST_DEPLOY_TOOL to its folder."""

import os
from pathlib import Path

import pytest

from ftp_sync.models import FtpProtocol
from ftp_sync.stores.deploy_tool_store import DeployToolStore

TOOL = Path(os.getenv("FTP_SYNC_TEST_DEPLOY_TOOL", ""))
CONFIG = """<?php
$ftpServer = 'ftp.example.com';
$ftpUser = 'bob';
$ftpPassword = 'p@ss';
return array(
    array('name' => 'Web', 'git' => array('root' => 'r'),
        'ftp' => array('root' => '/', 'server' => $ftpServer, 'username' => $ftpUser,
            'password' => $ftpPassword)),
    array('name' => 'Vendor', 'git' => array('root' => 'r'),
        'ftp' => array('root' => '/vendor', 'server' => $ftpServer, 'username' => $ftpUser,
            'password' => $ftpPassword, 'transferType' => 'FTPS', 'port' => 990)),
);
"""

pytestmark = pytest.mark.skipif(
    not DeployToolStore(TOOL).is_available() or not os.getenv("FTP_SYNC_TEST_DEPLOY_TOOL"),
    reason="FTP_SYNC_TEST_DEPLOY_TOOL not set to a deploy tool with export_ftp.php",
)


def test_reads_config_through_the_deploy_tool(tmp_path: Path) -> None:
    config = tmp_path / "config_my-project.php"
    config.write_text(CONFIG, encoding="utf-8")

    web, vendor = DeployToolStore(TOOL, config).load()

    assert (web.name, web.host, web.user, web.password) == ("Web", "ftp.example.com", "bob", "p@ss")
    assert (web.protocol, web.port, web.remote_dir, web.folder) == (
        FtpProtocol.FTP,
        21,
        "",
        "",
    )
    assert (vendor.protocol, vendor.port, vendor.remote_dir) == (FtpProtocol.FTPS, 990, "/vendor")


def test_invalid_config_reports_the_deploy_tool_errors(tmp_path: Path) -> None:
    config = tmp_path / "config_broken.php"
    config.write_text(CONFIG.replace("$ftpServer = 'ftp.example.com'", "$ftpServer = ''"))

    with pytest.raises(RuntimeError, match="ftp->server"):
        DeployToolStore(TOOL, config).load()
