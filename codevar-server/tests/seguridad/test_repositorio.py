"""CP-10. El repositorio no debe versionar bases de datos con datos reales."""
import subprocess


def test_cp10_repositorio_sin_bases_de_datos():
    rastreados = subprocess.run(["git", "ls-files", "*.db", "*.sqlite", "*.sqlite3"],
                                capture_output=True, text=True, check=True).stdout.split()
    assert rastreados == []
