import os
import re
import sys
import subprocess

from PyQt5 import QtCore, QtGui, QtWidgets, uic

from src.test_vector_gen import generate_test_vector

qtcreator_file  = "src/mainwindow.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtcreator_file)

class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.truth_table_generated = False

        self.circ_path_input.setText("")
        self.test_file_input.setText("")
        self.console_logs_tb.setText("")

        self.truth_table_model = QtGui.QStandardItemModel(self)
        self.truth_table_tab.setModel(self.truth_table_model)

        self.run_tests_btn.clicked.connect(self.run_tests)
        self.circ_select_btn.clicked.connect(self.select_circ_file)
        self.test_select_btn.clicked.connect(self.select_test_config_file)
        self.clear_tester_btn.clicked.connect(self.clear_test_config)
        self.clear_logs_btn.clicked.connect(self.clear_logs)
        self.save_tt_btn.clicked.connect(self.save_truth_table)

        self.statusbar.showMessage("TestBench is ready.")

    def run_tests(self):
        self.statusbar.showMessage("Running tests...")

        if self.circ_path_input.text() == "":
            error_dialog = QtWidgets.QErrorMessage()
            error_dialog.showMessage('Please select a circuit file!')
            error_dialog.exec_()

            self.statusbar.showMessage("TestBench is ready.")

            return

        if self.test_file_input.text() == "":
            error_dialog = QtWidgets.QErrorMessage()
            error_dialog.showMessage('Please select a test config file!')
            error_dialog.exec_()
            
            self.statusbar.showMessage("TestBench is ready.")

            return

        p = subprocess.Popen(
            f"java -jar src/logisim-ceng.jar -nosplash -grader _tt.txt.properties {self.circ_path_input.text()}",
            shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.clear_logs()

        process_stdout = p.stdout.read().decode()
        process_stderr = p.stderr.read().decode()

        if process_stderr != "":
            self.console_logs_tb.setText("=" * 10 + " ERROR LOG " + "=" * 10 + "\n\n Error:" + process_stderr)
            error_dialog = QtWidgets.QErrorMessage()
            error_dialog.setWindowTitle("Unexpected tester error")
            error_dialog.showMessage(process_stderr)

            error_dialog.exec_()

            return

        self.console_logs_tb.setText(process_stdout)

        tester_fails = len(re.findall("\[\!\!\] TEST RUN ERROR\\n", process_stdout))

        with open("_tt.txt.properties", "r") as fp:
            try:
                tester_total = int(re.findall(r"number_of_runs=(\d+)", fp.read())[0])
            except Exception as e:
                error_dialog = QtWidgets.QErrorMessage()
                error_dialog.showMessage('Exception: ' + str(e))
                error_dialog.exec_()

                return
      
        info_dialog = QtWidgets.QMessageBox()
        info_dialog.setIcon(QtWidgets.QMessageBox.Information)
        info_dialog.setText(f"Passed: {tester_total - tester_fails}\nFailed: {tester_fails}")
        info_dialog.setInformativeText("Detailed output can be found in console output section.")
        info_dialog.setWindowTitle("Tester output")
        info_dialog.setStandardButtons(QtWidgets.QMessageBox.Ok)
        info_dialog.exec_()

        self.statusbar.showMessage("TestBench is ready.")

    def select_circ_file(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select circuit file",
            "","Logisim Circuit Files (*.circ);;All Files (*)", options=options)

        if fileName:
            self.circ_path_input.setText(fileName)
            self.statusbar.showMessage("Selected circuit file.")

    def select_test_config_file(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select test configuration file",
            "","JSON Files (*.json);;All Files (*)", options=options)

        if fileName:
            self.test_file_input.setText(fileName)
            self.statusbar.showMessage("Selected test configuration file.")
            self.generate_truth_table(fileName)

    def generate_truth_table(self, fileName):
        self.statusbar.showMessage("Generating truth table...")

        generate_test_vector(fileName, output_file="_tt.txt")

        try:
            with open("_tt.txt", "r") as fp:
                self.truth_table_model.setRowCount(0)

                for line in fp.readlines():
                    row = [QtGui.QStandardItem(x) for x in line.replace("\n", "").split(" ")]
                    self.truth_table_model.appendRow(row)
        except Exception as e:
            error_dialog = QtWidgets.QErrorMessage()
            error_dialog.showMessage('Error reading test vector: ' + str(e))
            error_dialog.exec_()

            return
            
        self.truth_table_tab.resizeColumnsToContents()
        self.statusbar.showMessage("Truth table is OK.")

        self.truth_table_generated = True

    def clear_test_config(self):
        self.test_file_input.setText("")
        self.truth_table_model.setRowCount(0)

        self.statusbar.showMessage("Cleared test configurations.")

    def clear_logs(self):
        self.console_logs_tb.setText("")

        self.statusbar.showMessage("Cleared logisim console logs.")
        
    def save_truth_table(self):
        if not self.truth_table_generated:
            error_dialog = QtWidgets.QErrorMessage()
            error_dialog.showMessage('Please select a test config file!')
            error_dialog.exec_()
            
            self.statusbar.showMessage("TestBench is ready.")

            return

        with open('_tt.txt') as fp:
            name = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File')
            file = open(name[0], 'w')
            file.write(fp.read())
            file.close()

        self.statusbar.showMessage("TestBench is ready.")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()
    window.setWindowTitle("Sazak's Logisim Circuit TestBench")

    sys.exit(app.exec_())