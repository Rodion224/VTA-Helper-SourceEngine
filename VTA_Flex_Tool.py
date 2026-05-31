from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import sys
import shutil
import os

def validate_vta(lines):
    has_vertexanimation = any("vertexanimation" in l for l in lines)
    has_time0 = any(l.strip().startswith("time 0") for l in lines)

    if not has_vertexanimation:
        return "Invalid VTA file: missing 'vertexanimation' block"

    if not has_time0:
        return "Invalid VTA file: missing base frame (time 0)"

    found_vertex = False
    in_va = False

    for line in lines:
        s = line.strip()

        if s == "vertexanimation":
            in_va = True
            continue

        if not in_va:
            continue

        if len(s.split()) >= 7:
            found_vertex = True
            break

    if not found_vertex:
        return "Invalid VTA file: no valid vertex data found"

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
                    f"    {vid} "
                    f"{nx:.6f} "
                    f"{ny:.6f} "
                    f"{nz:.6f} "
                    f"{p[4]} {p[5]} {p[6]}\n"
                )

            except:
                out.append(line)

        else:
            out.append(line)

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(out)

class VTAWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("VTA Flex Tool")
        self.resize(350, 280)

        self.setFont(QFont("Segoe UI", 10))

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel("VTA Flex Tool")
        title.setObjectName("Title")
        layout.addWidget(title)

        label1 = QLabel("VTA File")
        layout.addWidget(label1)

        row = QHBoxLayout()

        self.entry = QLineEdit()
        self.entry.setPlaceholderText("Select VTA file...")

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse)

        row.addWidget(self.entry)
        row.addWidget(browse_btn)

        layout.addLayout(row)

        label2 = QLabel("Multiplier")
        layout.addWidget(label2)

        self.mult = QLineEdit()
        self.mult.setText("6.5")
        layout.addWidget(self.mult)

        layout.addStretch()

        self.make_btn = QPushButton("Make Flex")
        self.make_btn.setFixedHeight(42)
        self.make_btn.clicked.connect(self.run)

        layout.addWidget(self.make_btn)

    def browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select VTA",
            "",
            "VTA Files (*.vta)"
        )

        if path:
            self.entry.setText(path)

    def run(self):
        path = self.entry.text().strip()

        if not os.path.isfile(path):
            QMessageBox.critical(self, "Error", "File not found")
            return

        try:
            factor = float(self.mult.text())
        except:
            QMessageBox.critical(self, "Error", "Invalid multiplier")
            return

        result = process_vta(path, factor)

        if result:
            QMessageBox.critical(self, "Error", "File is corrupted or empty")
            return

        QMessageBox.information(self, "Done", "Flexes processed successfully")

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

QMessageBox QPushButton {
    min-width: 80px;
}
""")

window = VTAWindow()
window.show()

sys.exit(app.exec())