from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "infra" / "scripts" / "install_collector_demo_api.sh"


class CollectorDemoApiServiceRestartTests(unittest.TestCase):
    def test_replaced_service_is_explicitly_restarted_before_health_validation(self):
        source = INSTALLER.read_text(encoding="utf-8")
        install_app = source.index('install -o root -g servicetracer -m 0640 "$SOURCE_ROOT/demo_api/standalone_server.py"')
        write_env = source.index('cat > "$ENV_FILE"')
        write_unit = source.index('cat > "/etc/systemd/system/${SERVICE_NAME}"')
        daemon_reload = source.index("systemctl daemon-reload")
        enable = source.index('systemctl enable "$SERVICE_NAME"')
        restart = source.index('systemctl restart "$SERVICE_NAME"')
        active = source.index('systemctl is-active --quiet "$SERVICE_NAME"')
        health = source.index('https://${PUBLIC_FQDN}/api/health')

        self.assertLess(install_app, write_env)
        self.assertLess(write_env, write_unit)
        self.assertLess(write_unit, daemon_reload)
        self.assertLess(daemon_reload, enable)
        self.assertLess(enable, restart)
        self.assertLess(restart, active)
        self.assertLess(active, health)

    def test_enable_now_cannot_substitute_for_restart(self):
        source = INSTALLER.read_text(encoding="utf-8")
        self.assertNotIn('systemctl enable --now "$SERVICE_NAME"', source)
        self.assertIn(
            "enable --now does not restart an already-running process",
            source,
        )


if __name__ == "__main__":
    unittest.main()
