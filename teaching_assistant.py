import os
import subprocess
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from github import Github
from dotenv import load_dotenv
from transformers import pipeline

from submission_analyzer import SubmissionAnalyzer

import torch
device = "cuda:0" if torch.cuda.is_available() else "cpu"

class Teaching_Assistant(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Teaching Assistent")

        #Variablen für Eingabefelder
        self.token_var = tk.StringVar()
        self.org_var = tk.StringVar()
        self.prefix_var = tk.StringVar()
        self.test_suite_var = tk.StringVar()

        #Für Datei-Uploads der Aufgabenstellung und Musterlösung
        self.assignment_description_content = ""
        self.assignment_description_filename = ""
        self.sample_solution_content = ""
        self.sample_solution_filename = ""

        #Variablen für Bewertung-Gewichtungen (der Standard ist: Funktionalität 50%, Codequalität 30%, Dokumentation 20%)
        self.weight_functionality = tk.IntVar(value=50)
        self.weight_code_quality = tk.IntVar(value=30)
        self.weight_documentation = tk.IntVar(value=20)

        #Liste für Schülernamen (nach Download befüllt)
        self.student_names = []
        self.selected_student_var = tk.StringVar()

        #Zähler für gedownloadete Repos
        self.repo_count = 0

        #Variablen für die Speicherung des letzten Analyseergebnisses und AI-Feedbacks
        self.last_analysis_result = ""
        self.last_ai_feedback = ""

        self.create_widgets()

    def create_widgets(self):
        input_frame = ttk.Frame(self)
        input_frame.pack(padx=10, pady=10, fill=tk.X)

        #Zeile 1: GITHUB_TOKEN (entweder Umgebungsvariable setzen oder hier eintragen)
        ttk.Label(input_frame, text="GITHUB-TOKEN (optional):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(input_frame, textvariable=self.token_var, width=50).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        #Zeile 2: Name der GitHub Organisation
        ttk.Label(input_frame, text="ORG-NAME:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(input_frame, textvariable=self.org_var, width=25).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        #Zeile 3: Name des GitHub Classroom Assignments (klein geschrieben)
        ttk.Label(input_frame, text="Assignment Name:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(input_frame, textvariable=self.prefix_var, width=25).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        #Zeile 4: Code Tests (optional)
        ttk.Label(input_frame, text="Test Datei (optional):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        test_suite_frame = ttk.Frame(input_frame)
        test_suite_frame.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        self.test_suite_entry = ttk.Entry(test_suite_frame, textvariable=self.test_suite_var, width=40)
        self.test_suite_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(test_suite_frame, text="Browse...", command=self.upload_test).pack(side=tk.LEFT)

        #Zeile 5: Student für Analyse (Dropdown)
        ttk.Label(input_frame, text="Student für Analyse:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.student_combobox = ttk.Combobox(input_frame, textvariable=self.selected_student_var, state="readonly", width=23)
        self.student_combobox.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)

        #Zeile 6: Aufgabenstellung Datei-Upload
        ttk.Label(input_frame, text="Aufgabenstellung Datei:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        assignment_frame = ttk.Frame(input_frame)
        assignment_frame.grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Button(assignment_frame, text="Upload...", command=self.upload_assignment_description).pack(side=tk.LEFT)
        self.assignment_filename_label = ttk.Label(assignment_frame, text="Keine Datei ausgewählt")
        self.assignment_filename_label.pack(side=tk.LEFT, padx=5)

        #Zeile 7: Musterlösung Datei-Upload (optional)
        ttk.Label(input_frame, text="Musterlösung Datei (optional):").grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
        sample_frame = ttk.Frame(input_frame)
        sample_frame.grid(row=6, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Button(sample_frame, text="Upload...", command=self.upload_sample_solution).pack(side=tk.LEFT)
        self.sample_filename_label = ttk.Label(sample_frame, text="Keine Datei ausgewählt")
        self.sample_filename_label.pack(side=tk.LEFT, padx=5)

        #Zeile 8: Gewichtung für Bewertung
        weight_frame = ttk.LabelFrame(input_frame, text="Bewertungsgewichtung (%)")
        weight_frame.grid(row=7, column=0, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=5)
        ttk.Label(weight_frame, text="Funktionalität:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Spinbox(weight_frame, from_=0, to=100, textvariable=self.weight_functionality, width=5).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        ttk.Label(weight_frame, text="Codequalität:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        ttk.Spinbox(weight_frame, from_=0, to=100, textvariable=self.weight_code_quality, width=5).grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        ttk.Label(weight_frame, text="Dokumentation/Kommentare:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=2)
        ttk.Spinbox(weight_frame, from_=0, to=100, textvariable=self.weight_documentation, width=5).grid(row=0, column=5, sticky=tk.W, padx=5, pady=2)
        ttk.Label(weight_frame, text="(Gesamtsumme sollte idealerweise 100 ergeben)").grid(row=1, column=0, columnspan=6, sticky=tk.W, padx=5, pady=2)

        #Zeile 9: Log-Ausgabe
        ttk.Label(input_frame, text="Log-Ausgabe:").grid(row=8, column=0, sticky=tk.W, padx=5, pady=(10,2))
        self.log_text = scrolledtext.ScrolledText(input_frame, width=70, height=10, state='normal')
        self.log_text.grid(row=9, column=0, columnspan=2, padx=5, pady=5)

        #Zeile 10: Heruntergeladene Repos
        ttk.Label(input_frame, text="Heruntergeladene Repos:").grid(row=10, column=0, sticky=tk.W, padx=5, pady=(10,2))
        self.counter_label = ttk.Label(input_frame, text="0")
        self.counter_label.grid(row=10, column=1, sticky=tk.W, padx=5, pady=(10,2))

        #Zeile 11: Studenten (Account-Namen)
        ttk.Label(input_frame, text="Studenten (Account-Namen):").grid(row=11, column=0, sticky=tk.W, padx=5, pady=(10,2))
        self.students_text = scrolledtext.ScrolledText(input_frame, width=40, height=6, state='normal')
        self.students_text.grid(row=12, column=0, columnspan=2, padx=5, pady=5)

        #Button-Leiste
        button_frame = ttk.Frame(self)
        button_frame.pack(padx=10, pady=5, fill=tk.X)
        ttk.Button(button_frame, text="Download", command=self.on_download).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Dateien einlesen", command=self.on_read_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Analyse (ausgewählter Student)", command=self.on_analyze_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Analyse (alle)", command=self.on_analyze_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Generiere Feedback & Bewertung", command=self.on_generate_feedback_and_evaluation).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Beenden", command=self.on_exit).pack(side=tk.LEFT, padx=5)

    #Unit-Test Datei-Upload
    def upload_test(self):
        """
        Öffnet einen Datei-Dialog, um eine einzelne Unit-Test-Datei (.py) auszuwählen.
        Der Pfad der Datei wird in `test_suite_var` gespeichert.
        """
        filename = filedialog.askopenfilename(
            title="Unit Test Datei auswählen",
            filetypes=[("Python Dateien", "*.py"), ("Alle Dateien", "*.*")]
        )
        if filename:
            self.test_suite_var.set(filename)
            self.log(f"Unit Test Datei gesetzt: {filename}\n")

    #Aufgabenstellung Datei-Upload
    def upload_assignment_description(self):
        filename = filedialog.askopenfilename(title="Aufgabenstellung Datei auswählen",
                                              filetypes=[("Textdateien", "*.txt"), ("Alle Dateien", "*.*")])
        if filename:
            self.assignment_description_filename = filename
            self.assignment_filename_label.config(text=os.path.basename(filename))
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    self.assignment_description_content = f.read()
                self.log(f"Aufgabenstellung aus '{filename}' geladen.\n")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Laden der Datei: {e}")
                
    #Musterlösung Datei-Upload
    def upload_sample_solution(self):
        filename = filedialog.askopenfilename(
            title="Musterlösung Datei auswählen",
            filetypes=[("Python Dateien", "*.py"), ("Alle Dateien", "*.*")]
        )
        if filename:
            self.sample_solution_filename = filename
            self.sample_filename_label.config(text=os.path.basename(filename))
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    self.sample_solution_content = f.read()
                self.log(f"Musterlösung aus '{filename}' geladen.\n")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Laden der Datei: {e}")

    #Download der Repos starten
    def on_download(self):
        self.repo_count = 0
        self.counter_label.config(text=str(self.repo_count))
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state='disabled')
        self.students_text.config(state='normal')
        self.students_text.delete('1.0', tk.END)
        self.students_text.config(state='disabled')
        self.student_names = []
        self.student_combobox['values'] = []

        token = self.token_var.get().strip()
        org_name = self.org_var.get().strip()
        prefix = self.prefix_var.get().strip()

        if not org_name or not prefix:
            messagebox.showwarning("Eingabefehler", "Bitte sowohl ORG_NAME als auch ASSIGNMENT_PREFIX eingeben!")
            return

        self.log(f"Starte Download-Prozess für ORG '{org_name}' mit Prefix '{prefix}'...\n")
        self.download_repos(org_name, prefix, token)

    #Daten Einlesen (zum Debuggen)
    def on_read_files(self):
        assignment_folder = self.prefix_var.get().strip()
        if not assignment_folder:
            messagebox.showwarning("Eingabefehler", "Bitte zuerst einen gültigen ASSIGNMENT_PREFIX eingeben!")
            return
        self.log(f"Starte das Einlesen der Dateien aus dem Ordner '{assignment_folder}'...\n")
        self.read_files(assignment_folder)

    #Analyse (ausgewählter Student)
    def on_analyze_selected(self):
        prefix = self.prefix_var.get().strip()
        selected_student = self.selected_student_var.get().strip()
        test_suite = self.test_suite_var.get().strip()

        if not prefix or not selected_student:
            messagebox.showwarning("Eingabefehler", "Bitte ASSIGNMENT_PREFIX und einen Schüler angeben!")
            return

        submission_folder = os.path.join(prefix, selected_student)
        if not os.path.exists(submission_folder):
            self.log(f"Der Ordner '{submission_folder}' existiert nicht. Bitte überprüfe die Eingaben.\n")
            return

        self.log(f"Starte Analyse für '{submission_folder}'...\n")

        # Prüfen, ob eine Test-Datei hochgeladen wurde
        if test_suite and not os.path.exists(test_suite):
            self.log(f"Die angegebene Test-Suite-Datei '{test_suite}' existiert nicht. Überspringe Tests.\n")
            test_suite = ""

        analyzer = SubmissionAnalyzer(submission_folder, test_suite)
        analysis_text = self.perform_analysis(analyzer, selected_student)
        self.last_analysis_result = analysis_text
        result_file = self.save_analysis_result(prefix, selected_student, analysis_text)
        self.log(f"Analyseergebnisse für '{selected_student}' wurden in '{result_file}' gespeichert.\n")

    #Analyse (alle Schüler in der Liste)
    def on_analyze_all(self):
        prefix = self.prefix_var.get().strip()
        test_suite = self.test_suite_var.get().strip()

        if not prefix:
            messagebox.showwarning("Eingabefehler", "Bitte ASSIGNMENT_PREFIX eingeben!")
            return

        assignment_folder = prefix
        if not os.path.exists(assignment_folder):
            self.log(f"Der Ordner '{assignment_folder}' existiert nicht.\n")
            return

        student_folders = [d for d in os.listdir(assignment_folder) if os.path.isdir(os.path.join(assignment_folder, d))]
        if not student_folders:
            self.log(f"Keine Schülerordner in '{assignment_folder}' gefunden.\n")
            return

        self.log(f"Starte Analyse für alle Schüler in '{assignment_folder}'...\n")
        for student in student_folders:
            submission_folder = os.path.join(prefix, student)
            analyzer = SubmissionAnalyzer(submission_folder, test_suite)
            analysis_text = self.perform_analysis(analyzer, student)
            self.last_analysis_result = analysis_text
            result_file = self.save_analysis_result(prefix, student, analysis_text)
            self.log(f"Analyseergebnisse für '{student}' wurden in '{result_file}' gespeichert.\n")
        self.log("Analyse aller Abgaben abgeschlossen.\n")

    #Analyse durchführen
    def perform_analysis(self, analyzer, student):
        results = []
        results.append(f"=== Analyse für {student} ===\n")
        results.append("=== Unit Tests ===\n")
        if analyzer.test_suite_path:
            test_stdout, test_stderr, test_retcode = analyzer.run_unit_tests()
            results.append(test_stdout)
            if test_stderr:
                results.append("Fehlerausgabe:\n" + test_stderr + "\n")
            results.append(f"Return Code: {test_retcode}\n\n")
        else:
            results.append("Keine Testfälle bereitgestellt.\n\n")
        results.append("=== Statische Analyse (flake8) ===\n")
        analysis_stdout, analysis_stderr, analysis_retcode = analyzer.run_static_analysis()
        results.append(analysis_stdout)
        if analysis_stderr:
            results.append("Fehlerausgabe:\n" + analysis_stderr + "\n")
        results.append(f"Return Code: {analysis_retcode}\n\n")
        results.append("=== Code Formatierung (black) ===\n")
        format_stdout, format_stderr, format_retcode = analyzer.run_code_formatting()
        results.append(format_stdout)
        if format_stderr:
            results.append("Fehlerausgabe:\n" + format_stderr + "\n")
        results.append(f"Return Code: {format_retcode}\n\n")
        return "".join(results)

    #Analyseergebnisse speichern
    def save_analysis_result(self, assignment_folder, student, result_text):
        analysis_dir = os.path.join(assignment_folder, "analysis_results")
        os.makedirs(analysis_dir, exist_ok=True)
        result_file = os.path.join(analysis_dir, f"{student}_analysis.txt")
        with open(result_file, "w", encoding="utf-8") as f:
            f.write(result_text)
        return result_file

    #Dateien auslesen (Debugging)
    def read_files(self, assignment_folder):
        if not os.path.exists(assignment_folder):
            self.log(f"Der Ordner '{assignment_folder}' existiert nicht.\n")
            return
        for student in os.listdir(assignment_folder):
            student_dir = os.path.join(assignment_folder, student)
            if os.path.isdir(student_dir):
                self.log(f"\nStudent: {student}\n")
                for root, dirs, files in os.walk(student_dir):
                    for filename in files:
                        if filename.lower().endswith(".py"):
                            file_path = os.path.join(root, filename)
                            self.log(f"  Datei: {file_path}\n")
                            try:
                                with open(file_path, "r", encoding="utf-8") as f:
                                    content = f.read()
                                self.log(f"    Inhalt (erste 100 Zeichen): {content[:100]}\n")
                            except Exception as e:
                                self.log(f"    Fehler beim Lesen der Datei: {e}\n")

    #Daten einlesen für KI-Feedback und Bewertung
    def read_student_code(self, submission_folder):
        """
        Liest den gesamten Python-Code aus dem Ordner des Schülers ein.
        Da submission_folder den individuellen Schülerordner repräsentiert,
        wird hier nur der Code dieses Schülers zusammengefasst.
        """
        code = ""
        for root, dirs, files in os.walk(submission_folder):
            for filename in files:
                if filename.lower().endswith(".py"):
                    file_path = os.path.join(root, filename)
                    code += f"\n--- Datei: {os.path.relpath(file_path, submission_folder)} ---\n"
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            code += f.read() + "\n"
                    except Exception as e:
                        code += f"Fehler beim Lesen der Datei: {e}\n"
        return code

    #Feedback und Bewertung generieren
    def on_generate_feedback_and_evaluation(self):
        """
        Generiert kombinierten AI-Output (Feedback & Bewertung) entweder für den
        ausgewählten Schüler oder, wenn keiner ausgewählt ist, für alle Schüler im ASSIGNMENT_PREFIX.
        Dafür werden die hochgeladene Aufgabenstellung (und optional Musterlösung), der individuelle Schülercode 
        und die Analyseergebnisse zusammengeführt. Die manuelle Gewichtung fließt in die Bewertung mit ein.
        """
        prefix = self.prefix_var.get().strip()
        test_suite = self.test_suite_var.get().strip()

        if not prefix:
            messagebox.showwarning("Eingabefehler", "Bitte ASSIGNMENT_PREFIX eingeben!")
            return

        #Bestimme, ob ein spezifischer Schüler ausgewählt wurde
        if self.selected_student_var.get():
            students_to_process = [self.selected_student_var.get()]
        else:
            if not os.path.exists(prefix):
                messagebox.showwarning("Fehlende Daten", f"Der Ordner '{prefix}' existiert nicht!")
                return
            students_to_process = [d for d in os.listdir(prefix) if os.path.isdir(os.path.join(prefix, d))]
            if not students_to_process:
                messagebox.showwarning("Keine Schüler", "Es wurden keine Schülerordner gefunden!")
                return

        if not self.assignment_description_content:
            messagebox.showwarning("Eingabefehler", "Bitte eine Aufgabenstellungsdatei hochladen!")
            return

        for student in students_to_process:
            submission_folder = os.path.join(prefix, student)
            if not os.path.exists(submission_folder):
                self.log(f"Der Ordner '{submission_folder}' existiert nicht. Überspringe {student}.\n")
                continue

            self.log(f"Starte kombinierten AI-Feedback- und Bewertungsprozess für {student}...\n")
            #1. Schülercode einlesen (nur der Code dieses Schülers)
            student_code = self.read_student_code(submission_folder)

            #2. Analyse durchführen
            analyzer = SubmissionAnalyzer(submission_folder, test_suite)
            analysis_summary = self.perform_analysis(analyzer, student)
            self.last_analysis_result = analysis_summary

            #3. Gewichtungen einlesen
            weight_func = self.weight_functionality.get()
            weight_code = self.weight_code_quality.get()
            weight_doc = self.weight_documentation.get()

            #Check, dass die Summe der Gewichtungen 100 nicht überschreitet
            total_weight = weight_func + weight_code + weight_doc
            if total_weight > 100:
                messagebox.showwarning("Gewichtungsfehler", "Die Summe der Gewichtungen darf 100% nicht überschreiten!")
                return

            #4. Prompt erstellen – alle relevanten Daten
            prompt = f"""
    Aufgabenstellung:
    {self.assignment_description_content}

    Musterlösung:
    {self.sample_solution_content}

    Schülercode:
    {student_code}

    Analyseergebnisse (Unit-Tests und Formatierung):
    {analysis_summary}

    Die folgenden Kriterien sollen in die Bewertung einfließen:
    - Funktionalität: {weight_func}% (Sollte bei fehlerhaften Tests stark bestraft werden)
    - Codequalität: {weight_code}%
    - Dokumentation/Kommentare: {weight_doc}%

    Bitte generiere:
    1. Ein detailliertes Feedback für die Schüler zum Code, mit Verbesserungsvorschlägen und Hinweisen zur Optimierung.
    - Beziehe dich dabei nicht nur auf die Analyseergebnisse, sondern auch auf die Aufgabenstellung und Musterlösung.
    - Die Analyseergebnisse für die Codeformatierung sollte nicht so wichtig sein wie die Unit-Tests.
    2. Eine abschließende Bewertung der Abgabe im 15-Punkte-System, wobei:
    - Funktionalität, Codequalität und Dokumentation gemäß den oben angegebenen Gewichtungen bewertet werden.
    - Falls die Unit Tests in den Analyseergebnissen fehlschlagen, sollte die Bewertung dementsprechend niedrig ausfallen.
    - Wenn alle Units Tests bestanden sind, sollte die Bewertung höher sein, abhängig von der Qualität des Codes.
    
    Gib das Feedback und die Bewertung in einem klar strukturierten Format aus. Gehe dabei Schritt-Für-Schritt vor.
    Die Tokenanzahl deiner Antwort sollte maximal 800 sein.
    
    ### Antwort:
    """
            #os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
            #torch.cuda.empty_cache()
            
            self.log(f"Prompt für {student} erstellt. Starte Generierung...\n")
            try:
                #Verwende DeepSeek-R1-Distill-Llama-8B
                feedback_eval_generator = pipeline("text-generation",
                                                   model="deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
                                                   device=-1)
            except Exception as e:
                self.log("Fehler beim Laden des AI-Modells: " + str(e) + "\nBitte installieren Sie ein Deep Learning-Backend (z.B. pip install torch).\n")
                return

            #Nutze max_new_tokens, um sicherzustellen, dass nicht nur der Prompt zurückgegeben wird
            ai_output = feedback_eval_generator(prompt, max_new_tokens=800, do_sample=True)
            combined_output = ai_output[0]['generated_text'][len(prompt):]
            self.last_ai_feedback = combined_output

            self.log("=== AI Feedback und Bewertung für " + student + " ===\n" + combined_output + "\n")

            #Speicherung in einem schülerbezogenen Ordner
            combined_dir = os.path.join(prefix, "combined_results")
            os.makedirs(combined_dir, exist_ok=True)
            combined_file = os.path.join(combined_dir, f"{student}_combined.txt")
            with open(combined_file, "w", encoding="utf-8") as f:
                f.write(combined_output)
            self.log(f"Feedback und Bewertung für '{student}' wurden in '{combined_file}' gespeichert.\n")

    #Logging Funktion (Debugging)
    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.update_idletasks()

    #Zähler für gedownloadete Repos
    def update_counter(self):
        self.repo_count += 1
        self.counter_label.config(text=str(self.repo_count))

    #Repos herunterladen
    def download_repos(self, org_name, assignment_prefix, token):
        if not token:
            load_dotenv()
            token = os.getenv("GITHUB_TOKEN")
            if not token:
                self.log("Achtung: Kein Token angegeben und keine Umgebungsvariable GITHUB_TOKEN gefunden.\n"
                         "Öffentliche Repos können gelesen werden, private jedoch nicht.\n")
        try:
            g = Github(token) if token else Github()
            org = g.get_organization(org_name)
        except Exception as e:
            self.log(f"Fehler beim Zugriff auf die Organisation '{org_name}': {e}\n")
            return

        repo_count = 0
        for repo in org.get_repos():
            if repo.name.startswith(assignment_prefix):
                repo_count += 1
                self.log(f"Repo gefunden: {repo.name}\n")
                student_name = repo.name[len(assignment_prefix) + 1:]
                self.students_text.config(state='normal')
                self.students_text.insert(tk.END, student_name + "\n")
                self.students_text.config(state='disabled')
                if student_name not in self.student_names:
                    self.student_names.append(student_name)
                    self.student_combobox['values'] = self.student_names
                if not os.path.exists(assignment_prefix):
                    os.makedirs(assignment_prefix)
                repo_dir = os.path.join(assignment_prefix, student_name)
                clone_url = repo.clone_url
                if token and repo.private:
                    clone_url = f"https://{token}@github.com/{org_name}/{repo.name}.git"
                if not os.path.exists(repo_dir):
                    self.log(f"→ Klone Repository {repo.name}...\n")
                    result = subprocess.run(["git", "clone", clone_url, repo_dir],
                                            capture_output=True, text=True)
                    if result.returncode == 0:
                        self.log("→ Erfolgreich geklont.\n")
                    else:
                        self.log(f"→ Fehler beim Klonen: {result.stderr}\n")
                else:
                    self.log(f"→ Pull für {repo.name} (Repo existiert bereits)...\n")
                    result = subprocess.run(["git", "-C", repo_dir, "pull"],
                                            capture_output=True, text=True)
                    if result.returncode == 0:
                        self.log("→ Aktualisiert.\n")
                    else:
                        self.log(f"→ Fehler beim Pull: {result.stderr}\n")
                self.update_counter()
        if repo_count == 0:
            self.log(f"Keine Repos gefunden, die mit '{assignment_prefix}' beginnen.\n")

    def on_exit(self):
        self.destroy()

def main():
    app = Teaching_Assistant()
    app.mainloop()

if __name__ == "__main__":
    main()
