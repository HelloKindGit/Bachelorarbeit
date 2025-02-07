import os
import sys
import subprocess
import tempfile
import shutil

class SubmissionAnalyzer:
    def __init__(self, submission_path, test_suite_path):
        """
        :param submission_path: Pfad zum Ordner der Schülerabgabe (z.B. ./[ASSIGNMENT_PREFIX]/[StudentName])
        :param test_suite_path: Pfad zum Ordner der Testfälle (optional)
        """
        self.submission_path = submission_path
        self.test_suite_path = test_suite_path.strip() if test_suite_path else ""
        self.language = self.detect_language()

    #Momentan nur Python-Dateien unterstützt
    def detect_language(self):
        """
        Erkennt automatisch die verwendete Programmiersprache anhand der Dateiendungen.
        Falls mindestens eine Python-Datei (.py) gefunden wird, wird "python" zurückgegeben.
        """
        for root, dirs, files in os.walk(self.submission_path):
            for file in files:
                if file.lower().endswith(".py"):
                    return "python"
        return None

    #Führt alle Tests aus
    def run_unit_tests(self):
        """
        Führt Unit Tests aus, falls Testfälle vorhanden sind.
        """
        if not self.test_suite_path:
            return "Keine Testfälle bereitgestellt.\n", "", 0
        if self.language == "python":
            return self.run_python_unit_tests()
        else:
            return "Keine Unterstützung für die erkannte Sprache.", None, -1

    def run_python_unit_tests(self):
        """
        Führt Unit-Tests aus einer einzelnen Datei aus.
        Falls keine Test-Datei vorhanden ist, wird der Test-Abschnitt übersprungen.
        """
        if not os.path.exists(self.test_suite_path):
            return "Keine Testfälle bereitgestellt.\n", "", 0

        temp_dir = tempfile.mkdtemp()
        try:
            # Kopiere Schülercode in temporären Ordner
            submission_temp = os.path.join(temp_dir, "submission")
            shutil.copytree(self.submission_path, submission_temp, ignore=shutil.ignore_patterns(".git"))

            # Kopiere Test-Datei in das gleiche Verzeichnis wie den Schülercode
            test_file_name = os.path.basename(self.test_suite_path)
            test_file_temp_path = os.path.join(submission_temp, test_file_name)
            shutil.copy(self.test_suite_path, test_file_temp_path)

            # Führe Pytest im Schülerordner aus
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file_temp_path, "--maxfail=1", "--disable-warnings", "-q"],
                cwd=submission_temp,
                capture_output=True,
                text=True
            )

            return result.stdout, result.stderr, result.returncode
        finally:
            shutil.rmtree(temp_dir)

    #Führt statische Analyse aus
    def run_static_analysis(self):
        if self.language == "python":
            return self.run_python_static_analysis()
        else:
            return "Keine Unterstützung für die erkannte Sprache.", None, -1

    def run_python_static_analysis(self):
        result = subprocess.run(
            [sys.executable, "-m", "flake8", self.submission_path],
            capture_output=True,
            text=True
        )
        return result.stdout, result.stderr, result.returncode

    #Führt Code-Formatierung aus
    def run_code_formatting(self):
        if self.language == "python":
            return self.run_python_code_formatting()
        else:
            return "Keine Unterstützung für die erkannte Sprache.", None, -1

    def run_python_code_formatting(self):
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", self.submission_path],
            capture_output=True,
            text=True
        )
        return result.stdout, result.stderr, result.returncode
