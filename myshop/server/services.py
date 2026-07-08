from mcstatus import JavaServer

def get_minecraft_server_status(server_ip, server_port=25565):
    """
    دریافت وضعیت سرور ماینکرفت با استفاده از mcstatus
    """
    try:
        server = JavaServer.lookup(f"{server_ip}:{server_port}")
        status = server.status()

        return {
            "online_players": status.players.online if status.players else 0,
            "max_players": status.players.max if status.players else 0,
            "latency": round(status.latency or 0, 2),
            "server_ip": server_ip,
            "error": None,
        }
    except Exception as e:
        return {
            "error": f"سرور در دسترس نیست: {str(e)} ❌",
            "server_ip": server_ip,
            "online_players": 0,
            "max_players": 0,
            "latency": 0,
        }