import sys
import os
from antyx.report import EDAReport
from antyx.server.server import run_server

def main():
    if len(sys.argv) < 3:
        print("Uso:")
        print("  python -m antyx report archivo.csv")
        sys.exit(1)

    command = sys.argv[1]

    if command == "report":
        file_path = sys.argv[2]

        if not os.path.exists(file_path):
            print(f"Error: el archivo '{file_path}' no existe.")
            sys.exit(1)

        # Generar el reporte
        report = EDAReport(file_path=file_path)
        output_path = "antyx_report.html"
        report.save_html(output_path)

        # Directorios necesarios para servir JSON y estáticos
        figs_dir = os.path.join(os.getcwd(), "figs")
        static_dir = os.path.join(os.getcwd(), "antyx", "static")

        # Lanzar servidor interno
        run_server(output_path, figs_dir, static_dir)

    else:
        print(f"Comando desconocido: {command}")
        print("Comandos disponibles: report")
        sys.exit(1)


if __name__ == "__main__":
    main()