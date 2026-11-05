import time
import socket
import psutil

class NetworkSentinel:
    """
    Real-time Network Traffic & Bandwidth Sentinel.
    Audits active TCP/UDP ports, tracks socket bandwidth usage,
    and identifies background processes communicating externally.
    """
    def __init__(self):
        self._last_io = psutil.net_io_counters()
        self._last_time = time.time()
        self.known_safe_ports = {8080, 8765, 8766, 8767, 22, 53, 67, 68, 123}

    def get_bandwidth_rate(self) -> dict:
        """Calculates current upload and download transfer rate in KB/s."""
        now = time.time()
        current_io = psutil.net_io_counters()
        dt = max(0.1, now - self._last_time)

        rx_bytes_sec = (current_io.bytes_recv - self._last_io.bytes_recv) / dt
        tx_bytes_sec = (current_io.bytes_sent - self._last_io.bytes_sent) / dt

        self._last_io = current_io
        self._last_time = now

        return {
            "download_kb_s": round(rx_bytes_sec / 1024, 1),
            "upload_kb_s": round(tx_bytes_sec / 1024, 1),
            "total_received_mb": round(current_io.bytes_recv / (1024**2), 1),
            "total_sent_mb": round(current_io.bytes_sent / (1024**2), 1)
        }

    def scan_listening_ports(self) -> list:
        """Lists all local ports currently in LISTEN state with owning process."""
        results = []
        try:
            for conn in psutil.net_connections(kind="inet"):
                if conn.status == psutil.CONN_LISTEN:
                    pid = conn.pid
                    proc_name = "System"
                    if pid:
                        try:
                            proc_name = psutil.Process(pid).name()
                        except Exception:
                            proc_name = "Unknown"

                    ip, port = conn.laddr.ip, conn.laddr.port
                    proto = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
                    is_local_only = (ip in ["127.0.0.1", "::1", "localhost"])

                    results.append({
                        "protocol": proto,
                        "port": port,
                        "ip": ip,
                        "process": proc_name,
                        "pid": pid,
                        "is_local_only": is_local_only,
                        "is_expected": port in self.known_safe_ports
                    })
        except Exception as e:
            print(f"[NetworkSentinel] Port scan note: {e}")

        # Deduplicate
        seen = set()
        dedup = []
        for r in results:
            key = (r["protocol"], r["port"], r["pid"])
            if key not in seen:
                seen.add(key)
                dedup.append(r)

        return sorted(dedup, key=lambda x: x["port"])

    def scan_active_connections(self, max_items: int = 15) -> list:
        """Lists active ESTABLISHED internet connections and their processes."""
        active = []
        try:
            for conn in psutil.net_connections(kind="tcp"):
                if conn.status == psutil.CONN_ESTABLISHED and conn.raddr:
                    pid = conn.pid
                    proc_name = "Unknown"
                    if pid:
                        try:
                            proc_name = psutil.Process(pid).name()
                        except Exception:
                            pass

                    remote_ip = conn.raddr.ip
                    remote_port = conn.raddr.port
                    # Filter out local loopback
                    if remote_ip not in ["127.0.0.1", "::1"]:
                        active.append({
                            "process": proc_name,
                            "pid": pid,
                            "remote_ip": remote_ip,
                            "remote_port": remote_port
                        })
        except Exception:
            pass
        return active[:max_items]

    def audit_security_alert(self) -> dict:
        """Audits listening ports for unverified public interfaces."""
        listeners = self.scan_listening_ports()
        flagged = []
        for l in listeners:
            if not l["is_local_only"] and not l["is_expected"]:
                flagged.append(l)

        rate = self.get_bandwidth_rate()
        return {
            "has_warnings": len(flagged) > 0,
            "flagged_open_ports": flagged,
            "bandwidth": rate,
            "total_listeners": len(listeners)
        }

network_sentinel = NetworkSentinel()

