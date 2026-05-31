from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont
import sys
import os
import shutil

def validate_vta(lines):
    if not lines:
        return "EMPTY FILE"

    if not any("vertexanimation" in l for l in lines):
        return "MISSING VERTEXANIMATION"

    if not any(l.strip().startswith("time 0") for l in lines):
        return "MISSING TIME 0"

    in_va = False
    has_data = False

    for l in lines:
        s = l.strip()

        if "vertexanimation" in s:
            in_va = True
            continue

        if not in_va:
            continue

        if len(s.split()) >= 7:
            has_data = True
            break

    if not has_data:
        return "NO VALID VERTEX DATA"

    return None

def process_vta(filepath, factor):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    error = validate_vta(lines)
    if error:
        return error

    backup = filepath + ".bak"
    if not os.path.exists(backup):
        shutil.copy2(filepath, backup)

    basis = {}
    current_time = None
    in_va = False

    for line in lines:
        s = line.strip()

        if s == "vertexanimation":
            in_va = True
            continue

        if not in_va:
            continue

        if s.startswith("time "):
            try:
                current_time = int(s.split()[1])
            except:
                current_time = None
            continue

        if current_time != 0:
            continue

        p = s.split()

        if len(p) >= 7:
            try:
                basis[int(p[0])] = (
                    float(p[1]),
                    float(p[2]),
                    float(p[3])
                )
            except:
                pass

    out = []
    current_time = None
    in_va = False

    for line in lines:
        s = line.strip()

        if s == "vertexanimation":
            in_va = True
            out.append(line)
            continue

        if not in_va:
            out.append(line)
            continue

        if s.startswith("time "):
            try:
                current_time = int(s.split()[1])
            except:
                current_time = None

            out.append(line)
            continue

        if current_time in (None, 0):
            out.append(line)
            continue

        p = s.split()

        if len(p) >= 7:
            try:
                vid = int(p[0])

                if vid not in basis:
                    out.append(line)
                    continue

                bx, by, bz = basis[vid]

                x = float(p[1])
                y = float(p[2])
                z = float(p[3])

                nx = bx + (x - bx) * factor
                ny = by + (y - by) * factor
                nz = bz + (z - bz) * factor

                out.append(
                    f"    {vid} {nx:.6f} {ny:.6f} {nz:.6f} {p[4]} {p[5]} {p[6]}\n"
                )

            except:
                out.append(line)

        else:
            out.append(line)

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(out)


class BatchWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("VTA Batch Flex Tool")
        self.resize(350, 280)

        self.setFont(QFont("Segoe UI", 10))

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel("VTA Batch Flex Tool")
        title.setObjectName("Title")
        layout.addWidget(title)

        folder_label = QLabel("Models Folder")
        layout.addWidget(folder_label)

        row = QHBoxLayout()

        self.entry = QLineEdit()
        self.entry.setPlaceholderText("Select models folder...")

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse)

        row.addWidget(self.entry)
        row.addWidget(browse_btn)

        layout.addLayout(row)

        mult_label = QLabel("Multiplier")
        layout.addWidget(mult_label)

        self.mult = QLineEdit()
        self.mult.setText("6.5")
        layout.addWidget(self.mult)

        layout.addStretch()

        self.run_btn = QPushButton("MAKE ALL FLEXES")
        self.run_btn.setFixedHeight(45)
        self.run_btn.clicked.connect(self.run)

        layout.addWidget(self.run_btn)

    def browse(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Models Folder"
        )

        if path:
            self.entry.setText(path)

    def run(self):
        root_folder = self.entry.text().strip()

        if not os.path.isdir(root_folder):
            QMessageBox.critical(self, "Error", "Folder not found")
            return

        try:
            factor = float(self.mult.text())
        except:
            QMessageBox.critical(self, "Error", "Invalid multiplier")
            return

        total = 0
        ok = 0
        failed = 0

        errors = []

        for root_dir, dirs, files in os.walk(root_folder):
            for file in files:
                if file.lower().endswith(".vta"):
                    total += 1

                    path = os.path.join(root_dir, file)
                    result = process_vta(path, factor)

                    if result:
                        failed += 1
                        errors.append(f"{file}: {result}")
                    else:
                        ok += 1

        if failed == 0:
            QMessageBox.information(
                self,
                "Done",
                f"Processed {ok}/{total} VTA files successfully"
            )
        else:
            QMessageBox.warning(
                self,
                "Finished with errors",
                f"OK: {ok}\nFailed: {failed}\nTotal: {total}\n\nFirst errors:\n" +
                "\n".join(errors[:5])
            )

app = QApplication(sys.argv)

app.setStyleSheet("""
QWidget {
    background-color: #202020;
    color: white;
    font-family: "Segoe UI";
}

QLabel {
    font-size: 13px;
}

#Title {
    font-size: 24px;
    font-weight: 600;
    padding-bottom: 10px;
}

QLineEdit {
    background: #2B2B2B;
    border: 1px solid #3A3A3A;
    border-radius: 10px;
    padding: 10px;
    font-size: 13px;
}

QLineEdit:focus {
    border: 2px solid #4CC2FF;
}

QPushButton {
    background-color: #0078D4;
    border: none;
    border-radius: 10px;
    color: white;
    padding: 10px 18px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #1A86D9;
}

QPushButton:pressed {
    background-color: #0063B1;
}

QMessageBox {
    background-color: #202020;
}
""")

window = BatchWindow()
window.show()

sys.exit(app.exec())