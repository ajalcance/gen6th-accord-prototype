"""Fixed source policy; packaging must provide these real files in a signed image."""

from pathlib import Path

UID = 100
CONFIG = Path("/etc/accord-scanner")
DATABASE = Path("/var/lib/accord-scanner")
TEMPORARY = Path("/var/lib/accord-scanner-tmp")
SEEDS = ("main.cvd", "daily.cvd", "bytecode.cvd")
MAX_DATABASE_BYTES = 256 * 1024 * 1024
CLAMD = b"""Foreground yes
User clamav
DatabaseDirectory /var/lib/accord-scanner
TemporaryDirectory /var/lib/accord-scanner-tmp
TCPAddr 127.0.0.1
TCPSocket 3310
StreamMaxLength 10M
MaxThreads 2
MaxQueue 4
MaxConnectionQueueLength 4
ReadTimeout 5
CommandReadTimeout 5
SendBufTimeout 1000
IdleTimeout 5
MaxScanTime 20000
MaxScanSize 50M
MaxFileSize 10M
MaxRecursion 16
MaxFiles 1000
AlertExceedsMax yes
OfficialDatabaseOnly yes
Bytecode yes
BytecodeSecurity TrustSigned
BytecodeUnsigned no
ConcurrentDatabaseReload yes
SelfCheck 60
"""
FRESHCLAM = b"""Foreground yes
DatabaseOwner clamav
DatabaseDirectory /var/lib/accord-scanner
DatabaseMirror database.clamav.net
DNSDatabaseInfo current.cvd.clamav.net
Checks 12
ConnectTimeout 5
ReceiveTimeout 10
TestDatabases yes
Bytecode yes
"""
CONFIGURATIONS = {
    "clamd.conf": CLAMD,
    "bootstrap.conf": FRESHCLAM,
    "freshclam.conf": FRESHCLAM + b"NotifyClamd /etc/accord-scanner/clamd.conf\n",
}
EXECUTABLES = ("/usr/sbin/clamd", "/usr/bin/freshclam", "/usr/bin/sigtool", "/usr/bin/clamscan")
